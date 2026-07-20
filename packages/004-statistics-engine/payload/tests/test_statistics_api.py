from pathlib import Path

from fastapi.testclient import TestClient

from seymour_pool_engine.config import get_settings
from seymour_pool_engine.main import create_app


def test_statistics_routes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("SEYMOUR_IDENTITY_FILE", str(tmp_path / "installation-id"))
    get_settings.cache_clear()
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.statistics.get_statistics_overview",
        lambda **kwargs: {"window": kwargs["window"], "hashrate": 123.0},
    )
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.statistics.get_pool_statistics",
        lambda **kwargs: {"window": kwargs["window"], "pools": []},
    )
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.statistics.get_worker_statistics",
        lambda **kwargs: {"window": kwargs["window"], "workers": []},
    )
    client = TestClient(create_app())
    assert client.get("/api/v1/statistics/overview?window=1m").status_code == 200
    assert client.get("/api/v1/statistics/pools").status_code == 200
    assert client.get("/api/v1/statistics/workers").status_code == 200
