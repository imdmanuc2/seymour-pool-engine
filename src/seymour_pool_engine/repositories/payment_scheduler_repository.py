from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from psycopg.errors import UniqueViolation
from psycopg.types.json import Jsonb

from seymour_pool_engine.database import engine_connection


class PaymentSchedulerRepository:
    def upsert_profile(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.payment_scheduler_profiles (
                    scheduler_profile_id, pool_id, coin, network, source_wallet_id,
                    enabled, schedule_type, schedule_hour, schedule_weekday,
                    schedule_monthday, minimum_payout, absolute_minimum,
                    maximum_payout, maximum_behavior, retry_limit,
                    retry_backoff_seconds, next_run_at, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (pool_id, coin, network) DO UPDATE SET
                    source_wallet_id=EXCLUDED.source_wallet_id,
                    enabled=EXCLUDED.enabled,
                    schedule_type=EXCLUDED.schedule_type,
                    schedule_hour=EXCLUDED.schedule_hour,
                    schedule_weekday=EXCLUDED.schedule_weekday,
                    schedule_monthday=EXCLUDED.schedule_monthday,
                    minimum_payout=EXCLUDED.minimum_payout,
                    absolute_minimum=EXCLUDED.absolute_minimum,
                    maximum_payout=EXCLUDED.maximum_payout,
                    maximum_behavior=EXCLUDED.maximum_behavior,
                    retry_limit=EXCLUDED.retry_limit,
                    retry_backoff_seconds=EXCLUDED.retry_backoff_seconds,
                    next_run_at=EXCLUDED.next_run_at,
                    metadata=EXCLUDED.metadata,
                    updated_at=NOW()
                RETURNING *
                """,
                (
                    uuid4(), values["pool_id"], values["coin"], values["network"],
                    values["source_wallet_id"], values["enabled"],
                    values["schedule_type"], values.get("schedule_hour"),
                    values.get("schedule_weekday"), values.get("schedule_monthday"),
                    values["minimum_payout"], values["absolute_minimum"],
                    values.get("maximum_payout"), values["maximum_behavior"],
                    values["retry_limit"], values["retry_backoff_seconds"],
                    values.get("next_run_at"), Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def list_profiles(self, *, pool_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM seymour_engine.payment_scheduler_profiles"
        params: list[Any] = []
        if pool_id:
            query += " WHERE pool_id=%s"
            params.append(pool_id)
        query += " ORDER BY pool_id, coin, network"
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_profile(self, scheduler_profile_id: UUID) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM seymour_engine.payment_scheduler_profiles
                WHERE scheduler_profile_id=%s
                """,
                (scheduler_profile_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def due_profiles(self) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM seymour_engine.payment_scheduler_profiles
                WHERE enabled=TRUE AND schedule_type <> 'manual'
                  AND (next_run_at IS NULL OR next_run_at <= NOW())
                ORDER BY next_run_at NULLS FIRST
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def upsert_worker_policy(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.worker_payment_policies (
                    worker_payment_policy_id, worker_id, coin, network, enabled,
                    minimum_payout, schedule_type, destination_wallet_id, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (worker_id, coin, network) DO UPDATE SET
                    enabled=EXCLUDED.enabled,
                    minimum_payout=EXCLUDED.minimum_payout,
                    schedule_type=EXCLUDED.schedule_type,
                    destination_wallet_id=EXCLUDED.destination_wallet_id,
                    metadata=EXCLUDED.metadata,
                    updated_at=NOW()
                RETURNING *
                """,
                (
                    uuid4(), values["worker_id"], values["coin"], values["network"],
                    values["enabled"], values.get("minimum_payout"),
                    values.get("schedule_type"), values.get("destination_wallet_id"),
                    Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def eligible_balances(self, profile: dict[str, Any]) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT b.pool_id, b.miner, b.worker, b.confirmed_balance,
                       w.worker_id, a.address AS destination_address,
                       p.enabled AS policy_enabled,
                       p.minimum_payout AS worker_minimum_payout,
                       p.schedule_type AS worker_schedule_type
                FROM seymour_engine.worker_balances b
                JOIN seymour_engine.workers w
                  ON w.pool_id=b.pool_id AND w.miner=b.miner AND w.worker=b.worker
                LEFT JOIN seymour_engine.worker_payment_policies p
                  ON p.worker_id=w.worker_id AND p.coin=%s AND p.network=%s
                LEFT JOIN seymour_engine.worker_payout_addresses a
                  ON a.worker_id=w.worker_id AND a.status='active'
                 AND a.validation_status='valid'
                WHERE b.pool_id=%s AND b.confirmed_balance > 0
                ORDER BY b.miner, b.worker
                """,
                (profile["coin"], profile["network"], profile["pool_id"]),
            )
            return [dict(row) for row in cursor.fetchall()]

    def acquire_run(
        self, *, scheduler_profile_id: UUID, run_key: str, trigger_type: str,
        actor: str, retry_of_run_id: UUID | None = None,
    ) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO seymour_engine.payment_scheduler_runs (
                        scheduler_run_id, scheduler_profile_id, run_key,
                        trigger_type, actor, lock_token, retry_of_run_id
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                    RETURNING *
                    """,
                    (
                        uuid4(), scheduler_profile_id, run_key, trigger_type,
                        actor, uuid4(), retry_of_run_id,
                    ),
                )
            except UniqueViolation:
                connection.rollback()
                return None
            row = dict(cursor.fetchone())
            self._event(cursor, row["scheduler_run_id"], None, "run_started", actor, {})
            connection.commit()
            return row

    def create_job(self, *, scheduler_run_id: UUID, row: dict[str, Any]) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.payment_scheduler_jobs (
                    scheduler_job_id, scheduler_run_id, worker_id, pool_id,
                    miner, worker, destination_address, eligible_balance,
                    threshold_amount, payout_amount, status
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    uuid4(), scheduler_run_id, row.get("worker_id"), row["pool_id"],
                    row["miner"], row.get("worker", ""), row["destination_address"],
                    row["eligible_balance"], row["threshold_amount"],
                    row["payout_amount"], row.get("status", "pending"),
                ),
            )
            job = dict(cursor.fetchone())
            connection.commit()
            return job

    def attach_batch(self, *, scheduler_job_ids: list[UUID], payout_batch_id: UUID) -> None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE seymour_engine.payment_scheduler_jobs
                SET payout_batch_id=%s, status='batched', updated_at=NOW()
                WHERE scheduler_job_id=ANY(%s)
                """,
                (payout_batch_id, scheduler_job_ids),
            )
            connection.commit()

    def finish_run(self, *, scheduler_run_id: UUID, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE seymour_engine.payment_scheduler_runs
                SET status=%s, eligible_count=%s, payout_count=%s,
                    skipped_count=%s, failed_count=%s, total_amount=%s,
                    failure_reason=%s, completed_at=NOW(), metadata=%s
                WHERE scheduler_run_id=%s
                RETURNING *
                """,
                (
                    values["status"], values["eligible_count"], values["payout_count"],
                    values["skipped_count"], values["failed_count"],
                    values["total_amount"], values.get("failure_reason"),
                    Jsonb(values.get("metadata", {})), scheduler_run_id,
                ),
            )
            row = dict(cursor.fetchone())
            cursor.execute(
                """
                UPDATE seymour_engine.payment_scheduler_profiles p
                SET last_run_at=NOW(), next_run_at=%s, updated_at=NOW()
                FROM seymour_engine.payment_scheduler_runs r
                WHERE r.scheduler_run_id=%s
                  AND p.scheduler_profile_id=r.scheduler_profile_id
                """,
                (values.get("next_run_at"), scheduler_run_id),
            )
            self._event(
                cursor, scheduler_run_id, None, f"run_{values['status']}",
                values.get("actor", "scheduler"), values.get("metadata", {}),
            )
            connection.commit()
            return row

    def list_runs(
        self, *, scheduler_profile_id: UUID | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM seymour_engine.payment_scheduler_runs"
        params: list[Any] = []
        if scheduler_profile_id:
            query += " WHERE scheduler_profile_id=%s"
            params.append(scheduler_profile_id)
        query += " ORDER BY started_at DESC LIMIT %s"
        params.append(limit)
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def list_jobs(self, *, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = "SELECT * FROM seymour_engine.payment_scheduler_jobs"
        params: list[Any] = []
        if status:
            query += " WHERE status=%s"
            params.append(status)
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def transition_job(
        self, *, scheduler_job_id: UUID, status: str, failure_reason: str | None,
        next_attempt_at: Any, increment_attempt: bool,
    ) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE seymour_engine.payment_scheduler_jobs
                SET status=%s, failure_reason=%s, next_attempt_at=%s,
                    attempt_count=attempt_count + %s, updated_at=NOW()
                WHERE scheduler_job_id=%s AND status NOT IN ('completed', 'cancelled')
                RETURNING *
                """,
                (
                    status, failure_reason, next_attempt_at,
                    1 if increment_attempt else 0, scheduler_job_id,
                ),
            )
            row = cursor.fetchone()
            if row:
                connection.commit()
                return dict(row)
            return None

    @staticmethod
    def _event(
        cursor: Any, scheduler_run_id: UUID | None, scheduler_job_id: UUID | None,
        event_type: str, actor: str, details: dict[str, Any],
    ) -> None:
        cursor.execute(
            """
            INSERT INTO seymour_engine.payment_scheduler_events (
                scheduler_event_id, scheduler_run_id, scheduler_job_id,
                event_type, actor, details
            ) VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (
                uuid4(), scheduler_run_id, scheduler_job_id,
                event_type, actor, Jsonb(details),
            ),
        )
