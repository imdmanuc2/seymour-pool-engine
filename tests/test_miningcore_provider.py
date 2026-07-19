from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from seymour_pool_engine.config import get_settings
from seymour_pool_engine.main import create_app
from seymour_pool_engine.providers.miningcore.provider import MiningCoreProvider


def test_miningcore_status_is_safe_when_database_disabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SEYMOUR_IDENTITY_FILE", str(tmp_path / "installation-id"))
    monkeypatch.delenv("SEYMOUR_MININGCORE_DATABASE_URL", raising=False)
    get_settings.cache_clear()

    provider = MiningCoreProvider()
    monkeypatch.setattr(
        provider.rest,
        "health",
        lambda: {
            "status": "online",
            "summary": "MiningCore REST API is responding",
            "details": {},
        },
    )

    status = provider.get_status()

    assert status.provider == "miningcore"
    assert status.status == "online"
    assert status.schema_compatible is False
    assert any(check.status == "disabled" for check in status.checks)


def test_miningcore_status_endpoint_returns_normalized_contract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SEYMOUR_IDENTITY_FILE", str(tmp_path / "installation-id"))
    get_settings.cache_clear()

    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.miningcore.get_miningcore_status",
        lambda: {
            "provider": "miningcore",
            "status": "online",
            "observedAt": datetime.now(UTC).isoformat(),
            "version": None,
            "schemaCompatible": True,
            "capabilities": ["poolstats", "minerstats"],
            "checks": [],
        },
    )

    client = TestClient(create_app())
    response = client.get("/api/v1/miningcore/status")

    assert response.status_code == 200
    assert response.json()["provider"] == "miningcore"
    assert response.json()["schemaCompatible"] is True
