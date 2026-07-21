from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from seymour_pool_engine.database import engine_connection


class CoinbaseMaturityRepository:
    def policy(self, *, coin: str, network: str) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM seymour_engine.coinbase_maturity_policies
                WHERE coin=%s AND network=%s AND enabled=TRUE
                """,
                (coin, network),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def policies(self) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM seymour_engine.coinbase_maturity_policies
                ORDER BY coin, network
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def upsert_policy(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.coinbase_maturity_policies (
                    policy_id, coin, network, required_confirmations,
                    enabled, created_by, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (coin, network) DO UPDATE SET
                    required_confirmations=EXCLUDED.required_confirmations,
                    enabled=EXCLUDED.enabled,
                    updated_at=NOW(),
                    metadata=EXCLUDED.metadata
                RETURNING *
                """,
                (
                    uuid4(), values["coin"], values["network"],
                    values["required_confirmations"], values["enabled"],
                    values["actor"], Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def observe(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM seymour_engine.coinbase_maturity_records
                WHERE block_id=%s FOR UPDATE
                """,
                (values["block_id"],),
            )
            existing = cursor.fetchone()
            previous_status = existing["status"] if existing else None
            record_id = existing["maturity_record_id"] if existing else uuid4()
            cursor.execute(
                """
                INSERT INTO seymour_engine.coinbase_maturity_records (
                    maturity_record_id, block_id, pool_id, coin, network,
                    block_height, block_hash, confirmations,
                    required_confirmations, status, observed_tip_height,
                    matured_at, orphaned_at, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                          CASE WHEN %s='mature' THEN NOW() END,
                          CASE WHEN %s='orphaned' THEN NOW() END,%s)
                ON CONFLICT (block_id) DO UPDATE SET
                    block_hash=EXCLUDED.block_hash,
                    confirmations=EXCLUDED.confirmations,
                    required_confirmations=EXCLUDED.required_confirmations,
                    status=EXCLUDED.status,
                    observed_tip_height=EXCLUDED.observed_tip_height,
                    last_observed_at=NOW(),
                    matured_at=CASE
                        WHEN EXCLUDED.status='mature'
                        THEN COALESCE(coinbase_maturity_records.matured_at, NOW())
                        ELSE coinbase_maturity_records.matured_at END,
                    orphaned_at=CASE
                        WHEN EXCLUDED.status='orphaned' THEN NOW()
                        ELSE coinbase_maturity_records.orphaned_at END,
                    metadata=EXCLUDED.metadata
                RETURNING *
                """,
                (
                    record_id, values["block_id"], values["pool_id"],
                    values["coin"], values["network"], values["block_height"],
                    values.get("block_hash"), values["confirmations"],
                    values["required_confirmations"], values["status"],
                    values.get("observed_tip_height"), values["status"],
                    values["status"], Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            self._reconcile_accounting(cursor, row, previous_status)
            event_type = self._event_type(previous_status, row["status"])
            self._event(
                cursor, row["maturity_record_id"], event_type,
                previous_status, row["status"], row["confirmations"],
                values["actor"], values.get("metadata", {}),
            )
            connection.commit()
            return row

    def records(
        self, *, pool_id: str | None, status: str | None, limit: int
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if pool_id:
            clauses.append("pool_id=%s")
            params.append(pool_id)
        if status:
            clauses.append("status=%s")
            params.append(status)
        sql = "SELECT * FROM seymour_engine.coinbase_maturity_records"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY last_observed_at DESC LIMIT %s"
        params.append(limit)
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def summary(self, *, pool_id: str | None) -> dict[str, Any]:
        clause = "WHERE pool_id=%s" if pool_id else ""
        params = (pool_id,) if pool_id else ()
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*) AS total_records,
                       COUNT(*) FILTER (WHERE status='immature') AS immature_records,
                       COUNT(*) FILTER (WHERE status='mature') AS mature_records,
                       COUNT(*) FILTER (WHERE status='orphaned') AS orphaned_records,
                       COALESCE(SUM(confirmations) FILTER
                           (WHERE status='immature'), 0) AS immature_confirmations
                FROM seymour_engine.coinbase_maturity_records
                {clause}
                """,
                params,
            )
            return dict(cursor.fetchone())

    @staticmethod
    def _reconcile_accounting(
        cursor: Any, row: dict[str, Any], previous_status: str | None
    ) -> None:
        block_status = "confirmed" if row["status"] == "mature" else row["status"]
        cursor.execute(
            """
            UPDATE seymour_engine.blocks
            SET status=%s, confirmations=%s,
                confirmed_at=CASE WHEN %s='confirmed'
                    THEN COALESCE(confirmed_at, NOW()) ELSE confirmed_at END,
                orphaned_at=CASE WHEN %s='orphaned' THEN NOW() ELSE orphaned_at END,
                last_checked_at=NOW(), updated_at=NOW()
            WHERE block_id=%s
            """,
            (
                block_status, row["confirmations"], block_status,
                block_status, row["block_id"],
            ),
        )
        if row["status"] == "mature" and previous_status != "mature":
            cursor.execute(
                """
                UPDATE seymour_engine.reward_periods
                SET status='confirmed', confirmed_at=COALESCE(confirmed_at, NOW())
                WHERE block_id=%s AND status='immature'
                """,
                (row["block_id"],),
            )
            cursor.execute(
                """
                UPDATE seymour_engine.worker_reward_entries e
                SET status='confirmed', confirmed_at=COALESCE(confirmed_at, NOW())
                FROM seymour_engine.reward_periods p
                WHERE e.reward_period_id=p.reward_period_id
                  AND p.block_id=%s AND e.status='immature'
                """,
                (row["block_id"],),
            )
            CoinbaseMaturityRepository._post_maturity_ledger(cursor, row["block_id"])
        elif row["status"] == "orphaned" and previous_status != "orphaned":
            CoinbaseMaturityRepository._reverse_orphaned_reward(
                cursor, row["block_id"], previous_status
            )

    @staticmethod
    def _post_maturity_ledger(cursor: Any, block_id: UUID) -> None:
        for entry_type, sign, suffix in (
            ("immature_debit", -1, "maturity-immature-debit"),
            ("confirmed_credit", 1, "maturity-confirmed-credit"),
        ):
            cursor.execute(
                """
                INSERT INTO seymour_engine.balance_ledger (
                    ledger_entry_id, reward_entry_id, pool_id, miner, worker,
                    entry_type, amount, reference_type, reference_id,
                    idempotency_key, metadata
                )
                SELECT gen_random_uuid(), e.reward_entry_id, e.pool_id,
                       e.miner, e.worker, %s, e.reward_amount * %s,
                       'coinbase_maturity', p.block_id,
                       p.block_id::TEXT || ':' || e.reward_entry_id::TEXT || ':' || %s,
                       jsonb_build_object('blockId', p.block_id)
                FROM seymour_engine.worker_reward_entries e
                JOIN seymour_engine.reward_periods p
                  ON p.reward_period_id=e.reward_period_id
                WHERE p.block_id=%s
                ON CONFLICT (idempotency_key) DO NOTHING
                """,
                (entry_type, sign, suffix, block_id),
            )

    @staticmethod
    def _reverse_orphaned_reward(
        cursor: Any, block_id: UUID, previous_status: str | None
    ) -> None:
        cursor.execute(
            """
            UPDATE seymour_engine.reward_periods
            SET status='reversed' WHERE block_id=%s AND status<>'reversed'
            """,
            (block_id,),
        )
        cursor.execute(
            """
            UPDATE seymour_engine.worker_reward_entries e
            SET status='reversed'
            FROM seymour_engine.reward_periods p
            WHERE e.reward_period_id=p.reward_period_id
              AND p.block_id=%s AND e.status<>'reversed'
            """,
            (block_id,),
        )
        cursor.execute(
            """
            INSERT INTO seymour_engine.balance_ledger (
                ledger_entry_id, reward_entry_id, pool_id, miner, worker,
                entry_type, amount, reference_type, reference_id,
                idempotency_key, metadata
            )
            SELECT gen_random_uuid(), e.reward_entry_id, e.pool_id,
                   e.miner, e.worker,
                   CASE WHEN %s='mature' THEN 'confirmed_debit'
                        ELSE 'immature_debit' END,
                   -e.reward_amount, 'coinbase_reorg', p.block_id,
                   p.block_id::TEXT || ':' || e.reward_entry_id::TEXT || ':orphan-reversal',
                   jsonb_build_object('blockId', p.block_id)
            FROM seymour_engine.worker_reward_entries e
            JOIN seymour_engine.reward_periods p
              ON p.reward_period_id=e.reward_period_id
            WHERE p.block_id=%s
            ON CONFLICT (idempotency_key) DO NOTHING
            """,
            (previous_status or "immature", block_id),
        )

    @staticmethod
    def _event_type(previous_status: str | None, new_status: str) -> str:
        if new_status == "mature" and previous_status != "mature":
            return "matured"
        if new_status == "orphaned" and previous_status != "orphaned":
            return "orphaned"
        if previous_status is None:
            return "observed"
        return "confirmation_updated"

    @staticmethod
    def _event(
        cursor: Any, record_id: UUID, event_type: str,
        previous_status: str | None, new_status: str, confirmations: int,
        actor: str, details: dict[str, Any],
    ) -> None:
        cursor.execute(
            """
            INSERT INTO seymour_engine.coinbase_maturity_events (
                maturity_event_id, maturity_record_id, event_type,
                previous_status, new_status, confirmations, actor, details
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                uuid4(), record_id, event_type, previous_status, new_status,
                confirmations, actor, Jsonb(details),
            ),
        )
