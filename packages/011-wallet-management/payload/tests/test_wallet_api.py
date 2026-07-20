from fastapi.testclient import TestClient

from seymour_pool_engine.main import app


def test_wallet_routes_registered():
    paths = {route.path for route in app.routes}
    assert "/api/v1/wallets" in paths
    assert "/api/v1/wallets/{wallet_id}" in paths
    assert "/api/v1/workers/{worker_id}/payout-addresses/{coin}" in paths


def test_wallet_validation_error(monkeypatch):
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.wallets.WalletService.create",
        lambda self, **kwargs: (_ for _ in ()).throw(ValueError("bad wallet")),
    )
    response = TestClient(app).post(
        "/api/v1/wallets",
        json={
            "walletKey": "bad",
            "coin": "BTC",
            "network": "mainnet",
            "purpose": "pool",
            "address": "bad",
        },
    )
    assert response.status_code == 400
