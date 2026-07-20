from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from seymour_pool_engine.repositories.block_repository import BlockRepository

BLOCK_STATUSES = {"candidate", "immature", "confirmed", "orphaned"}
MAX_BLOCK_LIMIT = 5000


class BlockService:
    def __init__(self, repository: BlockRepository | None = None) -> None:
        self.repository = repository or BlockRepository()

    def synchronize(
        self,
        *,
        provider_name: str,
        observations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not provider_name.strip():
            raise ValueError("Block provider name is required")
        normalized = [self._normalize_observation(item) for item in observations]
        result = self.repository.upsert(
            provider_name=provider_name.strip(),
            observations=normalized,
        )
        return {
            "provider": provider_name.strip(),
            "observed": len(normalized),
            "synchronizedAt": datetime.now(UTC).isoformat(),
            **result,
        }

    def list_blocks(
        self,
        *,
        pool_id: str | None = None,
        status: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        normalized_status = self._validate_status(status)
        normalized_limit = self._normalize_limit(limit)
        rows = self.repository.list_blocks(
            pool_id=pool_id,
            status=normalized_status,
            since=since,
            limit=normalized_limit,
        )
        return {
            "count": len(rows),
            "poolId": pool_id,
            "status": normalized_status,
            "since": since.isoformat() if since else None,
            "limit": normalized_limit,
            "blocks": [self._serialize_block(row) for row in rows],
        }

    def get_block(self, block_id: UUID) -> dict[str, Any] | None:
        row = self.repository.get(block_id)
        if row is None:
            return None
        return {
            **self._serialize_block(row),
            "events": [self._serialize_event(event) for event in self.repository.events(block_id)],
        }

    def statistics(self, *, pool_id: str | None = None) -> dict[str, Any]:
        row = self.repository.statistics(pool_id=pool_id)
        return {
            "poolId": pool_id,
            "calculatedAt": datetime.now(UTC).isoformat(),
            "totalBlocks": int(row.get("total_blocks") or 0),
            "candidateBlocks": int(row.get("candidate_blocks") or 0),
            "immatureBlocks": int(row.get("immature_blocks") or 0),
            "confirmedBlocks": int(row.get("confirmed_blocks") or 0),
            "orphanedBlocks": int(row.get("orphaned_blocks") or 0),
            "confirmedReward": float(row.get("confirmed_reward") or 0),
            "lastBlockAt": row["last_block_at"].isoformat() if row.get("last_block_at") else None,
        }

    @staticmethod
    def _normalize_observation(item: dict[str, Any]) -> dict[str, Any]:
        required = ("provider_block_key", "pool_id", "block_height", "status", "found_at")
        missing = [field for field in required if item.get(field) in (None, "")]
        if missing:
            raise ValueError(f"Block observation is missing: {', '.join(missing)}")
        status = BlockService._validate_status(str(item["status"]))
        confirmations = int(item.get("confirmations", 0))
        if confirmations < 0:
            raise ValueError("Block confirmations cannot be negative")
        found_at = item["found_at"]
        if not isinstance(found_at, datetime):
            raise ValueError("Block found_at must be a datetime")
        normalized = dict(item)
        normalized["status"] = status
        normalized["confirmations"] = confirmations
        normalized["worker"] = str(item.get("worker") or "")
        normalized["metadata"] = dict(item.get("metadata") or {})
        normalized["last_checked_at"] = item.get("last_checked_at") or datetime.now(UTC)
        if status == "confirmed" and not normalized.get("confirmed_at"):
            normalized["confirmed_at"] = datetime.now(UTC)
        if status == "orphaned" and not normalized.get("orphaned_at"):
            normalized["orphaned_at"] = datetime.now(UTC)
        return normalized

    @staticmethod
    def _validate_status(status: str | None) -> str | None:
        if status is None:
            return None
        normalized = status.strip().lower()
        if normalized not in BLOCK_STATUSES:
            allowed = ", ".join(sorted(BLOCK_STATUSES))
            raise ValueError(f"Unsupported block status: {status}. Expected one of: {allowed}")
        return normalized

    @staticmethod
    def _normalize_limit(limit: int) -> int:
        if limit < 1 or limit > MAX_BLOCK_LIMIT:
            raise ValueError(f"Block limit must be between 1 and {MAX_BLOCK_LIMIT}")
        return limit

    @staticmethod
    def _serialize_block(row: dict[str, Any]) -> dict[str, Any]:
        reward = row.get("reward")
        return {
            "blockId": str(row["block_id"]),
            "provider": row["provider_name"],
            "providerBlockKey": row["provider_block_key"],
            "poolId": row["pool_id"],
            "blockHeight": int(row["block_height"]),
            "blockHash": row.get("block_hash"),
            "status": row["status"],
            "confirmations": int(row.get("confirmations") or 0),
            "networkDifficulty": row.get("network_difficulty"),
            "reward": float(reward) if isinstance(reward, Decimal) else reward,
            "miner": row.get("miner"),
            "worker": row.get("worker") or "",
            "shareId": str(row["share_id"]) if row.get("share_id") else None,
            "foundAt": row["found_at"].isoformat(),
            "confirmedAt": row["confirmed_at"].isoformat() if row.get("confirmed_at") else None,
            "orphanedAt": row["orphaned_at"].isoformat() if row.get("orphaned_at") else None,
            "lastCheckedAt": (
                row["last_checked_at"].isoformat() if row.get("last_checked_at") else None
            ),
            "createdAt": row["created_at"].isoformat(),
            "updatedAt": row["updated_at"].isoformat(),
            "metadata": row.get("metadata") or {},
        }

    @staticmethod
    def _serialize_event(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "eventId": str(row["event_id"]),
            "type": row["event_type"],
            "previousStatus": row.get("previous_status"),
            "newStatus": row["new_status"],
            "confirmations": int(row.get("confirmations") or 0),
            "occurredAt": row["occurred_at"].isoformat(),
            "details": row.get("details") or {},
        }


def get_blocks(**kwargs: Any) -> dict[str, Any]:
    return BlockService().list_blocks(**kwargs)


def get_block(block_id: UUID) -> dict[str, Any] | None:
    return BlockService().get_block(block_id)


def get_block_statistics(*, pool_id: str | None = None) -> dict[str, Any]:
    return BlockService().statistics(pool_id=pool_id)


def synchronize_blocks(
    *, provider_name: str, observations: list[dict[str, Any]]
) -> dict[str, Any]:
    return BlockService().synchronize(
        provider_name=provider_name,
        observations=observations,
    )
