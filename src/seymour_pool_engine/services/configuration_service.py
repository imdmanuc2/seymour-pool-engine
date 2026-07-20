import hashlib
import json
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from seymour_pool_engine.repositories.configuration_repository import ConfigurationRepository

SUPPORTED_DOMAINS = {
    "engine",
    "pool",
    "coin",
    "rpc",
    "stratum",
    "wallet-reference",
    "reward-policy",
    "developer-fee",
    "logging",
    "monitoring",
    "api",
    "security",
}


class ConfigurationService:
    def __init__(self, repository: ConfigurationRepository | None = None) -> None:
        self.repository = repository or ConfigurationRepository()

    def validate(
        self, *, profile_key: str, domain: str, configuration: dict[str, Any]
    ) -> dict[str, Any]:
        errors: list[str] = []
        warnings: list[str] = []
        normalized_domain = domain.strip().lower()
        if not profile_key.strip():
            errors.append("profileKey is required")
        if normalized_domain not in SUPPORTED_DOMAINS:
            errors.append("Unsupported configuration domain")
        if not isinstance(configuration, dict) or not configuration:
            errors.append("configuration must be a non-empty object")
        self._domain_validation(normalized_domain, configuration, errors, warnings)
        checksum = self._checksum(configuration)
        result = {
            "profileKey": profile_key,
            "domain": normalized_domain,
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "checksum": checksum,
        }
        self.repository.record_validation(
            profile_key=profile_key,
            domain=normalized_domain,
            valid=not errors,
            errors=errors,
            warnings=warnings,
            checksum=checksum,
        )
        return result

    def put(
        self,
        *,
        profile_key: str,
        domain: str,
        configuration: dict[str, Any],
        change_summary: str,
        changed_by: str,
    ) -> dict[str, Any]:
        validation = self.validate(
            profile_key=profile_key, domain=domain, configuration=configuration
        )
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))
        row = self.repository.upsert_profile_revision(
            profile_key=profile_key.strip(),
            domain=domain.strip().lower(),
            configuration=deepcopy(configuration),
            checksum=validation["checksum"],
            change_summary=change_summary.strip() or "Configuration updated",
            changed_by=changed_by.strip() or "system",
        )
        return self._serialize_revision(row)

    def get(self, *, profile_key: str | None = None) -> Any:
        if profile_key:
            row = self.repository.get_active(profile_key=profile_key)
            if row is None:
                raise ValueError("Configuration profile was not found")
            return self._serialize_revision(row)
        return [self._serialize_revision(row) for row in self.repository.list_active()]

    def history(self, *, profile_key: str) -> list[dict[str, Any]]:
        return [
            self._serialize_revision(row)
            for row in self.repository.history(profile_key=profile_key)
        ]

    def rollback(
        self, *, profile_key: str, revision_number: int, changed_by: str
    ) -> dict[str, Any]:
        row = self.repository.rollback(
            profile_key=profile_key,
            revision_number=revision_number,
            changed_by=changed_by,
        )
        if row is None:
            raise ValueError("Requested configuration revision was not found")
        return self._serialize_revision(row)

    def export(self, *, actor: str) -> dict[str, Any]:
        profiles = self.get()
        payload = {
            "format": "seymour-configuration-backup",
            "version": 1,
            "createdAt": datetime.now(UTC).isoformat(),
            "profiles": profiles,
        }
        checksum = self._checksum(payload)
        export_id = self.repository.record_export(
            checksum=checksum, profile_count=len(profiles), actor=actor
        )
        return {"exportId": str(export_id), "checksum": checksum, "payload": payload}

    def import_backup(
        self, *, payload: dict[str, Any], checksum: str, actor: str
    ) -> dict[str, Any]:
        calculated = self._checksum(payload)
        profiles = payload.get("profiles", []) if isinstance(payload, dict) else []
        if calculated != checksum:
            self.repository.record_import(
                checksum=checksum,
                profile_count=0,
                actor=actor,
                status="rejected",
                error_message="Checksum mismatch",
            )
            raise ValueError("Configuration backup checksum mismatch")
        if payload.get("format") != "seymour-configuration-backup" or payload.get("version") != 1:
            raise ValueError("Unsupported configuration backup format")
        imported = 0
        for profile in profiles:
            self.put(
                profile_key=profile["profileKey"],
                domain=profile["domain"],
                configuration=profile["configuration"],
                change_summary="Imported from configuration backup",
                changed_by=actor,
            )
            imported += 1
        import_id = self.repository.record_import(
            checksum=checksum,
            profile_count=imported,
            actor=actor,
            status="completed",
        )
        return {"importId": str(import_id), "importedProfiles": imported, "checksum": checksum}

    @staticmethod
    def _domain_validation(
        domain: str,
        configuration: dict[str, Any],
        errors: list[str],
        warnings: list[str],
    ) -> None:
        if domain == "rpc":
            if not configuration.get("url"):
                errors.append("RPC configuration requires url")
            if not configuration.get("username"):
                warnings.append("RPC username is not present")
        if domain == "stratum":
            port = configuration.get("port")
            if not isinstance(port, int) or not 1 <= port <= 65535:
                errors.append("Stratum configuration requires a valid port")
        if domain == "pool" and not configuration.get("poolId"):
            errors.append("Pool configuration requires poolId")
        if domain == "coin" and not configuration.get("symbol"):
            errors.append("Coin configuration requires symbol")
        if domain == "reward-policy" and configuration.get("policy") not in {
            "solo",
            "prop",
            "pplns",
        }:
            errors.append("Reward policy must be solo, prop, or pplns")
        if domain == "developer-fee":
            fee = configuration.get("percent")
            if fee is None or float(fee) < 0.75:
                errors.append("Developer fee cannot be lower than 0.75 percent")
            if configuration.get("enabled") is False:
                errors.append("Developer fee cannot be disabled")

    @staticmethod
    def _checksum(value: Any) -> str:
        canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    @staticmethod
    def _serialize_revision(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "profileKey": row["profile_key"],
            "domain": row["domain"],
            "revisionNumber": row["revision_number"],
            "configuration": row["configuration"],
            "checksum": row["checksum"],
            "status": row["status"],
            "changeSummary": row["change_summary"],
            "changedBy": row["changed_by"],
            "createdAt": row["created_at"].isoformat() if row.get("created_at") else None,
        }
