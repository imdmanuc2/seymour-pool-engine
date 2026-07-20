from unittest.mock import patch

from fastapi.testclient import TestClient

from seymour_pool_engine.main import create_app

client = TestClient(create_app())


def test_blocks_routes_are_registered() -> None:
    paths = client.app.openapi()["paths"]
    assert "/api/v1/blocks" in paths
    assert "/api/v1/blocks/statistics" in paths
    assert "/api/v1/blocks/{block_id}" in paths
    assert "/api/v1/blocks/sync" in paths


def test_blocks_list_contract() -> None:
    with patch(
        "seymour_pool_engine.api.routes.blocks.get_blocks",
        return_value={"count": 0, "blocks": []},
    ):
        response = client.get("/api/v1/blocks")
    assert response.status_code == 200
    assert response.json()["count"] == 0


def test_sync_rejects_invalid_lifecycle_status() -> None:
    response = client.post(
        "/api/v1/blocks/sync",
        json={
            "provider": "synthetic",
            "blocks": [
                {
                    "providerBlockKey": "bad",
                    "poolId": "btc-solo",
                    "blockHeight": 1,
                    "status": "paid",
                    "foundAt": "2026-07-20T00:00:00Z",
                }
            ],
        },
    )
    assert response.status_code == 400
