from datetime import UTC, datetime, timedelta
from typing import Any

from seymour_pool_engine.repositories.statistics_repository import StatisticsRepository

HASHES_PER_DIFFICULTY = 2**32
WINDOWS = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600}
MAX_WORKERS_LIMIT = 5000


class StatisticsService:
    def __init__(self, repository: StatisticsRepository | None = None) -> None:
        self.repository = repository or StatisticsRepository()

    def overview(self, *, window: str = "5m") -> dict[str, Any]:
        seconds, since = self._window(window)
        return self._serialize_scope(
            self.repository.overview(since=since),
            scope={"type": "platform", "id": "platform"},
            window=window,
            seconds=seconds,
        )

    def pools(self, *, window: str = "5m") -> dict[str, Any]:
        seconds, since = self._window(window)
        rows = self.repository.pools(since=since)
        return {
            "window": window,
            "windowSeconds": seconds,
            "calculatedAt": datetime.now(UTC).isoformat(),
            "count": len(rows),
            "pools": [
                self._serialize_scope(
                    row,
                    scope={"type": "pool", "id": row["pool_id"]},
                    window=window,
                    seconds=seconds,
                )
                for row in rows
            ],
        }

    def workers(
        self,
        *,
        window: str = "5m",
        pool_id: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        if limit < 1 or limit > MAX_WORKERS_LIMIT:
            raise ValueError(f"Worker statistics limit must be between 1 and {MAX_WORKERS_LIMIT}")
        seconds, since = self._window(window)
        rows = self.repository.workers(since=since, pool_id=pool_id, limit=limit)
        return {
            "window": window,
            "windowSeconds": seconds,
            "poolId": pool_id,
            "calculatedAt": datetime.now(UTC).isoformat(),
            "count": len(rows),
            "workers": [self._serialize_worker(row, window, seconds) for row in rows],
        }

    @staticmethod
    def _window(window: str) -> tuple[int, datetime]:
        try:
            seconds = WINDOWS[window]
        except KeyError as exc:
            raise ValueError(f"Unsupported statistics window: {window}") from exc
        return seconds, datetime.now(UTC) - timedelta(seconds=seconds)

    @staticmethod
    def _metrics(row: dict[str, Any], seconds: int) -> dict[str, Any]:
        accepted = int(row.get("accepted_shares") or 0)
        rejected = int(row.get("rejected_shares") or 0)
        stale = int(row.get("stale_shares") or 0)
        total = accepted + rejected + stale
        difficulty = float(row.get("accepted_difficulty") or 0)
        return {
            "hashrate": difficulty * HASHES_PER_DIFFICULTY / seconds,
            "acceptedShares": accepted,
            "rejectedShares": rejected,
            "staleShares": stale,
            "totalShares": total,
            "efficiency": accepted / total if total else 0.0,
            "rejectionRate": rejected / total if total else 0.0,
            "staleRate": stale / total if total else 0.0,
            "lastShareAt": (
                row["last_share_at"].isoformat() if row.get("last_share_at") else None
            ),
        }

    def _serialize_scope(
        self,
        row: dict[str, Any],
        *,
        scope: dict[str, str],
        window: str,
        seconds: int,
    ) -> dict[str, Any]:
        return {
            "scope": scope,
            "window": window,
            "windowSeconds": seconds,
            "calculatedAt": datetime.now(UTC).isoformat(),
            "activeWorkers": int(row.get("active_workers") or 0),
            "activePools": int(row.get("active_pools") or 0),
            **self._metrics(row, seconds),
        }

    def _serialize_worker(
        self,
        row: dict[str, Any],
        window: str,
        seconds: int,
    ) -> dict[str, Any]:
        return {
            "workerId": str(row["worker_id"]) if row.get("worker_id") else None,
            "poolId": row["pool_id"],
            "miner": row["miner"],
            "worker": row["worker"],
            "window": window,
            "windowSeconds": seconds,
            **self._metrics(row, seconds),
        }


def get_statistics_overview(*, window: str = "5m") -> dict[str, Any]:
    return StatisticsService().overview(window=window)


def get_pool_statistics(*, window: str = "5m") -> dict[str, Any]:
    return StatisticsService().pools(window=window)


def get_worker_statistics(
    *, window: str = "5m", pool_id: str | None = None, limit: int = 100
) -> dict[str, Any]:
    return StatisticsService().workers(window=window, pool_id=pool_id, limit=limit)
