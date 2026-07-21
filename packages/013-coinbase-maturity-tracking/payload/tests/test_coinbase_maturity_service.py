from datetime import UTC, datetime
from uuid import uuid4

import pytest

from seymour_pool_engine.services.coinbase_maturity_service import (
    CoinbaseMaturityService,
)


class FakeRepository:
    def __init__(self, required_confirmations=100):
        self.required_confirmations = required_confirmations
        self.observed = None

    def policy(self, *, coin, network):
        return {"required_confirmations": self.required_confirmations}

    def observe(self, **values):
        self.observed = values
        now = datetime.now(UTC)
        return {
            "maturity_record_id": uuid4(),
            "block_id": values["block_id"],
            "pool_id": values["pool_id"],
            "coin": values["coin"],
            "network": values["network"],
            "block_height": values["block_height"],
            "block_hash": values.get("block_hash"),
            "confirmations": values["confirmations"],
            "required_confirmations": values["required_confirmations"],
            "status": values["status"],
            "observed_tip_height": values.get("observed_tip_height"),
            "last_observed_at": now,
            "matured_at": now if values["status"] == "mature" else None,
            "orphaned_at": now if values["status"] == "orphaned" else None,
        }


def test_observation_is_immature_below_threshold():
    repository = FakeRepository(required_confirmations=100)
    result = CoinbaseMaturityService(repository).observe(
        block_id=uuid4(), pool_id="btc", coin="btc", network="mainnet",
        block_height=900000, confirmations=99,
    )
    assert result["status"] == "immature"
    assert result["remainingConfirmations"] == 1


def test_observation_matures_at_threshold():
    repository = FakeRepository(required_confirmations=100)
    result = CoinbaseMaturityService(repository).observe(
        block_id=uuid4(), pool_id="btc", coin="BTC", network="mainnet",
        block_height=900000, confirmations=100,
    )
    assert result["status"] == "mature"
    assert repository.observed["status"] == "mature"


def test_orphaned_observation_overrides_confirmations():
    repository = FakeRepository(required_confirmations=100)
    result = CoinbaseMaturityService(repository).observe(
        block_id=uuid4(), pool_id="btc", coin="BTC", network="mainnet",
        block_height=900000, confirmations=120, orphaned=True,
    )
    assert result["status"] == "orphaned"


def test_observation_rejects_negative_confirmations():
    with pytest.raises(ValueError, match="negative"):
        CoinbaseMaturityService(FakeRepository()).observe(
            block_id=uuid4(), pool_id="btc", coin="BTC", network="mainnet",
            block_height=900000, confirmations=-1,
        )
