from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from seymour_pool_engine.services.reward_service import RewardService


class FakeRepository:
    def __init__(self) -> None:
        self.allocations = []

    def accepted_difficulty_by_worker(self, **_: object) -> list[dict]:
        return [
            {
                "worker_id": uuid4(),
                "miner": "wallet-a",
                "worker": "001",
                "accepted_difficulty": Decimal("75"),
            },
            {
                "worker_id": uuid4(),
                "miner": "wallet-b",
                "worker": "002",
                "accepted_difficulty": Decimal("25"),
            },
        ]

    def create_period(self, **kwargs: object) -> dict:
        self.allocations = kwargs["allocations"]
        return {"reward_period_id": uuid4(), "created": True, "entries": 2}

    def confirm_period(self, _: object) -> dict:
        return {"entriesConfirmed": 2}

    def list_periods(self, **_: object) -> list[dict]:
        return []

    def list_balances(self, **_: object) -> list[dict]:
        return []


def test_calculate_allocates_reward_proportionally() -> None:
    repository = FakeRepository()
    service = RewardService(repository)
    end_at = datetime.now(UTC)
    result = service.calculate(
        block_id=uuid4(),
        pool_id="btc-solo",
        gross_reward=Decimal("4"),
        fee_percent=Decimal("0"),
        start_at=end_at - timedelta(hours=1),
        end_at=end_at,
    )
    assert result["allocationCount"] == 2
    assert repository.allocations[0]["reward_amount"] == Decimal("3.000000000000")
    assert repository.allocations[1]["reward_amount"] == Decimal("1.000000000000")


def test_fee_is_removed_before_allocation() -> None:
    repository = FakeRepository()
    service = RewardService(repository)
    end_at = datetime.now(UTC)
    result = service.calculate(
        block_id=uuid4(),
        pool_id="btc-solo",
        gross_reward=Decimal("4"),
        fee_percent=Decimal("1"),
        start_at=end_at - timedelta(hours=1),
        end_at=end_at,
    )
    assert result["poolFee"] == 0.04
    assert result["distributableReward"] == 3.96


def test_invalid_calculation_inputs_are_rejected() -> None:
    service = RewardService(FakeRepository())
    end_at = datetime.now(UTC)
    for kwargs in (
        {"gross_reward": Decimal("0"), "fee_percent": Decimal("0")},
        {"gross_reward": Decimal("1"), "fee_percent": Decimal("101")},
    ):
        try:
            service.calculate(
                block_id=uuid4(),
                pool_id="btc-solo",
                start_at=end_at - timedelta(hours=1),
                end_at=end_at,
                **kwargs,
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Expected ValueError")
