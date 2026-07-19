from datetime import UTC, datetime
from typing import Any, Protocol

from seymour_pool_engine.providers.miningcore import MiningCoreProvider
from seymour_pool_engine.providers.models import ShareSummary
from seymour_pool_engine.repositories.share_repository import ShareRepository

MAX_SHARE_LIMIT = 5000


class ShareProvider(Protocol):
    def list_shares(
        self,
        *,
        pool_id: str | None = None,
        since: datetime | None = None,
        limit: int = 1000,
    ) -> list[ShareSummary]: ...


class ShareService:
    def __init__(
        self,
        *,
        repository: ShareRepository | None = None,
        provider: ShareProvider | None = None,
        provider_name: str = "miningcore",
    ) -> None:
        self.repository = repository or ShareRepository()
        self.provider = provider or MiningCoreProvider()
        self.provider_name = provider_name

    def synchronize(
        self,
        *,
        pool_id: str | None = None,
        since: datetime | None = None,
        limit: int = 1000,
    ) -> dict[str, Any]:
        normalized_limit = self._normalize_limit(limit)
        observations = self.provider.list_shares(
            pool_id=pool_id,
            since=since,
            limit=normalized_limit,
        )
        result = self.repository.ingest(
            provider_name=self.provider_name,
            observations=observations,
        )
        return {
            "provider": self.provider_name,
            "poolId": pool_id,
            "since": since.isoformat() if since else None,
            "limit": normalized_limit,
            "synchronizedAt": datetime.now(UTC).isoformat(),
            **result,
        }

    def list_shares(
        self,
        *,
        pool_id: str | None = None,
        miner: str | None = None,
        worker: str | None = None,
        provider_name: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        normalized_limit = self._normalize_limit(limit)
        rows = self.repository.list_shares(
            pool_id=pool_id,
            miner=miner,
            worker=worker,
            provider_name=provider_name,
            since=since,
            limit=normalized_limit,
        )
        return {
            "count": len(rows),
            "poolId": pool_id,
            "miner": miner,
            "worker": worker,
            "provider": provider_name,
            "since": since.isoformat() if since else None,
            "limit": normalized_limit,
            "shares": [self._serialize_share(row) for row in rows],
        }

    @staticmethod
    def _normalize_limit(limit: int) -> int:
        if limit < 1 or limit > MAX_SHARE_LIMIT:
            raise ValueError(f"Share limit must be between 1 and {MAX_SHARE_LIMIT}")
        return limit

    @staticmethod
    def _serialize_share(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "shareId": str(row["share_id"]),
            "provider": row["provider_name"],
            "providerShareKey": row["provider_share_key"],
            "workerId": str(row["worker_id"]) if row["worker_id"] else None,
            "poolId": row["pool_id"],
            "miner": row["miner"],
            "worker": row["worker"],
            "difficulty": row["difficulty"],
            "networkDifficulty": row["network_difficulty"],
            "blockHeight": row["block_height"],
            "ipAddress": row["ip_address"],
            "userAgent": row["user_agent"],
            "providerCreatedAt": row["provider_created_at"].isoformat(),
            "ingestedAt": row["ingested_at"].isoformat(),
            "metadata": row["metadata"],
        }


def synchronize_shares(
    *,
    pool_id: str | None = None,
    since: datetime | None = None,
    limit: int = 1000,
) -> dict[str, Any]:
    return ShareService().synchronize(pool_id=pool_id, since=since, limit=limit)


def get_shares(
    *,
    pool_id: str | None = None,
    miner: str | None = None,
    worker: str | None = None,
    provider_name: str | None = None,
    since: datetime | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    return ShareService().list_shares(
        pool_id=pool_id,
        miner=miner,
        worker=worker,
        provider_name=provider_name,
        since=since,
        limit=limit,
    )
