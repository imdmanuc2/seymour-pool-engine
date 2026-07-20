from fastapi.testclient import TestClient

from seymour_pool_engine.main import app


def test_configuration_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/v1/config" in paths
    assert "/api/v1/config/validate" in paths
    assert "/api/v1/config/history" in paths
    assert "/api/v1/config/export" in paths
    assert "/api/v1/config/import" in paths
    assert "/api/v1/config/rollback/{revision_number}" in paths


def test_invalid_developer_fee_validation_is_transparent(monkeypatch):
    class StubService:
        def validate(self, **kwargs):
            return {
                "profileKey": kwargs["profile_key"],
                "domain": kwargs["domain"],
                "valid": False,
                "errors": ["Developer fee cannot be lower than 0.75 percent"],
                "warnings": [],
                "checksum": "abc",
            }

    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.configuration.ConfigurationService",
        StubService,
    )
    response = TestClient(app).post(
        "/api/v1/config/validate",
        json={
            "profileKey": "fees.btc",
            "domain": "developer-fee",
            "configuration": {"enabled": True, "percent": 0.5},
        },
    )
    assert response.status_code == 200
    assert response.json()["valid"] is False
