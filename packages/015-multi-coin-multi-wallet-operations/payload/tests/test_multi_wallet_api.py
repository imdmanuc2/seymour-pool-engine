from fastapi.testclient import TestClient

from seymour_pool_engine.main import app


def test_multi_wallet_routes_registered():
    paths = set(app.openapi()["paths"])
    required = {
        "/api/v1/coins",
        "/api/v1/coin-networks",
        "/api/v1/wallet-operations/assignments",
        "/api/v1/wallet-operations/policies",
        "/api/v1/wallet-operations/select",
        "/api/v1/wallet-operations/wallets/{wallet_id}/reserve",
        "/api/v1/wallet-operations/wallets/{wallet_id}/balances",
        "/api/v1/wallet-operations/wallets/{wallet_id}/health",
        "/api/v1/wallet-operations/wallets/{wallet_id}/reconcile",
    }
    assert not required - paths


def test_selection_validation_error(monkeypatch):
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.multi_wallets.MultiWalletService.select",
        lambda self, **kwargs: (_ for _ in ()).throw(
            ValueError("No eligible wallet is available for this payment")
        ),
    )
    response = TestClient(app).post(
        "/api/v1/wallet-operations/select",
        json={
            "coin": "BTC",
            "network": "mainnet",
            "assignmentScope": "pool",
            "scopeKey": "btc",
            "purpose": "payout",
            "amount": "1",
        },
    )
    assert response.status_code == 400
