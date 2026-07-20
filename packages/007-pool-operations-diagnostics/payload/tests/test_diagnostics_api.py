from fastapi.testclient import TestClient

from seymour_pool_engine.main import app

client = TestClient(app)


def test_readiness_route(monkeypatch):
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.diagnostics.run_pool_diagnostics",
        lambda **_: {
            "diagnosticRunId": None,
            "poolId": None,
            "operation": "pool.readiness",
            "status": "passed",
            "readinessScore": 100,
            "summary": "ready",
            "checks": [],
        },
    )
    response = client.get("/api/v1/operations/readiness")
    assert response.status_code == 200
    assert response.json()["readinessScore"] == 100
