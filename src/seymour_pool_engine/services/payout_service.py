from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

from seymour_pool_engine.repositories.payout_repository import PayoutRepository


class PayoutService:
    def __init__(self, repository: PayoutRepository | None = None) -> None:
        self.repository = repository or PayoutRepository()

    def eligible(self, *, pool_id: str, minimum_payout: str) -> list[dict[str, Any]]:
        minimum = self._amount(minimum_payout, allow_zero=True)
        rows = self.repository.eligible_balances(pool_id=pool_id, minimum_payout=minimum)
        return [self._eligible(row) for row in rows if row.get("destination_address")]

    def create(self, **values: Any) -> dict[str, Any]:
        items = values.get("items") or []
        if not items:
            raise ValueError("A payout batch requires at least one payout item")
        normalized_items = []
        for item in items:
            amount = self._amount(item["amount"])
            address = item["destination_address"].strip()
            if not address:
                raise ValueError("A payout destination address is required")
            normalized_items.append({**item, "amount": amount, "destination_address": address})
        values["minimum_payout"] = self._amount(
            values.get("minimum_payout", "0"), allow_zero=True
        )
        values["coin"] = values["coin"].upper()
        values["network"] = values["network"].lower()
        values["requested_by"] = values.get("requested_by", "api").strip() or "api"
        values["items"] = normalized_items
        return self._batch(self.repository.create_batch(**values))

    def get(self, payout_batch_id: UUID) -> dict[str, Any]:
        row = self.repository.get_batch(payout_batch_id)
        if row is None:
            raise ValueError("Payout batch was not found")
        result = self._batch(row)
        result["items"] = [self._item(item) for item in self.repository.items(payout_batch_id)]
        return result

    def list(self, *, pool_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return [self._batch(row) for row in self.repository.list_batches(
            pool_id=pool_id, limit=max(1, min(limit, 500))
        )]

    def approve(self, *, payout_batch_id: UUID, actor: str) -> dict[str, Any]:
        return self._transition(payout_batch_id, ("draft",), "approved", actor)

    def start(self, *, payout_batch_id: UUID, actor: str) -> dict[str, Any]:
        return self._transition(payout_batch_id, ("approved",), "processing", actor)

    def complete(
        self, *, payout_batch_id: UUID, actor: str, transaction_id: str
    ) -> dict[str, Any]:
        if not transaction_id.strip():
            raise ValueError("A transaction ID is required")
        return self._transition(
            payout_batch_id, ("processing",), "completed", actor,
            transaction_id=transaction_id.strip(),
        )

    def fail(
        self, *, payout_batch_id: UUID, actor: str, failure_reason: str
    ) -> dict[str, Any]:
        if not failure_reason.strip():
            raise ValueError("A failure reason is required")
        return self._transition(
            payout_batch_id, ("approved", "processing"), "failed", actor,
            failure_reason=failure_reason.strip(),
        )

    def cancel(self, *, payout_batch_id: UUID, actor: str) -> dict[str, Any]:
        return self._transition(payout_batch_id, ("draft", "approved"), "cancelled", actor)

    def events(self, payout_batch_id: UUID) -> list[dict[str, Any]]:
        return [{
            "eventType": row["event_type"], "actor": row["actor"],
            "details": row["details"], "createdAt": row["created_at"].isoformat(),
        } for row in self.repository.events(payout_batch_id)]

    def _transition(
        self, payout_batch_id: UUID, from_statuses: tuple[str, ...],
        to_status: str, actor: str, **values: Any,
    ) -> dict[str, Any]:
        row = self.repository.transition(
            payout_batch_id=payout_batch_id, from_statuses=from_statuses,
            to_status=to_status, actor=actor.strip() or "api", **values,
        )
        if row is None:
            raise ValueError(f"Payout batch cannot transition to {to_status}")
        return self._batch(row)

    @staticmethod
    def _amount(value: Any, *, allow_zero: bool = False) -> Decimal:
        try:
            amount = Decimal(str(value))
        except (InvalidOperation, TypeError) as exc:
            raise ValueError("Invalid payout amount") from exc
        if amount < 0 or (amount == 0 and not allow_zero):
            raise ValueError("Payout amount must be greater than zero")
        return amount

    @staticmethod
    def _eligible(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "workerId": str(row["worker_id"]) if row.get("worker_id") else None,
            "poolId": row["pool_id"], "miner": row["miner"], "worker": row["worker"],
            "amount": str(row["confirmed_balance"]),
            "destinationAddress": row["destination_address"],
        }

    @staticmethod
    def _batch(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "payoutBatchId": str(row["payout_batch_id"]), "batchKey": row["batch_key"],
            "poolId": row["pool_id"], "coin": row["coin"], "network": row["network"],
            "sourceWalletId": str(row["source_wallet_id"]), "status": row["status"],
            "minimumPayout": str(row["minimum_payout"]),
            "totalAmount": str(row["total_amount"]), "itemCount": row["item_count"],
            "transactionId": row.get("transaction_id"),
            "failureReason": row.get("failure_reason"),
            "createdAt": row["created_at"].isoformat() if row.get("created_at") else None,
        }

    @staticmethod
    def _item(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "payoutItemId": str(row["payout_item_id"]),
            "workerId": str(row["worker_id"]) if row.get("worker_id") else None,
            "miner": row["miner"], "worker": row["worker"],
            "destinationAddress": row["destination_address"],
            "amount": str(row["amount"]), "status": row["status"],
            "transactionId": row.get("transaction_id"),
            "failureReason": row.get("failure_reason"),
        }
