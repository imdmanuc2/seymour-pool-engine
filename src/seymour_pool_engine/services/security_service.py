import hashlib
import hmac
import secrets
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from seymour_pool_engine.repositories.security_repository import SecurityRepository


class SecurityService:
    def __init__(self, repository: SecurityRepository | None = None):
        self.repository = repository or SecurityRepository()

    def principals(self) -> list[dict[str, Any]]:
        return [self._serialize(row, redact=True) for row in self.repository.list_principals()]

    def roles(self) -> list[dict[str, Any]]:
        return [self._serialize(row) for row in self.repository.list_roles()]

    def create_principal(self, **values: Any) -> dict[str, Any]:
        principal_type = values["principal_type"].lower()
        if principal_type not in {"user", "service"}:
            raise ValueError("Principal type must be user or service")
        name = values["principal_name"].strip().lower()
        if not name:
            raise ValueError("Principal name is required")
        password = values.pop("password", None)
        if principal_type == "user" and password is not None and len(password) < 12:
            raise ValueError("User passwords must contain at least 12 characters")
        password_hash = self.hash_password(password) if password else None
        values = dict(values)
        values["principal_type"] = principal_type
        values["principal_name"] = name
        values["password_hash"] = password_hash
        row = self.repository.create_principal(**values)
        return self._serialize(row, redact=True)

    def grant_role(
        self, principal_id: UUID, role_name: str, granted_by: str = "api"
    ) -> dict[str, Any]:
        row = self.repository.grant_role(principal_id, role_name.lower(), granted_by)
        return self._serialize(row)

    def permissions(self, principal_id: UUID) -> dict[str, Any]:
        principal = self.repository.get_principal(principal_id)
        if not principal:
            raise ValueError("Principal does not exist")
        return {
            "principalId": str(principal_id),
            "permissions": self.repository.permissions_for_principal(principal_id),
        }

    def issue_api_key(
        self,
        *,
        principal_id: UUID,
        key_name: str,
        created_by: str = "api",
        expires_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.repository.get_principal(principal_id):
            raise ValueError("Principal does not exist")
        raw = "spe_" + secrets.token_urlsafe(36)
        digest = self.hash_token(raw)
        row = self.repository.create_api_key(
            principal_id=principal_id,
            key_name=key_name.strip(),
            key_prefix=raw[:12],
            key_hash=digest,
            expires_at=expires_at,
            created_by=created_by,
            metadata=metadata or {},
        )
        result = self._serialize(row, redact=True)
        result["apiKey"] = raw
        return result

    def authenticate_api_key(self, raw_key: str) -> dict[str, Any]:
        if not raw_key or not raw_key.startswith("spe_"):
            raise ValueError("Invalid API key")
        row = self.repository.find_active_api_key(self.hash_token(raw_key))
        if not row:
            raise ValueError("Invalid or expired API key")
        self.repository.touch_api_key(row["api_key_id"])
        permissions = self.repository.permissions_for_principal(row["principal_id"])
        return {
            "principalId": str(row["principal_id"]),
            "principalType": row["principal_type"],
            "principalName": row["principal_name"],
            "permissions": permissions,
        }

    def authorize(self, raw_key: str, permission: str) -> dict[str, Any]:
        identity = self.authenticate_api_key(raw_key)
        if permission not in identity["permissions"]:
            raise PermissionError(f"Permission denied: {permission}")
        return identity

    def revoke_api_key(self, api_key_id: UUID) -> dict[str, Any]:
        row = self.repository.revoke_api_key(api_key_id)
        if not row:
            raise ValueError("API key does not exist")
        return self._serialize(row, redact=True)

    def events(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        return [self._serialize(row) for row in self.repository.list_events(limit)]

    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_bytes(16)
        rounds = 310_000
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, rounds)
        return f"pbkdf2_sha256${rounds}${salt.hex()}${digest.hex()}"

    @staticmethod
    def verify_password(password: str, encoded: str) -> bool:
        algorithm, rounds, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), int(rounds)
        )
        return hmac.compare_digest(actual.hex(), expected)

    @staticmethod
    def hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()

    @staticmethod
    def _serialize(row: dict[str, Any], redact: bool = False) -> dict[str, Any]:
        result = {}
        for key, value in row.items():
            if redact and key in {"password_hash", "key_hash", "token_hash"}:
                continue
            camel = key.split("_")[0] + "".join(part.title() for part in key.split("_")[1:])
            if isinstance(value, UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.astimezone(UTC).isoformat()
            result[camel] = value
        return result
