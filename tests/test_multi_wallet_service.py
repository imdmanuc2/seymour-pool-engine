from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from seymour_pool_engine.services.multi_wallet_service import MultiWalletService


class Repo:
    def __init__(self):
        self.rows = []

    def list_coins(self, enabled_only=True):
        return [
            {
                "coin_code": "BTC",
                "display_name": "Bitcoin",
                "family": "utxo",
                "decimals": 8,
                "enabled": True,
            }
        ]

    def list_networks(self, coin=None):
        return [
            {
                "coin_code": "BTC",
                "network": "mainnet",
                "rpc_chain_name": "main",
                "confirmations_required": 1,
                "enabled": True,
            }
        ]

    def upsert_assignment(self, **v):
        return {"wallet_assignment_id": uuid4(), **v, "created_at": datetime.now(UTC)}

    def upsert_policy(self, **v):
        return {"wallet_selection_policy_id": uuid4(), **v}

    def set_reserve(self, **v):
        return v

    def record_balance(self, **v):
        return {"wallet_balance_snapshot_id": uuid4(), **v}

    def set_health(self, **v):
        return v

    def candidates(self, **v):
        return self.rows

    def record_reconciliation(self, **v):
        return {"wallet_reconciliation_event_id": uuid4(), **v}


def test_supports_many_wallets_and_selects_first_eligible():
    repo = Repo()
    bad = uuid4()
    good = uuid4()
    repo.rows = [
        {
            "wallet_id": bad,
            "health_status": "healthy",
            "spendable": True,
            "available_balance": Decimal("1"),
            "minimum_balance": Decimal("1"),
            "maximum_single_payout": None,
        },
        {
            "wallet_id": good,
            "health_status": "healthy",
            "spendable": True,
            "available_balance": Decimal("5"),
            "minimum_balance": Decimal("1"),
            "maximum_single_payout": Decimal("2"),
        },
    ]
    result = MultiWalletService(repo).select(
        coin="BTC",
        network="mainnet",
        assignment_scope="pool",
        scope_key="btc-public",
        purpose="payout",
        amount=Decimal("1.5"),
    )
    assert result["selected"]["walletId"] == str(good)
    assert result["rejections"][0]["walletId"] == str(bad)


def test_reserve_protection_blocks_selection():
    repo = Repo()
    repo.rows = [
        {
            "wallet_id": uuid4(),
            "health_status": "healthy",
            "spendable": True,
            "available_balance": Decimal("2"),
            "minimum_balance": Decimal("1.5"),
            "maximum_single_payout": None,
        }
    ]
    with pytest.raises(ValueError, match="No eligible wallet"):
        MultiWalletService(repo).select(
            coin="BTC",
            network="mainnet",
            assignment_scope="pool",
            scope_key="x",
            purpose="payout",
            amount=Decimal("1"),
        )


def test_reconciliation_detects_drift():
    result = MultiWalletService(Repo()).reconcile(
        wallet_id=uuid4(), ledger_balance=Decimal("1"), blockchain_balance=Decimal("1.1")
    )
    assert result["status"] == "drift"
    assert result["difference"] == "0.1"
