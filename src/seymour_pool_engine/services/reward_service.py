from datetime import datetime
from decimal import ROUND_DOWN, Decimal
from typing import Any
from uuid import UUID

from seymour_pool_engine.repositories.reward_repository import RewardRepository

MAX_REWARD_LIMIT = 1000
COIN_QUANTUM = Decimal("0.000000000001")


class RewardService:
    def __init__(self, repository: RewardRepository | None = None) -> None:
        self.repository = repository or RewardRepository()

    def calculate(
        self,
        *,
        block_id: UUID,
        pool_id: str,
        gross_reward: Decimal,
        fee_percent: Decimal,
        start_at: datetime,
        end_at: datetime,
    ) -> dict[str, Any]:
        if gross_reward <= 0:
            raise ValueError("Gross reward must be greater than zero")
        if fee_percent < 0 or fee_percent > 100:
            raise ValueError("Fee percent must be between 0 and 100")
        if start_at >= end_at:
            raise ValueError("Reward period start must be before end")

        workers = self.repository.accepted_difficulty_by_worker(
            pool_id=pool_id,
            start_at=start_at,
            end_at=end_at,
        )
        total_difficulty = sum(
            (Decimal(str(row["accepted_difficulty"])) for row in workers),
            Decimal("0"),
        )
        if total_difficulty <= 0:
            raise ValueError("No accepted share difficulty exists for the reward period")

        pool_fee = (gross_reward * fee_percent / Decimal("100")).quantize(
            COIN_QUANTUM,
            rounding=ROUND_DOWN,
        )
        distributable = gross_reward - pool_fee
        allocations: list[dict[str, Any]] = []
        allocated = Decimal("0")
        for index, worker in enumerate(workers):
            difficulty = Decimal(str(worker["accepted_difficulty"]))
            if index == len(workers) - 1:
                amount = distributable - allocated
            else:
                amount = (distributable * difficulty / total_difficulty).quantize(
                    COIN_QUANTUM,
                    rounding=ROUND_DOWN,
                )
                allocated += amount
            allocations.append(
                {
                    "worker_id": worker.get("worker_id"),
                    "miner": worker["miner"],
                    "worker": worker.get("worker", ""),
                    "accepted_difficulty": difficulty,
                    "reward_amount": amount,
                }
            )

        result = self.repository.create_period(
            block_id=block_id,
            pool_id=pool_id,
            gross_reward=gross_reward,
            pool_fee=pool_fee,
            distributable_reward=distributable,
            total_accepted_difficulty=total_difficulty,
            allocations=allocations,
            metadata={
                "startAt": start_at.isoformat(),
                "endAt": end_at.isoformat(),
                "feePercent": str(fee_percent),
            },
        )
        return {
            "blockId": str(block_id),
            "poolId": pool_id,
            "grossReward": float(gross_reward),
            "poolFee": float(pool_fee),
            "distributableReward": float(distributable),
            "totalAcceptedDifficulty": float(total_difficulty),
            "allocationCount": len(allocations),
            "allocations": [self._serialize_allocation(item) for item in allocations],
            "rewardPeriodId": str(result["reward_period_id"]),
            "created": result["created"],
        }

    def confirm(self, reward_period_id: UUID) -> dict[str, Any]:
        return {
            "rewardPeriodId": str(reward_period_id),
            **self.repository.confirm_period(reward_period_id),
        }

    def periods(self, *, pool_id: str | None = None, limit: int = 100) -> dict[str, Any]:
        normalized_limit = self._normalize_limit(limit)
        rows = self.repository.list_periods(pool_id=pool_id, limit=normalized_limit)
        return {
            "count": len(rows),
            "poolId": pool_id,
            "periods": [self._serialize_period(row) for row in rows],
        }

    def balances(
        self,
        *,
        pool_id: str | None = None,
        miner: str | None = None,
    ) -> dict[str, Any]:
        rows = self.repository.list_balances(pool_id=pool_id, miner=miner)
        return {
            "count": len(rows),
            "poolId": pool_id,
            "miner": miner,
            "balances": [self._serialize_balance(row) for row in rows],
        }

    @staticmethod
    def _normalize_limit(limit: int) -> int:
        if limit < 1 or limit > MAX_REWARD_LIMIT:
            raise ValueError(f"Reward limit must be between 1 and {MAX_REWARD_LIMIT}")
        return limit

    @staticmethod
    def _serialize_allocation(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "workerId": str(item["worker_id"]) if item.get("worker_id") else None,
            "miner": item["miner"],
            "worker": item.get("worker", ""),
            "acceptedDifficulty": float(item["accepted_difficulty"]),
            "rewardAmount": float(item["reward_amount"]),
        }

    @staticmethod
    def _serialize_period(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "rewardPeriodId": str(row["reward_period_id"]),
            "blockId": str(row["block_id"]),
            "poolId": row["pool_id"],
            "status": row["status"],
            "grossReward": float(row["gross_reward"]),
            "poolFee": float(row["pool_fee"]),
            "distributableReward": float(row["distributable_reward"]),
            "totalAcceptedDifficulty": float(row["total_accepted_difficulty"]),
            "calculatedAt": row["calculated_at"].isoformat(),
            "confirmedAt": row["confirmed_at"].isoformat() if row.get("confirmed_at") else None,
        }

    @staticmethod
    def _serialize_balance(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "poolId": row["pool_id"],
            "miner": row["miner"],
            "worker": row["worker"],
            "immatureBalance": float(row["immature_balance"]),
            "confirmedBalance": float(row["confirmed_balance"]),
            "updatedAt": row["updated_at"].isoformat() if row.get("updated_at") else None,
        }


def calculate_rewards(**kwargs: Any) -> dict[str, Any]:
    return RewardService().calculate(**kwargs)


def confirm_rewards(reward_period_id: UUID) -> dict[str, Any]:
    return RewardService().confirm(reward_period_id)


def get_reward_periods(*, pool_id: str | None = None, limit: int = 100) -> dict[str, Any]:
    return RewardService().periods(pool_id=pool_id, limit=limit)


def get_balances(*, pool_id: str | None = None, miner: str | None = None) -> dict[str, Any]:
    return RewardService().balances(pool_id=pool_id, miner=miner)
