from decimal import Decimal
from uuid import uuid4

import pytest

from seymour_pool_engine.services.economics_service import EconomicsService


class Repo:
    def __init__(self):
        self.profile={"fee_profile_id": uuid4(), "pool_id": "btc", "coin": "BTC",
                      "developer_fee_percent": Decimal("0.75"), "operator_fee_percent": Decimal("1"),
                      "developer_destination": "dev-wallet", "operator_destination": "pool-wallet"}
    def upsert_fee_profile(self, **values): return {"fee_profile_id": uuid4(), **values}
    def get_fee_profile(self, **kwargs): return self.profile
    def latest_integrity_hash(self, **kwargs): return "previous"
    def create_calculation(self, **kwargs): return {"rewardCalculationId": str(uuid4()), "created": True}
    def economics_summary(self, **kwargs): return {"minimumDeveloperFeePercent": 0.75}


def test_fee_below_minimum_is_rejected():
    with pytest.raises(ValueError, match="0.75"):
        EconomicsService(Repo()).configure_fee_profile(pool_id="btc", coin="BTC",
            developer_fee_percent=Decimal("0.74"), developer_destination="dev")


def test_operator_can_increase_developer_fee():
    result=EconomicsService(Repo()).configure_fee_profile(pool_id="btc", coin="BTC",
        developer_fee_percent=Decimal("1.25"), developer_destination="dev")
    assert result["developerFeePercent"] == 1.25


def test_transparent_fee_allocation_balances_exactly():
    result=EconomicsService(Repo()).calculate(block_id=uuid4(), pool_id="btc", coin="BTC",
        policy="prop", gross_reward=Decimal("10"),
        worker_weights=[{"recipientKey":"alice", "weight":3}, {"recipientKey":"bob", "weight":1}])
    assert sum(Decimal(str(x["amount"])) for x in result["allocations"]) == Decimal("10.0")
    assert result["developerFeePercent"] == 0.75
    assert result["integrityHash"]


def test_solo_requires_one_recipient():
    with pytest.raises(ValueError, match="exactly one"):
        EconomicsService(Repo()).calculate(block_id=uuid4(), pool_id="btc", coin="BTC",
            policy="solo", gross_reward=Decimal("1"),
            worker_weights=[{"recipientKey":"a", "weight":1}, {"recipientKey":"b", "weight":1}])
