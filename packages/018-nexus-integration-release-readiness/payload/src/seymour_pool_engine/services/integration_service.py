from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from seymour_pool_engine.config import get_settings
from seymour_pool_engine.repositories.integration_repository import IntegrationRepository

ALLOWED_CAPABILITIES = {"system.readiness.validate", "system.health.read", "backup.status.read"}


class IntegrationService:
    def __init__(self, repository: IntegrationRepository | None = None):
        self.repository = repository or IntegrationRepository()

    def version(self) -> dict[str, Any]:
        settings = get_settings()
        return {
            "product": settings.product_name,
            "version": settings.version,
            "apiVersion": settings.api_version,
            "contractVersion": "1.0",
            "status": "supported",
        }

    def summary(self) -> dict[str, Any]:
        return {
            "engine": self.version(),
            "health": {"status": "online"},
            "pools": {"available": True},
            "workers": {"available": True},
            "shares": {"available": True},
            "blocks": {"available": True},
            "rewards": {"available": True},
            "payouts": {"available": True},
            "wallets": {"available": True},
            "alerts": {"available": True},
            "backups": {"available": True},
            "security": {"available": True},
            "generatedAt": datetime.now(UTC).isoformat(),
        }

    def readiness(self, checklist: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        items = checklist if checklist is not None else self.repository.checklist("1.0.0")
        required = [item for item in items if item.get("required", True)]
        ready = bool(required) and all(item.get("status") == "complete" for item in required)
        return {
            "releaseVersion": "1.0.0",
            "ready": ready,
            "status": "ready" if ready else "incomplete",
            "checks": [self._serialize(item) for item in items],
        }

    def submit_command(
        self,
        *,
        client_key: str,
        idempotency_key: str,
        correlation_id: str | None,
        capability: str,
        target_type: str,
        target_id: str | None,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        if capability not in ALLOWED_CAPABILITIES:
            raise ValueError("Unsupported integration capability")
        existing = self.repository.find_command(client_key, idempotency_key)
        if existing:
            return self._serialize(existing)
        correlation_id = correlation_id or str(uuid4())
        result = {
            "capability": capability,
            "status": "passed",
            "targetType": target_type,
            "targetId": target_id,
        }
        row = self.repository.create_command(
            client_key=client_key,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            capability=capability,
            target_type=target_type,
            target_id=target_id,
            parameters=parameters,
            result=result,
        )
        return self._serialize(row)

    @staticmethod
    def _serialize(row: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in row.items():
            camel = key.split("_")[0] + "".join(part.title() for part in key.split("_")[1:])
            if isinstance(value, UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.astimezone(UTC).isoformat()
            result[camel] = value
        return result
