from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from seymour_pool_engine.repositories.coinbase_maturity_repository import (
    CoinbaseMaturityRepository,
)

MATURITY_STATUSES = {"immature", "mature", "orphaned"}


class CoinbaseMaturityService:
    def __init__(self, repository: CoinbaseMaturityRepository | None = None) -> None:
        self.repository = repository or CoinbaseMaturityRepository()

    def policies(self) -> list[dict[str, Any]]:
        return [self._policy(row) for row in self.repository.policies()]

    def set_policy(self, **values: Any) -> dict[str, Any]:
        coin = self._coin(values["coin"])
        network = self._network(values["network"])
        required = int(values["required_confirmations"])
        if required < 1 or required > 100000:
            raise ValueError("Required confirmations must be between 1 and 100000")
        row = self.repository.upsert_policy(
            coin=coin,
            network=network,
            required_confirmations=required,
            enabled=bool(values.get("enabled", True)),
            actor=str(values.get("actor") or "api").strip() or "api",
            metadata=dict(values.get("metadata") or {}),
        )
        return self._policy(row)

    def observe(self, **values: Any) -> dict[str, Any]:
        coin = self._coin(values["coin"])
        network = self._network(values["network"])
        confirmations = int(values.get("confirmations", 0))
        if confirmations < 0:
            raise ValueError("Confirmations cannot be negative")
        policy = self.repository.policy(coin=coin, network=network)
        if policy is None:
            raise ValueError(f"No enabled maturity policy exists for {coin} {network}")
        required = int(policy["required_confirmations"])
        orphaned = bool(values.get("orphaned", False))
        status = "orphaned" if orphaned else (
            "mature" if confirmations >= required else "immature"
        )
        row = self.repository.observe(
            block_id=values["block_id"],
            pool_id=str(values["pool_id"]).strip(),
            coin=coin,
            network=network,
            block_height=int(values["block_height"]),
            block_hash=(str(values.get("block_hash") or "").strip() or None),
            confirmations=confirmations,
            required_confirmations=required,
            status=status,
            observed_tip_height=values.get("observed_tip_height"),
            actor=str(values.get("actor") or "api").strip() or "api",
            metadata=dict(values.get("metadata") or {}),
        )
        return self._record(row)

    def records(
        self, *, pool_id: str | None = None, status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        normalized_status = None
        if status is not None:
            normalized_status = status.strip().lower()
            if normalized_status not in MATURITY_STATUSES:
                raise ValueError("Unsupported maturity status")
        normalized_limit = max(1, min(int(limit), 500))
        rows = self.repository.records(
            pool_id=pool_id, status=normalized_status, limit=normalized_limit
        )
        return [self._record(row) for row in rows]

    def summary(self, *, pool_id: str | None = None) -> dict[str, Any]:
        row = self.repository.summary(pool_id=pool_id)
        return {
            "poolId": pool_id,
            "totalRecords": int(row.get("total_records") or 0),
            "immatureRecords": int(row.get("immature_records") or 0),
            "matureRecords": int(row.get("mature_records") or 0),
            "orphanedRecords": int(row.get("orphaned_records") or 0),
            "calculatedAt": datetime.now(UTC).isoformat(),
        }

    @staticmethod
    def _coin(value: Any) -> str:
        coin = str(value).strip().upper()
        if not coin or len(coin) > 16:
            raise ValueError("A valid coin symbol is required")
        return coin

    @staticmethod
    def _network(value: Any) -> str:
        network = str(value).strip().lower()
        if network not in {"mainnet", "testnet", "regtest"}:
            raise ValueError("Network must be mainnet, testnet, or regtest")
        return network

    @staticmethod
    def _policy(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "policyId": str(row["policy_id"]),
            "coin": row["coin"],
            "network": row["network"],
            "requiredConfirmations": int(row["required_confirmations"]),
            "enabled": bool(row["enabled"]),
            "updatedAt": row["updated_at"].isoformat(),
        }

    @staticmethod
    def _record(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "maturityRecordId": str(row["maturity_record_id"]),
            "blockId": str(row["block_id"]),
            "poolId": row["pool_id"],
            "coin": row["coin"],
            "network": row["network"],
            "blockHeight": int(row["block_height"]),
            "blockHash": row.get("block_hash"),
            "confirmations": int(row["confirmations"]),
            "requiredConfirmations": int(row["required_confirmations"]),
            "remainingConfirmations": max(
                0, int(row["required_confirmations"]) - int(row["confirmations"])
            ),
            "status": row["status"],
            "observedTipHeight": row.get("observed_tip_height"),
            "lastObservedAt": row["last_observed_at"].isoformat(),
            "maturedAt": row["matured_at"].isoformat() if row.get("matured_at") else None,
            "orphanedAt": (
                row["orphaned_at"].isoformat() if row.get("orphaned_at") else None
            ),
        }
