from fastapi.testclient import TestClient

from seymour_pool_engine.main import app

client = TestClient(app)


def test_reliability_routes_are_registered():
    paths = set(app.openapi()["paths"])
    required = {
        "/api/v1/reliability/backup-profiles",
        "/api/v1/reliability/backup-profiles/{profile_key}",
        "/api/v1/reliability/backup-targets",
        "/api/v1/reliability/backup-targets/{target_key}",
        "/api/v1/reliability/backup-profiles/{profile_key}/runs",
        "/api/v1/reliability/backup-runs",
        "/api/v1/reliability/backup-runs/{backup_run_id}/restore-runs",
        "/api/v1/reliability/disaster-recovery-playbooks",
    }
    assert not required - paths


def test_invalid_profile_returns_400(monkeypatch):
    def fail(*args, **kwargs):
        raise ValueError("Unsupported backup type")

    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.reliability.ReliabilityService.put_profile", fail
    )
    response = client.put(
        "/api/v1/reliability/backup-profiles/test",
        json={"displayName": "Test", "backupType": "invalid"},
    )
    assert response.status_code == 400
