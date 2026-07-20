from uuid import uuid4

from fastapi.testclient import TestClient

from seymour_pool_engine.main import app

client = TestClient(app)


def test_collect_health_route(monkeypatch):
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.monitoring.collect_health",
        lambda **_: {
            "scopeType": "engine",
            "scopeId": None,
            "status": "healthy",
            "observedAt": "2026-07-20T00:00:00Z",
            "observations": [],
            "observationIds": [],
            "alertsCreatedOrUpdated": 0,
        },
    )
    response = client.post("/api/v1/monitoring/health/collect", json={})
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_alert_acknowledge_not_found(monkeypatch):
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.monitoring.acknowledge_alert",
        lambda **_: (_ for _ in ()).throw(LookupError("active alert not found")),
    )
    response = client.post(
        f"/api/v1/monitoring/alerts/{uuid4()}/acknowledge",
        json={"actor": "operator"},
    )
    assert response.status_code == 404
