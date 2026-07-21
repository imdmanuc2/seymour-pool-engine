from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from seymour_pool_engine.services.payment_scheduler_service import PaymentSchedulerService


def profile(**overrides):
    values = {
        "scheduler_profile_id": uuid4(), "pool_id": "btc", "coin": "BTC",
        "network": "mainnet", "source_wallet_id": uuid4(), "enabled": True,
        "schedule_type": "daily", "schedule_hour": 2, "schedule_weekday": None,
        "schedule_monthday": None, "minimum_payout": Decimal("0.005"),
        "absolute_minimum": Decimal("0.001"), "maximum_payout": None,
        "maximum_behavior": "pay_full", "retry_limit": 3,
        "retry_backoff_seconds": 300, "last_run_at": None, "next_run_at": None,
    }
    values.update(overrides)
    return values


def test_evaluate_uses_pool_threshold():
    result = PaymentSchedulerService.evaluate(
        profile=profile(), row={
            "pool_id": "btc", "miner": "m", "worker": "w", "worker_id": uuid4(),
            "confirmed_balance": Decimal("0.006"), "destination_address": "bc1qtest",
            "policy_enabled": None, "worker_minimum_payout": None,
            "worker_schedule_type": None,
        },
    )
    assert result is not None
    assert result["payout_amount"] == Decimal("0.006")


def test_evaluate_skips_below_threshold():
    result = PaymentSchedulerService.evaluate(
        profile=profile(), row={
            "pool_id": "btc", "miner": "m", "worker": "w", "worker_id": uuid4(),
            "confirmed_balance": Decimal("0.004"), "destination_address": "bc1qtest",
            "policy_enabled": None, "worker_minimum_payout": None,
            "worker_schedule_type": None,
        },
    )
    assert result is None


def test_worker_threshold_can_be_higher():
    result = PaymentSchedulerService.evaluate(
        profile=profile(), row={
            "pool_id": "btc", "miner": "m", "worker": "w", "worker_id": uuid4(),
            "confirmed_balance": Decimal("0.006"), "destination_address": "bc1qtest",
            "policy_enabled": True, "worker_minimum_payout": Decimal("0.01"),
            "worker_schedule_type": None,
        },
    )
    assert result is None


def test_absolute_minimum_overrides_too_low_worker_threshold():
    result = PaymentSchedulerService.evaluate(
        profile=profile(absolute_minimum=Decimal("0.01")), row={
            "pool_id": "btc", "miner": "m", "worker": "w", "worker_id": uuid4(),
            "confirmed_balance": Decimal("0.009"), "destination_address": "bc1qtest",
            "policy_enabled": True, "worker_minimum_payout": Decimal("0.001"),
            "worker_schedule_type": None,
        },
    )
    assert result is None


def test_cap_and_carry_limits_payout():
    result = PaymentSchedulerService.evaluate(
        profile=profile(
            maximum_payout=Decimal("0.25"), maximum_behavior="cap_and_carry"
        ),
        row={
            "pool_id": "btc", "miner": "m", "worker": "w", "worker_id": uuid4(),
            "confirmed_balance": Decimal("0.40"), "destination_address": "bc1qtest",
            "policy_enabled": True, "worker_minimum_payout": None,
            "worker_schedule_type": None,
        },
    )
    assert result is not None
    assert result["payout_amount"] == Decimal("0.25")


def test_daily_next_run_moves_to_next_day():
    now = datetime(2026, 7, 20, 3, 0, tzinfo=UTC)
    result = PaymentSchedulerService.next_run_at(profile(), now)
    assert result == datetime(2026, 7, 21, 2, 0, tzinfo=UTC)


def test_weekly_requires_weekday():
    class FakeRepository:
        def upsert_profile(self, **values):
            return values

    with pytest.raises(ValueError, match="weekday"):
        PaymentSchedulerService(FakeRepository()).configure_profile(
            pool_id="btc", coin="BTC", network="mainnet",
            source_wallet_id=uuid4(), schedule_type="weekly",
            minimum_payout="0.01",
        )
