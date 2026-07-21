from __future__ import annotations

from typing import Any
from uuid import UUID

from seymour_pool_engine.repositories.wallet_repository import WalletRepository

NETWORKS = {"mainnet", "testnet", "regtest"}
PURPOSES = {"developer", "operator", "pool", "payout", "reserve", "cold-storage"}
STATUSES = {"active", "standby", "retired"}


class WalletService:
    def __init__(self, repository: WalletRepository | None = None) -> None:
        self.repository = repository or WalletRepository()

    def create(self, **values: Any) -> dict[str, Any]:
        normalized = self._normalize(values)
        return self._serialize(self.repository.create_wallet(**normalized))

    def list(self, *, coin: str | None = None, purpose: str | None = None) -> list[dict[str, Any]]:
        rows = self.repository.list_wallets(
            coin=coin.upper() if coin else None,
            purpose=purpose.lower() if purpose else None,
        )
        return [self._serialize(row) for row in rows]

    def get(self, wallet_id: UUID) -> dict[str, Any]:
        row = self.repository.get_wallet(wallet_id)
        if row is None:
            raise ValueError("Wallet was not found")
        return self._serialize(row)

    def change_status(self, *, wallet_id: UUID, status: str, actor: str) -> dict[str, Any]:
        normalized = status.lower()
        if normalized not in STATUSES:
            raise ValueError("Invalid wallet status")
        row = self.repository.update_status(wallet_id=wallet_id, status=normalized, actor=actor)
        if row is None:
            raise ValueError("Wallet was not found")
        return self._serialize(row)

    def validate(self, *, wallet_id: UUID, actor: str) -> dict[str, Any]:
        row = self.repository.get_wallet(wallet_id)
        if row is None:
            raise ValueError("Wallet was not found")
        errors = self._address_errors(row["address"], row["network"])
        updated = self.repository.set_validation(
            wallet_id=wallet_id,
            valid=not errors,
            actor=actor,
            details={"errors": errors},
        )
        return {"wallet": self._serialize(updated), "valid": not errors, "errors": errors}

    def events(self, wallet_id: UUID) -> list[dict[str, Any]]:
        return [
            {
                "eventType": row["event_type"],
                "actor": row["actor"],
                "details": row["details"],
                "createdAt": row["created_at"].isoformat(),
            }
            for row in self.repository.wallet_events(wallet_id)
        ]

    def set_worker_payout(
        self, *, worker_id: UUID, coin: str, network: str, address: str, changed_by: str
    ) -> dict[str, Any]:
        self._validate_common(coin=coin, network=network, address=address)
        row = self.repository.upsert_worker_payout(
            worker_id=worker_id,
            coin=coin.upper(),
            network=network.lower(),
            address=address.strip(),
            changed_by=changed_by.strip() or "api",
        )
        return self._serialize_worker_payout(row)

    def worker_payouts(self, worker_id: UUID) -> list[dict[str, Any]]:
        return [
            self._serialize_worker_payout(row) for row in self.repository.worker_payouts(worker_id)
        ]

    def _normalize(self, values: dict[str, Any]) -> dict[str, Any]:
        self._validate_common(
            coin=values["coin"], network=values["network"], address=values["address"]
        )
        purpose = values["purpose"].lower()
        status = values.get("status", "active").lower()
        if purpose not in PURPOSES:
            raise ValueError("Invalid wallet purpose")
        if status not in STATUSES:
            raise ValueError("Invalid wallet status")
        if purpose == "developer" and status != "active":
            raise ValueError("Developer wallet must be active when created")
        values = dict(values)
        values.update(
            wallet_key=values["wallet_key"].strip(),
            coin=values["coin"].upper(),
            network=values["network"].lower(),
            purpose=purpose,
            address=values["address"].strip(),
            status=status,
            created_by=values.get("created_by", "api").strip() or "api",
        )
        if not values["wallet_key"]:
            raise ValueError("walletKey is required")
        return values

    @staticmethod
    def _validate_common(*, coin: str, network: str, address: str) -> None:
        if not coin.strip():
            raise ValueError("coin is required")
        if network.lower() not in NETWORKS:
            raise ValueError("Invalid wallet network")
        errors = WalletService._address_errors(address, network)
        if errors:
            raise ValueError("; ".join(errors))

    @staticmethod
    def _address_errors(address: str, network: str) -> list[str]:
        value = address.strip()
        errors: list[str] = []
        if len(value) < 14 or len(value) > 128:
            errors.append("Wallet address length is invalid")
        if any(character.isspace() for character in value):
            errors.append("Wallet address cannot contain whitespace")
        if network == "mainnet" and value.lower().startswith(("tb1", "bchtest:")):
            errors.append("Testnet address cannot be used on mainnet")
        return errors

    @staticmethod
    def _serialize(row: dict[str, Any] | None) -> dict[str, Any]:
        if row is None:
            raise ValueError("Wallet was not found")
        return {
            "walletId": str(row["wallet_id"]),
            "walletKey": row["wallet_key"],
            "poolId": row.get("pool_id"),
            "coin": row["coin"],
            "network": row["network"],
            "purpose": row["purpose"],
            "address": row["address"],
            "status": row["status"],
            "validationStatus": row["validation_status"],
            "validatedAt": row["validated_at"].isoformat() if row.get("validated_at") else None,
            "descriptorReference": row.get("descriptor_reference"),
            "secretReference": row.get("secret_reference"),
            "createdAt": row["created_at"].isoformat() if row.get("created_at") else None,
            "updatedAt": row["updated_at"].isoformat() if row.get("updated_at") else None,
        }

    @staticmethod
    def _serialize_worker_payout(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "workerPayoutAddressId": str(row["worker_payout_address_id"]),
            "workerId": str(row["worker_id"]),
            "coin": row["coin"],
            "network": row["network"],
            "address": row["address"],
            "status": row["status"],
            "validationStatus": row["validation_status"],
            "validatedAt": row["validated_at"].isoformat() if row.get("validated_at") else None,
        }
