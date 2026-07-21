from fastapi.testclient import TestClient

from seymour_pool_engine.main import app


def test_security_routes_registered():
    paths = set(app.openapi()["paths"])
    required = {
        "/api/v1/security/principals",
        "/api/v1/security/roles",
        "/api/v1/security/principals/{principal_id}/roles",
        "/api/v1/security/principals/{principal_id}/permissions",
        "/api/v1/security/principals/{principal_id}/api-keys",
        "/api/v1/security/api-keys/{api_key_id}",
        "/api/v1/security/whoami",
        "/api/v1/security/authorize/{permission}",
        "/api/v1/security/events",
    }
    assert not required - paths


def test_short_password_returns_validation_error(monkeypatch):
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.security.SecurityService.create_principal",
        lambda self, **kwargs: (_ for _ in ()).throw(
            ValueError("User passwords must contain at least 12 characters")
        ),
    )
    response = TestClient(app).post(
        "/api/v1/security/principals",
        json={"principalType": "user", "principalName": "alice", "password": "short"},
    )
    assert response.status_code == 400
