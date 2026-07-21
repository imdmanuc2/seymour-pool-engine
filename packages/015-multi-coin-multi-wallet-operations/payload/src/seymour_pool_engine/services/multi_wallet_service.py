from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from seymour_pool_engine.repositories.multi_wallet_repository import MultiWalletRepository

SCOPES = {"global", "pool", "developer-fee", "pool-fee", "treasury", "exchange"}
PURPOSES = {"payout", "fee-receipt", "reserve", "treasury", "exchange", "backup"}
STRATEGIES = {"priority", "highest-available", "round-robin", "manual"}
HEALTH_RANK = {"healthy": 0, "degraded": 1, "unhealthy": 2, "unknown": 3, None: 3}


class MultiWalletService:
    def __init__(self, repository: MultiWalletRepository | None = None) -> None:
        self.repository = repository or MultiWalletRepository()

    def coins(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        return [
            {
                "coin": r["coin_code"],
                "displayName": r["display_name"],
                "family": r["family"],
                "decimals": r["decimals"],
                "enabled": r["enabled"],
            }
            for r in self.repository.list_coins(enabled_only)
        ]

    def networks(self, coin: str | None = None) -> list[dict[str, Any]]:
        rows = self.repository.list_networks(coin.upper() if coin else None)
        return [
            {
                "coin": r["coin_code"],
                "network": r["network"],
                "rpcChainName": r.get("rpc_chain_name"),
                "confirmationsRequired": r["confirmations_required"],
                "enabled": r["enabled"],
            }
            for r in rows
        ]

    def assign(self, **values: Any) -> dict[str, Any]:
        self._scope(values["assignment_scope"], values["purpose"])
        values = dict(
            values,
            scope_key=values.get("scope_key", "*").strip() or "*",
            priority=max(0, values.get("priority", 100)),
            created_by=values.get("created_by", "api").strip() or "api",
        )
        return self._serialize(self.repository.upsert_assignment(**values))

    def policy(self, **values: Any) -> dict[str, Any]:
        self._scope(values["assignment_scope"], values["purpose"])
        strategy = values.get("strategy", "priority")
        if strategy not in STRATEGIES:
            raise ValueError("Invalid wallet selection strategy")
        values = dict(
            values,
            coin=values["coin"].upper(),
            network=values["network"].lower(),
            scope_key=values.get("scope_key", "*").strip() or "*",
            strategy=strategy,
        )
        return self._serialize(self.repository.upsert_policy(**values))

    def reserve(self, **values: Any) -> dict[str, Any]:
        minimum = Decimal(str(values["minimum_balance"]))
        target = (
            Decimal(str(values["target_balance"]))
            if values.get("target_balance") is not None
            else None
        )
        maximum = (
            Decimal(str(values["maximum_single_payout"]))
            if values.get("maximum_single_payout") is not None
            else None
        )
        if minimum < 0 or (target is not None and target < minimum):
            raise ValueError("Invalid reserve amounts")
        if maximum is not None and maximum <= 0:
            raise ValueError("maximumSinglePayout must be positive")
        values = dict(
            values, minimum_balance=minimum, target_balance=target, maximum_single_payout=maximum
        )
        return self._serialize(self.repository.set_reserve(**values))

    def observe_balance(self, **values: Any) -> dict[str, Any]:
        confirmed = Decimal(str(values["confirmed_balance"]))
        unconfirmed = Decimal(str(values.get("unconfirmed_balance", 0)))
        locked = Decimal(str(values.get("locked_balance", 0)))
        available = values.get("available_balance")
        available = Decimal(str(available)) if available is not None else confirmed - locked
        values = dict(
            values,
            confirmed_balance=confirmed,
            unconfirmed_balance=unconfirmed,
            locked_balance=locked,
            available_balance=available,
            observed_at=values.get("observed_at") or datetime.now(UTC),
        )
        return self._serialize(self.repository.record_balance(**values))

    def health(self, **values: Any) -> dict[str, Any]:
        status = values.get("health_status") or self._derive_health(values)
        values = dict(
            values, health_status=status, checked_at=values.get("checked_at") or datetime.now(UTC)
        )
        return self._serialize(self.repository.set_health(**values))

    def select(self, *, amount: Decimal, **values: Any) -> dict[str, Any]:
        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Selection amount must be positive")
        self._scope(values["assignment_scope"], values["purpose"])
        rows = self.repository.candidates(
            coin=values["coin"].upper(),
            network=values["network"].lower(),
            assignment_scope=values["assignment_scope"],
            scope_key=values.get("scope_key", "*"),
            purpose=values["purpose"],
        )
        rejections = []
        for row in rows:
            available = Decimal(str(row.get("available_balance") or 0))
            minimum = Decimal(str(row.get("minimum_balance") or 0))
            maximum = row.get("maximum_single_payout")
            reasons = []
            if HEALTH_RANK.get(row.get("health_status"), 3) > 1 or not row.get("spendable", False):
                reasons.append("wallet-not-healthy-or-spendable")
            if maximum is not None and amount > Decimal(str(maximum)):
                reasons.append("maximum-single-payout-exceeded")
            if available - amount < minimum:
                reasons.append("reserve-threshold-violation")
            if reasons:
                rejections.append({"walletId": str(row["wallet_id"]), "reasons": reasons})
                continue
            return {
                "selected": self._serialize(row),
                "amount": str(amount),
                "rejections": rejections,
            }
        raise ValueError("No eligible wallet is available for this payment")

    def reconcile(
        self,
        *,
        wallet_id: UUID,
        ledger_balance: Decimal,
        blockchain_balance: Decimal,
        actor: str = "api",
        tolerance: Decimal = Decimal("0.00000001"),
    ) -> dict[str, Any]:
        ledger = Decimal(str(ledger_balance))
        chain = Decimal(str(blockchain_balance))
        difference = chain - ledger
        status = "matched" if abs(difference) <= Decimal(str(tolerance)) else "drift"
        row = self.repository.record_reconciliation(
            wallet_id=wallet_id,
            ledger_balance=ledger,
            blockchain_balance=chain,
            difference=difference,
            status=status,
            actor=actor,
            details={"tolerance": str(tolerance)},
        )
        return self._serialize(row)

    @staticmethod
    def _derive_health(v: dict[str, Any]) -> str:
        if v.get("rpc_reachable") and v.get("node_synced") and v.get("spendable"):
            return "healthy"
        if v.get("rpc_reachable"):
            return "degraded"
        return "unhealthy"

    @staticmethod
    def _scope(scope: str, purpose: str) -> None:
        if scope not in SCOPES:
            raise ValueError("Invalid assignment scope")
        if purpose not in PURPOSES:
            raise ValueError("Invalid assignment purpose")

    @staticmethod
    def _serialize(row: dict[str, Any]) -> dict[str, Any]:
        out = {}
        for key, value in row.items():
            camel = key.split("_")[0] + "".join(x.title() for x in key.split("_")[1:])
            if isinstance(value, (UUID, Decimal)):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            out[camel] = value
        return out
