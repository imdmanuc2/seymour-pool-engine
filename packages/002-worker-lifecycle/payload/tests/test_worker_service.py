from datetime import UTC, datetime, timedelta
from uuid import uuid4

from seymour_pool_engine.providers.models import WorkerSummary
from seymour_pool_engine.services.worker_service import WorkerService


class FakeProvider:
    def list_workers(self, pool_id: str | None = None) -> list[WorkerSummary]:
        return [
            WorkerSummary(
                poolId=pool_id or "btc-solo",
                miner="seymour",
                worker="001",
                hashrate=12_500_000_000,
                sharesPerSecond=0.2,
                observedAt=datetime.now(UTC),
            )
        ]


class FakeRepository:
    def __init__(self) -> None:
        self.sync_args = None

    def synchronize(self, **kwargs):
        self.sync_args = kwargs
        return {"observed": 1, "created": 1, "updated": 0, "markedOffline": 0}

    def list_workers(self, **kwargs):
        now = datetime.now(UTC)
        return [
            {
                "worker_id": uuid4(),
                "provider_name": "miningcore",
                "pool_id": "btc-solo",
                "miner": "seymour",
                "worker": "001",
                "lifecycle_state": "active",
                "hashrate": 12_500_000_000,
                "shares_per_second": 0.2,
                "first_seen_at": now - timedelta(hours=1),
                "last_seen_at": now,
                "provider_observed_at": now,
                "last_sync_at": now,
                "offline_since": None,
                "metadata": {},
            }
        ]


def test_worker_sync_normalizes_provider_observations() -> None:
    repository = FakeRepository()
    service = WorkerService(repository=repository, provider=FakeProvider())

    result = service.synchronize("btc-solo")

    assert result["provider"] == "miningcore"
    assert result["created"] == 1
    assert repository.sync_args["pool_id"] == "btc-solo"
    assert len(repository.sync_args["observations"]) == 1


def test_worker_list_returns_spe_owned_contract() -> None:
    service = WorkerService(repository=FakeRepository(), provider=FakeProvider())

    result = service.list_workers(lifecycle_state="active")

    assert result["count"] == 1
    assert result["workers"][0]["workerId"]
    assert result["workers"][0]["provider"] == "miningcore"
    assert result["workers"][0]["state"] == "active"


def test_worker_list_rejects_unknown_state() -> None:
    service = WorkerService(repository=FakeRepository(), provider=FakeProvider())

    try:
        service.list_workers(lifecycle_state="ghost")
    except ValueError as exc:
        assert "Unsupported worker lifecycle state" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
