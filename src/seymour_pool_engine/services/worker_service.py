from datetime import UTC, datetime, timedelta
from typing import Any

from seymour_pool_engine.config import get_settings
from seymour_pool_engine.providers.base import MiningProvider
from seymour_pool_engine.providers.miningcore import MiningCoreProvider
from seymour_pool_engine.repositories.worker_repository import WorkerRepository

VALID_LIFECYCLE_STATES = {"active", "offline", "disabled", "retired", "unknown"}


class WorkerService:
    def __init__(
        self,
        *,
        repository: WorkerRepository | None = None,
        provider: MiningProvider | None = None,
        provider_name: str = "miningcore",
    ) -> None:
        self.repository = repository or WorkerRepository()
        self.provider = provider or MiningCoreProvider()
        self.provider_name = provider_name

    def synchronize(self, pool_id: str | None = None) -> dict[str, Any]:
        settings = get_settings()
        observations = self.provider.list_workers(pool_id)
        active_after = datetime.now(UTC) - timedelta(
            seconds=settings.worker_active_window_seconds
        )
        result = self.repository.synchronize(
            provider_name=self.provider_name,
            observations=observations,
            active_after=active_after,
            pool_id=pool_id,
        )
        return {
            "provider": self.provider_name,
            "poolId": pool_id,
            "synchronizedAt": datetime.now(UTC).isoformat(),
            **result,
        }

    def list_workers(
        self,
        *,
        pool_id: str | None = None,
        lifecycle_state: str | None = None,
        provider_name: str | None = None,
    ) -> dict[str, Any]:
        if lifecycle_state is not None and lifecycle_state not in VALID_LIFECYCLE_STATES:
            raise ValueError(f"Unsupported worker lifecycle state: {lifecycle_state}")

        workers = self.repository.list_workers(
            pool_id=pool_id,
            lifecycle_state=lifecycle_state,
            provider_name=provider_name,
        )
        serialized = [self._serialize(row) for row in workers]
        return {
            "count": len(serialized),
            "poolId": pool_id,
            "state": lifecycle_state,
            "provider": provider_name,
            "workers": serialized,
        }

    @staticmethod
    def _serialize(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "workerId": str(row["worker_id"]),
            "provider": row["provider_name"],
            "poolId": row["pool_id"],
            "miner": row["miner"],
            "worker": row["worker"],
            "state": row["lifecycle_state"],
            "hashrate": row["hashrate"],
            "sharesPerSecond": row["shares_per_second"],
            "firstSeenAt": row["first_seen_at"].isoformat(),
            "lastSeenAt": row["last_seen_at"].isoformat(),
            "providerObservedAt": row["provider_observed_at"].isoformat(),
            "lastSyncAt": row["last_sync_at"].isoformat(),
            "offlineSince": (
                row["offline_since"].isoformat() if row["offline_since"] else None
            ),
            "metadata": row["metadata"],
        }


def synchronize_workers(pool_id: str | None = None) -> dict[str, Any]:
    return WorkerService().synchronize(pool_id)


def get_workers(
    *,
    pool_id: str | None = None,
    lifecycle_state: str | None = None,
    provider_name: str | None = None,
) -> dict[str, Any]:
    return WorkerService().list_workers(
        pool_id=pool_id,
        lifecycle_state=lifecycle_state,
        provider_name=provider_name,
    )
