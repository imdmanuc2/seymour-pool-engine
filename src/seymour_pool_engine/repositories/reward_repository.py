from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from seymour_pool_engine.database import engine_connection


class RewardRepository:
    """Persistence boundary for reward allocation and balance accounting."""

    def accepted_difficulty_by_worker(
        self,
        *,
        pool_id: str,
        start_at: datetime,
        end_at: datetime,
    ) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    worker_id,
                    pool_id,
                    miner,
                    worker,
                    COALESCE(SUM(difficulty), 0)::NUMERIC AS accepted_difficulty
                FROM seymour_engine.shares
                WHERE pool_id = %s
                  AND provider_created_at >= %s
                  AND provider_created_at <= %s
                  AND share_status = 'accepted'
                GROUP BY worker_id, pool_id, miner, worker
                ORDER BY miner, worker
                """,
                (pool_id, start_at, end_at),
            )
            return [dict(row) for row in cursor.fetchall()]

    def create_period(
        self,
        *,
        block_id: UUID,
        pool_id: str,
        gross_reward: Decimal,
        pool_fee: Decimal,
        distributable_reward: Decimal,
        total_accepted_difficulty: Decimal,
        allocations: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        reward_period_id = uuid4()
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.reward_periods (
                    reward_period_id, block_id, pool_id, gross_reward, pool_fee,
                    distributable_reward, total_accepted_difficulty, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (block_id) DO NOTHING
                RETURNING reward_period_id
                """,
                (
                    reward_period_id,
                    block_id,
                    pool_id,
                    gross_reward,
                    pool_fee,
                    distributable_reward,
                    total_accepted_difficulty,
                    Jsonb(metadata or {}),
                ),
            )
            inserted = cursor.fetchone()
            if inserted is None:
                cursor.execute(
                    """
                    SELECT reward_period_id
                    FROM seymour_engine.reward_periods
                    WHERE block_id = %s
                    """,
                    (block_id,),
                )
                existing = cursor.fetchone()
                return {
                    "reward_period_id": existing["reward_period_id"],
                    "created": False,
                    "entries": 0,
                }

            for allocation in allocations:
                reward_entry_id = uuid4()
                cursor.execute(
                    """
                    INSERT INTO seymour_engine.worker_reward_entries (
                        reward_entry_id, reward_period_id, worker_id, pool_id,
                        miner, worker, accepted_difficulty, reward_amount, metadata
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        reward_entry_id,
                        reward_period_id,
                        allocation.get("worker_id"),
                        pool_id,
                        allocation["miner"],
                        allocation.get("worker", ""),
                        allocation["accepted_difficulty"],
                        allocation["reward_amount"],
                        Jsonb(allocation.get("metadata", {})),
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO seymour_engine.balance_ledger (
                        ledger_entry_id, reward_entry_id, pool_id, miner, worker,
                        entry_type, amount, reference_type, reference_id,
                        idempotency_key, metadata
                    ) VALUES (%s, %s, %s, %s, %s, 'immature_credit', %s,
                              'reward_entry', %s, %s, %s)
                    """,
                    (
                        uuid4(),
                        reward_entry_id,
                        pool_id,
                        allocation["miner"],
                        allocation.get("worker", ""),
                        allocation["reward_amount"],
                        reward_entry_id,
                        f"reward:{reward_entry_id}:immature",
                        Jsonb({"rewardPeriodId": str(reward_period_id)}),
                    ),
                )
            connection.commit()
        return {
            "reward_period_id": reward_period_id,
            "created": True,
            "entries": len(allocations),
        }

    def confirm_period(self, reward_period_id: UUID) -> dict[str, int]:
        moved = 0
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT reward_entry_id, pool_id, miner, worker, reward_amount
                FROM seymour_engine.worker_reward_entries
                WHERE reward_period_id = %s AND status = 'immature'
                FOR UPDATE
                """,
                (reward_period_id,),
            )
            entries = [dict(row) for row in cursor.fetchall()]
            for entry in entries:
                reward_entry_id = entry["reward_entry_id"]
                common = (
                    entry["pool_id"],
                    entry["miner"],
                    entry["worker"],
                    entry["reward_amount"],
                    reward_entry_id,
                )
                cursor.execute(
                    """
                    INSERT INTO seymour_engine.balance_ledger (
                        ledger_entry_id, reward_entry_id, pool_id, miner, worker,
                        entry_type, amount, reference_type, reference_id,
                        idempotency_key
                    ) VALUES (%s, %s, %s, %s, %s, 'immature_debit', %s,
                              'reward_entry', %s, %s)
                    ON CONFLICT (idempotency_key) DO NOTHING
                    """,
                    (
                        uuid4(),
                        reward_entry_id,
                        *common,
                        f"reward:{reward_entry_id}:immature-debit",
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO seymour_engine.balance_ledger (
                        ledger_entry_id, reward_entry_id, pool_id, miner, worker,
                        entry_type, amount, reference_type, reference_id,
                        idempotency_key
                    ) VALUES (%s, %s, %s, %s, %s, 'confirmed_credit', %s,
                              'reward_entry', %s, %s)
                    ON CONFLICT (idempotency_key) DO NOTHING
                    """,
                    (
                        uuid4(),
                        reward_entry_id,
                        *common,
                        f"reward:{reward_entry_id}:confirmed",
                    ),
                )
                moved += 1
            cursor.execute(
                """
                UPDATE seymour_engine.worker_reward_entries
                SET status = 'confirmed', confirmed_at = NOW()
                WHERE reward_period_id = %s AND status = 'immature'
                """,
                (reward_period_id,),
            )
            cursor.execute(
                """
                UPDATE seymour_engine.reward_periods
                SET status = 'confirmed', confirmed_at = NOW()
                WHERE reward_period_id = %s AND status = 'immature'
                """,
                (reward_period_id,),
            )
            connection.commit()
        return {"entriesConfirmed": moved}

    def list_periods(self, *, pool_id: str | None, limit: int) -> list[dict[str, Any]]:
        query = "SELECT * FROM seymour_engine.reward_periods WHERE TRUE"
        params: list[Any] = []
        if pool_id is not None:
            query += " AND pool_id = %s"
            params.append(pool_id)
        query += " ORDER BY calculated_at DESC LIMIT %s"
        params.append(limit)
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    def list_balances(self, *, pool_id: str | None, miner: str | None) -> list[dict[str, Any]]:
        query = "SELECT * FROM seymour_engine.worker_balances WHERE TRUE"
        params: list[Any] = []
        if pool_id is not None:
            query += " AND pool_id = %s"
            params.append(pool_id)
        if miner is not None:
            query += " AND miner = %s"
            params.append(miner)
        query += " ORDER BY pool_id, miner, worker"
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
