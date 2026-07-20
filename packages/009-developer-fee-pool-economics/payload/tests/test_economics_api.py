from fastapi.testclient import TestClient

from seymour_pool_engine.main import app


def test_economics_policy_is_public_and_transparent():
    response=TestClient(app).get("/api/v1/economics/policy")
    assert response.status_code == 200
    body=response.json()
    assert body["developerFeeRequired"] is True
    assert body["minimumDeveloperFeePercent"] == 0.75
    assert body["operatorMayDisableDeveloperFee"] is False
