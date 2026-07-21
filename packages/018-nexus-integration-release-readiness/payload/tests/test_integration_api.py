from fastapi.testclient import TestClient

from seymour_pool_engine.main import app

client = TestClient(app)


def test_integration_routes_registered():
    paths = set(app.openapi()["paths"])
    required = {
        "/api/v1/version",
        "/api/v1/integration/status",
        "/api/v1/integration/summary",
        "/api/v1/integration/compatibility",
        "/api/v1/release/readiness",
        "/api/v1/integration/commands",
        "/api/v1/integration/commands/{command_id}",
    }
    assert not required - paths


def test_version_endpoint():
    response = client.get("/api/v1/version")
    assert response.status_code == 200
    assert response.json()["contractVersion"] == "1.0"


def test_unknown_capability_returns_400(monkeypatch):
    def fail(*args, **kwargs):
        raise ValueError("Unsupported integration capability")

    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.integration.IntegrationService.submit_command", fail
    )
    response = client.post(
        "/api/v1/integration/commands", headers={"Idempotency-Key": "x"}, json={"capability": "bad"}
    )
    assert response.status_code == 400
