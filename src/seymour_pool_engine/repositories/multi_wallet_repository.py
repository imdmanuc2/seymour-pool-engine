from decimal import Decimal
from typing import Any
from uuid import uuid4

from psycopg.types.json import Jsonb

from seymour_pool_engine.database import engine_connection


class MultiWalletRepository:
    def list_coins(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        clause = " WHERE enabled" if enabled_only else ""
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seymour_engine.coin_registry" + clause + " ORDER BY coin_code"
            )
            return [dict(row) for row in cursor.fetchall()]

    def list_networks(self, coin: str | None = None) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            if coin:
                cursor.execute(
                    "SELECT * FROM seymour_engine.coin_networks "
                    "WHERE coin_code=%s ORDER BY network",
                    (coin,),
                )
            else:
                cursor.execute(
                    "SELECT * FROM seymour_engine.coin_networks ORDER BY coin_code, network"
                )
            return [dict(row) for row in cursor.fetchall()]

    def upsert_assignment(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.wallet_assignments (
                    wallet_assignment_id, wallet_id, assignment_scope, scope_key,
                    purpose, priority, enabled, created_by, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (wallet_id, assignment_scope, scope_key, purpose) DO UPDATE SET
                    priority=EXCLUDED.priority, enabled=EXCLUDED.enabled,
                    metadata=EXCLUDED.metadata, updated_at=NOW()
                RETURNING *
            """,
                (
                    uuid4(),
                    values["wallet_id"],
                    values["assignment_scope"],
                    values["scope_key"],
                    values["purpose"],
                    values["priority"],
                    values["enabled"],
                    values["created_by"],
                    Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def upsert_policy(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.wallet_selection_policies (
                    wallet_selection_policy_id, coin, network, assignment_scope, scope_key,
                    purpose, strategy, allow_failover, minimum_health_status, enabled, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (coin, network, assignment_scope, scope_key, purpose) DO UPDATE SET
                    strategy=EXCLUDED.strategy, allow_failover=EXCLUDED.allow_failover,
                    minimum_health_status=EXCLUDED.minimum_health_status,
                    enabled=EXCLUDED.enabled, metadata=EXCLUDED.metadata, updated_at=NOW()
                RETURNING *
            """,
                (
                    uuid4(),
                    values["coin"],
                    values["network"],
                    values["assignment_scope"],
                    values["scope_key"],
                    values["purpose"],
                    values["strategy"],
                    values["allow_failover"],
                    values["minimum_health_status"],
                    values["enabled"],
                    Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def set_reserve(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.wallet_reserves (
                    wallet_id, minimum_balance, target_balance, maximum_single_payout,
                    action_below_minimum, updated_by
                ) VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (wallet_id) DO UPDATE SET
                    minimum_balance=EXCLUDED.minimum_balance,
                    target_balance=EXCLUDED.target_balance,
                    maximum_single_payout=EXCLUDED.maximum_single_payout,
                    action_below_minimum=EXCLUDED.action_below_minimum,
                    updated_by=EXCLUDED.updated_by, updated_at=NOW()
                RETURNING *
            """,
                (
                    values["wallet_id"],
                    values["minimum_balance"],
                    values.get("target_balance"),
                    values.get("maximum_single_payout"),
                    values["action_below_minimum"],
                    values["updated_by"],
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def record_balance(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.wallet_balance_snapshots (
                    wallet_balance_snapshot_id, wallet_id, confirmed_balance,
                    unconfirmed_balance, locked_balance, available_balance,
                    block_height, observed_at, source, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *
            """,
                (
                    uuid4(),
                    values["wallet_id"],
                    values["confirmed_balance"],
                    values.get("unconfirmed_balance", Decimal("0")),
                    values.get("locked_balance", Decimal("0")),
                    values["available_balance"],
                    values.get("block_height"),
                    values["observed_at"],
                    values["source"],
                    Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def set_health(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.wallet_health (
                    wallet_id, health_status, rpc_reachable, node_synced, wallet_unlocked,
                    spendable, address_valid, checked_at, details
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (wallet_id) DO UPDATE SET
                    health_status=EXCLUDED.health_status, rpc_reachable=EXCLUDED.rpc_reachable,
                    node_synced=EXCLUDED.node_synced, wallet_unlocked=EXCLUDED.wallet_unlocked,
                    spendable=EXCLUDED.spendable, address_valid=EXCLUDED.address_valid,
                    checked_at=EXCLUDED.checked_at, details=EXCLUDED.details
                RETURNING *
            """,
                (
                    values["wallet_id"],
                    values["health_status"],
                    values["rpc_reachable"],
                    values["node_synced"],
                    values.get("wallet_unlocked"),
                    values["spendable"],
                    values.get("address_valid"),
                    values["checked_at"],
                    Jsonb(values.get("details", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def candidates(
        self, *, coin: str, network: str, assignment_scope: str, scope_key: str, purpose: str
    ) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT w.*, a.priority AS assignment_priority, h.health_status, h.spendable,
                       b.available_balance, r.minimum_balance, r.maximum_single_payout,
                       r.action_below_minimum
                FROM seymour_engine.wallet_assignments a
                JOIN seymour_engine.wallets w ON w.wallet_id=a.wallet_id
                LEFT JOIN seymour_engine.wallet_health h ON h.wallet_id=w.wallet_id
                LEFT JOIN LATERAL (
                    SELECT available_balance FROM seymour_engine.wallet_balance_snapshots
                    WHERE wallet_id=w.wallet_id ORDER BY observed_at DESC LIMIT 1
                ) b ON TRUE
                LEFT JOIN seymour_engine.wallet_reserves r ON r.wallet_id=w.wallet_id
                WHERE w.coin=%s AND w.network=%s AND w.status IN ('active','standby')
                  AND w.spend_enabled AND a.enabled AND a.assignment_scope=%s
                  AND a.scope_key IN (%s, '*') AND a.purpose=%s
                ORDER BY CASE WHEN a.scope_key=%s THEN 0 ELSE 1 END,
                         a.priority, w.priority, w.created_at
            """,
                (coin, network, assignment_scope, scope_key, purpose, scope_key),
            )
            return [dict(row) for row in cursor.fetchall()]

    def record_reconciliation(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.wallet_reconciliation_events (
                    wallet_reconciliation_event_id, wallet_id, ledger_balance,
                    blockchain_balance, difference, status, actor, details
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *
            """,
                (
                    uuid4(),
                    values["wallet_id"],
                    values["ledger_balance"],
                    values["blockchain_balance"],
                    values["difference"],
                    values["status"],
                    values["actor"],
                    Jsonb(values.get("details", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row
