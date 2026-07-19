from pathlib import Path

from fastapi.testclient import TestClient

from seymour_pool_engine.config import get_settings
from seymour_pool_engine.main import create_app


def test_workers_endpoint_uses_worker_service(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SEYMOUR_IDENTITY_FILE", str(tmp_path / "installation-id"))
    get_settings.cache_clear()
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.workers.get_workers",
        lambda **kwargs: {
            "count": 1,
            "poolId": kwargs["pool_id"],
            "state": kwargs["lifecycle_state"],
            "provider": kwargs["provider_name"],
            "workers": [{"workerId": "abc", "state": "active"}],
        },
    )

    client = TestClient(create_app())
    response = client.get("/api/v1/workers?poolId=btc-solo&state=active")

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["poolId"] == "btc-solo"


def test_workers_sync_endpoint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SEYMOUR_IDENTITY_FILE", str(tmp_path / "installation-id"))
    get_settings.cache_clear()
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.workers.synchronize_workers",
        lambda pool_id: {
            "provider": "miningcore",
            "poolId": pool_id,
            "observed": 2,
            "created": 2,
            "updated": 0,
            "markedOffline": 0,
        },
    )

    client = TestClient(create_app())
    response = client.post("/api/v1/workers/sync?poolId=btc-solo")

    assert response.status_code == 200
    assert response.json()["observed"] == 2
