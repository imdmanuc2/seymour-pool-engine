import hashlib
import json
from decimal import ROUND_DOWN, Decimal
from typing import Any
from uuid import UUID

from seymour_pool_engine.repositories.economics_repository import EconomicsRepository

MINIMUM_DEVELOPER_FEE_PERCENT = Decimal("0.75")
COIN_QUANTUM = Decimal("0.000000000001")
SUPPORTED_POLICIES = {"solo", "prop", "pplns"}


class EconomicsService:
    def __init__(self, repository: EconomicsRepository | None = None) -> None:
        self.repository = repository or EconomicsRepository()

    def configure_fee_profile(
        self, *, pool_id: str, coin: str, developer_fee_percent: Decimal,
        developer_destination: str, operator_fee_percent: Decimal = Decimal("0"),
        operator_destination: str | None = None,
    ) -> dict[str, Any]:
        self._validate_fees(developer_fee_percent, operator_fee_percent)
        if not pool_id.strip() or not coin.strip() or not developer_destination.strip():
            raise ValueError("Pool, coin, and developer destination are required")
        if operator_fee_percent > 0 and not operator_destination:
            raise ValueError("Operator destination is required when operator fee is greater than zero")
        row = self.repository.upsert_fee_profile(
            pool_id=pool_id.strip(), coin=coin.strip().upper(),
            developer_fee_percent=developer_fee_percent,
            developer_destination=developer_destination.strip(),
            operator_fee_percent=operator_fee_percent,
            operator_destination=operator_destination.strip() if operator_destination else None,
        )
        return self._serialize_profile(row)

    def calculate(
        self, *, block_id: UUID, pool_id: str, coin: str, policy: str,
        gross_reward: Decimal, worker_weights: list[dict[str, Any]],
    ) -> dict[str, Any]:
        normalized_policy = policy.lower()
        if normalized_policy not in SUPPORTED_POLICIES:
            raise ValueError("Policy must be solo, prop, or pplns")
        if gross_reward <= 0:
            raise ValueError("Gross reward must be greater than zero")
        profile = self.repository.get_fee_profile(pool_id=pool_id, coin=coin.upper())
        if profile is None:
            raise ValueError("A fee profile is required before reward calculation")
        developer_percent = Decimal(str(profile["developer_fee_percent"]))
        operator_percent = Decimal(str(profile["operator_fee_percent"]))
        self._validate_fees(developer_percent, operator_percent)
        allocations = self._allocate(
            gross_reward=gross_reward, developer_percent=developer_percent,
            operator_percent=operator_percent, developer_destination=profile["developer_destination"],
            operator_destination=profile.get("operator_destination"), worker_weights=worker_weights,
            policy=normalized_policy,
        )
        previous_hash = self.repository.latest_integrity_hash(pool_id=pool_id, coin=coin.upper())
        integrity_hash = self._integrity_hash(
            block_id=block_id, pool_id=pool_id, coin=coin.upper(), policy=normalized_policy,
            gross_reward=gross_reward, allocations=allocations, previous_hash=previous_hash,
        )
        result = self.repository.create_calculation(
            block_id=block_id, fee_profile_id=profile["fee_profile_id"], pool_id=pool_id,
            coin=coin.upper(), policy=normalized_policy, gross_reward=gross_reward,
            developer_fee_percent=developer_percent,
            operator_fee_percent=operator_percent, allocations=allocations,
            integrity_hash=integrity_hash, previous_integrity_hash=previous_hash,
        )
        return {**result, "integrityHash": integrity_hash, "previousIntegrityHash": previous_hash,
                "policy": normalized_policy, "grossReward": float(gross_reward),
                "developerFeePercent": float(developer_percent),
                "operatorFeePercent": float(operator_percent),
                "allocations": [self._serialize_allocation(item) for item in allocations]}

    def summary(self, *, pool_id: str | None = None, coin: str | None = None) -> dict[str, Any]:
        return self.repository.economics_summary(pool_id=pool_id, coin=coin.upper() if coin else None)

    @staticmethod
    def _validate_fees(developer: Decimal, operator: Decimal) -> None:
        if developer < MINIMUM_DEVELOPER_FEE_PERCENT:
            raise ValueError("Developer fee cannot be lower than 0.75 percent")
        if developer > 100 or operator < 0 or operator > 100 or developer + operator >= 100:
            raise ValueError("Developer and operator fees must total less than 100 percent")

    @staticmethod
    def _allocate(*, gross_reward: Decimal, developer_percent: Decimal,
                  operator_percent: Decimal, developer_destination: str,
                  operator_destination: str | None, worker_weights: list[dict[str, Any]],
                  policy: str) -> list[dict[str, Any]]:
        if not worker_weights:
            raise ValueError("At least one worker weight is required")
        cleaned = []
        for item in worker_weights:
            key = str(item.get("recipientKey", "")).strip()
            weight = Decimal(str(item.get("weight", 0)))
            if not key or weight <= 0:
                raise ValueError("Each worker requires a recipientKey and positive weight")
            cleaned.append({"recipient_key": key, "weight": weight})
        if policy == "solo" and len(cleaned) != 1:
            raise ValueError("SOLO reward calculation requires exactly one recipient")
        total_weight = sum((x["weight"] for x in cleaned), Decimal("0"))
        developer_amount = (gross_reward * developer_percent / 100).quantize(COIN_QUANTUM, rounding=ROUND_DOWN)
        operator_amount = (gross_reward * operator_percent / 100).quantize(COIN_QUANTUM, rounding=ROUND_DOWN)
        worker_total = gross_reward - developer_amount - operator_amount
        rows = [{"allocation_type": "developer", "recipient_key": developer_destination,
                 "amount": developer_amount, "weight": None}]
        if operator_amount > 0:
            rows.append({"allocation_type": "operator", "recipient_key": operator_destination,
                         "amount": operator_amount, "weight": None})
        allocated = Decimal("0")
        for index, worker in enumerate(cleaned):
            amount = worker_total - allocated if index == len(cleaned) - 1 else (
                worker_total * worker["weight"] / total_weight
            ).quantize(COIN_QUANTUM, rounding=ROUND_DOWN)
            allocated += amount
            rows.append({"allocation_type": "worker", "recipient_key": worker["recipient_key"],
                         "amount": amount, "weight": worker["weight"]})
        return rows

    @staticmethod
    def _integrity_hash(**values: Any) -> str:
        normalized = dict(values)
        normalized["block_id"] = str(normalized["block_id"])
        normalized["gross_reward"] = str(normalized["gross_reward"])
        normalized["allocations"] = [
            {k: str(v) if isinstance(v, Decimal) else v for k, v in item.items()}
            for item in normalized["allocations"]
        ]
        return hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()

    @staticmethod
    def _serialize_profile(row: dict[str, Any]) -> dict[str, Any]:
        return {"feeProfileId": str(row["fee_profile_id"]), "poolId": row["pool_id"],
                "coin": row["coin"], "minimumDeveloperFeePercent": 0.75,
                "developerFeePercent": float(row["developer_fee_percent"]),
                "operatorFeePercent": float(row["operator_fee_percent"]),
                "developerDestination": row["developer_destination"],
                "operatorDestination": row.get("operator_destination")}

    @staticmethod
    def _serialize_allocation(item: dict[str, Any]) -> dict[str, Any]:
        return {"type": item["allocation_type"], "recipientKey": item["recipient_key"],
                "amount": float(item["amount"]),
                "weight": float(item["weight"]) if item["weight"] is not None else None}
