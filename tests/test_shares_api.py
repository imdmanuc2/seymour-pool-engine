from pathlib import Path

from fastapi.testclient import TestClient

from seymour_pool_engine.config import get_settings
from seymour_pool_engine.main import create_app


def test_shares_endpoint_uses_share_service(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SEYMOUR_IDENTITY_FILE", str(tmp_path / "installation-id"))
    get_settings.cache_clear()
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.shares.get_shares",
        lambda **kwargs: {
            "count": 1,
            "poolId": kwargs["pool_id"],
            "limit": kwargs["limit"],
            "shares": [{"shareId": "abc", "poolId": "btc-solo"}],
        },
    )

    client = TestClient(create_app())
    response = client.get("/api/v1/shares?poolId=btc-solo&limit=25")

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["poolId"] == "btc-solo"


def test_shares_sync_endpoint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SEYMOUR_IDENTITY_FILE", str(tmp_path / "installation-id"))
    get_settings.cache_clear()
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.shares.synchronize_shares",
        lambda **kwargs: {
            "provider": "miningcore",
            "poolId": kwargs["pool_id"],
            "observed": 3,
            "inserted": 2,
            "duplicates": 1,
        },
    )

    client = TestClient(create_app())
    response = client.post("/api/v1/shares/sync?poolId=btc-solo&limit=500")

    assert response.status_code == 200
    assert response.json()["inserted"] == 2
    assert response.json()["duplicates"] == 1
