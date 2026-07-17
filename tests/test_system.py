from pathlib import Path

from fastapi.testclient import TestClient

from seymour_pool_engine.config import get_settings
from seymour_pool_engine.main import create_app


def test_root_endpoint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(
        "SEYMOUR_IDENTITY_FILE",
        str(tmp_path / "installation-id"),
    )
    get_settings.cache_clear()

    client = TestClient(create_app())
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["product"] == "Seymour Pool Engine"
    assert response.json()["apiVersion"] == "v1"


def test_system_endpoint_has_persistent_identity(
    tmp_path: Path,
    monkeypatch,
) -> None:
    identity_file = tmp_path / "installation-id"

    monkeypatch.setenv("SEYMOUR_IDENTITY_FILE", str(identity_file))
    get_settings.cache_clear()

    client = TestClient(create_app())

    first = client.get("/api/v1/system")
    second = client.get("/api/v1/system")

    assert first.status_code == 200
    assert second.status_code == 200

    first_id = first.json()["installationId"]
    second_id = second.json()["installationId"]

    assert first_id == second_id
    assert identity_file.exists()
