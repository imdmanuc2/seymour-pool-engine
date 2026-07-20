from unittest.mock import patch

from fastapi.testclient import TestClient

from seymour_pool_engine.main import create_app

client = TestClient(create_app())


def test_reward_routes_are_registered() -> None:
    paths = client.app.openapi()["paths"]
    assert "/api/v1/rewards" in paths
    assert "/api/v1/rewards/balances" in paths
    assert "/api/v1/rewards/calculate" in paths
    assert "/api/v1/rewards/{reward_period_id}/confirm" in paths


def test_reward_period_list_contract() -> None:
    with patch(
        "seymour_pool_engine.api.routes.rewards.get_reward_periods",
        return_value={"count": 0, "periods": []},
    ):
        response = client.get("/api/v1/rewards")
    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_reward_calculation_rejects_invalid_amount() -> None:
    response = client.post(
        "/api/v1/rewards/calculate",
        json={
            "blockId": "20000000-0000-0000-0000-000000000001",
            "poolId": "btc-solo",
            "grossReward": "0",
            "feePercent": "0",
            "startAt": "2026-07-20T00:00:00Z",
            "endAt": "2026-07-20T01:00:00Z",
        },
    )
    assert response.status_code == 400
