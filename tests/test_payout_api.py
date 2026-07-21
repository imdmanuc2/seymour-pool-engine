from fastapi.testclient import TestClient

from seymour_pool_engine.main import app


def test_payout_routes_registered():
    paths = set(app.openapi()["paths"])
    required = {
        "/api/v1/payouts/eligible",
        "/api/v1/payouts/batches",
        "/api/v1/payouts/batches/{payout_batch_id}",
        "/api/v1/payouts/batches/{payout_batch_id}/approve",
        "/api/v1/payouts/batches/{payout_batch_id}/complete",
    }
    assert not required - paths


def test_create_payout_validation_error(monkeypatch):
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.payouts.PayoutService.create",
        lambda self, **kwargs: (_ for _ in ()).throw(ValueError("bad payout")),
    )
    response = TestClient(app).post(
        "/api/v1/payouts/batches",
        json={
            "batchKey": "bad", "poolId": "btc", "coin": "BTC",
            "network": "mainnet", "sourceWalletId": "00000000-0000-0000-0000-000000000001",
            "items": [{"miner": "m", "destinationAddress": "a", "amount": "1"}],
        },
    )
    assert response.status_code == 400
