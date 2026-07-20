from datetime import UTC, datetime
from uuid import uuid4

import pytest

from seymour_pool_engine.services.wallet_service import WalletService


class FakeRepository:
    def __init__(self):
        self.row = None

    def create_wallet(self, **values):
        self.row = {
            "wallet_id": uuid4(),
            "validation_status": "pending",
            "validated_at": None,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            **values,
        }
        return self.row

    def list_wallets(self, **kwargs):
        return [self.row] if self.row else []

    def get_wallet(self, wallet_id):
        return self.row

    def set_validation(self, **kwargs):
        self.row["validation_status"] = "valid" if kwargs["valid"] else "invalid"
        self.row["validated_at"] = datetime.now(UTC)
        return self.row

    def update_status(self, **kwargs):
        self.row["status"] = kwargs["status"]
        return self.row

    def wallet_events(self, wallet_id):
        return []


def test_create_and_validate_wallet():
    service = WalletService(FakeRepository())
    wallet = service.create(
        wallet_key="btc-dev",
        pool_id="btc",
        coin="btc",
        network="mainnet",
        purpose="developer",
        address="bc1qexampleaddress123456",
        status="active",
        created_by="test",
    )
    assert wallet["coin"] == "BTC"
    result = service.validate(wallet_id=uuid4(), actor="test")
    assert result["valid"] is True


def test_rejects_testnet_address_on_mainnet():
    service = WalletService(FakeRepository())
    with pytest.raises(ValueError):
        service.create(
            wallet_key="bad",
            coin="btc",
            network="mainnet",
            purpose="pool",
            address="tb1qexampleaddress123456",
            status="active",
            created_by="test",
        )
