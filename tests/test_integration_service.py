import pytest

from seymour_pool_engine.services.integration_service import IntegrationService


class Repo:
    def checklist(self, release_version):
        return [{"item_key": "a", "status": "complete", "required": True}]

    def find_command(self, client_key, idempotency_key):
        return None

    def create_command(self, **values):
        return {"command_id": "1", **values, "status": "completed"}


def test_version_contract():
    assert IntegrationService(Repo()).version()["contractVersion"] == "1.0"


def test_readiness_complete():
    assert IntegrationService(Repo()).readiness()["ready"] is True


def test_command_rejects_unknown():
    with pytest.raises(ValueError, match="Unsupported"):
        IntegrationService(Repo()).submit_command(
            client_key="nexus",
            idempotency_key="x",
            correlation_id=None,
            capability="bad",
            target_type="engine",
            target_id=None,
            parameters={},
        )


def test_summary_sections():
    data = IntegrationService(Repo()).summary()
    assert {"engine", "health", "pools", "workers", "wallets", "backups"} <= set(data)
