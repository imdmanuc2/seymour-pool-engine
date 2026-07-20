from datetime import UTC, datetime
from uuid import uuid4

from seymour_pool_engine.services.statistics_service import StatisticsService


class FakeRepository:
    def overview(self, **kwargs):
        return {
            "accepted_difficulty": 600.0,
            "accepted_shares": 8,
            "rejected_shares": 1,
            "stale_shares": 1,
            "active_workers": 2,
            "active_pools": 1,
            "last_share_at": datetime.now(UTC),
        }

    def pools(self, **kwargs):
        return [{"pool_id": "btc-solo", **self.overview()}]

    def workers(self, **kwargs):
        return [
            {
                "worker_id": uuid4(),
                "pool_id": "btc-solo",
                "miner": "seymour",
                "worker": "001",
                **self.overview(),
            }
        ]


def test_overview_calculates_hashrate_and_quality_rates() -> None:
    result = StatisticsService(FakeRepository()).overview(window="1m")
    assert result["hashrate"] == 600 * 2**32 / 60
    assert result["efficiency"] == 0.8
    assert result["activeWorkers"] == 2


def test_pool_and_worker_contracts() -> None:
    service = StatisticsService(FakeRepository())
    assert service.pools(window="5m")["pools"][0]["scope"]["id"] == "btc-solo"
    assert service.workers(window="15m")["workers"][0]["worker"] == "001"


def test_invalid_window_and_limit_are_rejected() -> None:
    service = StatisticsService(FakeRepository())
    for call in (
        lambda: service.overview(window="2m"),
        lambda: service.workers(limit=5001),
    ):
        try:
            call()
        except ValueError:
            pass
        else:
            raise AssertionError("Expected ValueError")
