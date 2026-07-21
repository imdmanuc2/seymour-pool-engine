from fastapi.testclient import TestClient

from seymour_pool_engine.main import app


def test_coinbase_maturity_routes_registered():
    paths = set(app.openapi()["paths"])
    assert "/api/v1/coinbase-maturity/policies" in paths
    assert "/api/v1/coinbase-maturity/observations" in paths
    assert "/api/v1/coinbase-maturity/records" in paths
    assert "/api/v1/coinbase-maturity/summary" in paths


def test_maturity_policy_validation(monkeypatch):
    monkeypatch.setattr(
        "seymour_pool_engine.api.routes.coinbase_maturity."
        "CoinbaseMaturityService.set_policy",
        lambda self, **kwargs: (_ for _ in ()).throw(ValueError("bad policy")),
    )
    response = TestClient(app).put(
        "/api/v1/coinbase-maturity/policies/BTC/mainnet",
        json={"requiredConfirmations": 0},
    )
    assert response.status_code == 400
