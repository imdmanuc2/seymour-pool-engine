from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from seymour_pool_engine.services.payout_service import PayoutService


class FakeRepository:
    def __init__(self):
        self.created = None

    def create_batch(self, **values):
        self.created = values
        return {
            "payout_batch_id": uuid4(), "batch_key": values["batch_key"],
            "pool_id": values["pool_id"], "coin": values["coin"],
            "network": values["network"], "source_wallet_id": values["source_wallet_id"],
            "status": "draft", "minimum_payout": values["minimum_payout"],
            "total_amount": Decimal("1.25"), "item_count": len(values["items"]),
            "transaction_id": None, "failure_reason": None,
            "created_at": datetime.now(UTC),
        }


def test_create_batch_normalizes_amounts():
    repository = FakeRepository()
    result = PayoutService(repository).create(
        batch_key="btc-1", pool_id="btc", coin="btc", network="mainnet",
        source_wallet_id=uuid4(), minimum_payout="0.01", requested_by="operator",
        items=[{
            "worker_id": uuid4(), "miner": "m1", "worker": "w1",
            "destination_address": " address ", "amount": "1.25",
        }],
    )
    assert result["status"] == "draft"
    assert repository.created["coin"] == "BTC"
    assert repository.created["items"][0]["amount"] == Decimal("1.25")
    assert repository.created["items"][0]["destination_address"] == "address"


def test_create_batch_rejects_empty_items():
    with pytest.raises(ValueError, match="at least one"):
        PayoutService(FakeRepository()).create(
            batch_key="empty", pool_id="btc", coin="BTC", network="mainnet",
            source_wallet_id=uuid4(), items=[],
        )


def test_create_batch_rejects_zero_amount():
    with pytest.raises(ValueError, match="greater than zero"):
        PayoutService(FakeRepository()).create(
            batch_key="zero", pool_id="btc", coin="BTC", network="mainnet",
            source_wallet_id=uuid4(), items=[{
                "miner": "m1", "worker": "", "destination_address": "a", "amount": "0"
            }],
        )
