from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from seymour_pool_engine.database import engine_connection


class PayoutRepository:
    def eligible_balances(
        self, *, pool_id: str, minimum_payout: Decimal
    ) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT b.pool_id, b.miner, b.worker, b.confirmed_balance,
                       w.worker_id, p.address AS destination_address
                FROM seymour_engine.worker_balances b
                LEFT JOIN seymour_engine.workers w
                  ON w.pool_id=b.pool_id AND w.miner=b.miner AND w.worker=b.worker
                LEFT JOIN seymour_engine.worker_payout_addresses p
                  ON p.worker_id=w.worker_id AND p.status='active'
                 AND p.validation_status='valid'
                WHERE b.pool_id=%s AND b.confirmed_balance >= %s
                ORDER BY b.miner, b.worker
                """,
                (pool_id, minimum_payout),
            )
            return [dict(row) for row in cursor.fetchall()]

    def create_batch(self, **values: Any) -> dict[str, Any]:
        batch_id = uuid4()
        items = values["items"]
        total = sum((Decimal(str(item["amount"])) for item in items), Decimal("0"))
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.payout_batches (
                    payout_batch_id, batch_key, pool_id, coin, network,
                    source_wallet_id, minimum_payout, total_amount, item_count,
                    requested_by, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    batch_id,
                    values["batch_key"],
                    values["pool_id"],
                    values["coin"],
                    values["network"],
                    values["source_wallet_id"],
                    values["minimum_payout"],
                    total,
                    len(items),
                    values["requested_by"],
                    Jsonb(values.get("metadata", {})),
                ),
            )
            batch = dict(cursor.fetchone())
            for item in items:
                cursor.execute(
                    """
                    INSERT INTO seymour_engine.payout_items (
                        payout_item_id, payout_batch_id, worker_id, pool_id,
                        miner, worker, destination_address, amount, metadata
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        uuid4(), batch_id, item.get("worker_id"), values["pool_id"],
                        item["miner"], item.get("worker", ""),
                        item["destination_address"], item["amount"],
                        Jsonb(item.get("metadata", {})),
                    ),
                )
            self._event(cursor, batch_id, "created", values["requested_by"], {})
            connection.commit()
            return batch

    def get_batch(self, payout_batch_id: UUID) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seymour_engine.payout_batches WHERE payout_batch_id=%s",
                (payout_batch_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_batches(self, *, pool_id: str | None, limit: int) -> list[dict[str, Any]]:
        sql = "SELECT * FROM seymour_engine.payout_batches"
        params: list[Any] = []
        if pool_id:
            sql += " WHERE pool_id=%s"
            params.append(pool_id)
        sql += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def items(self, payout_batch_id: UUID) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM seymour_engine.payout_items
                WHERE payout_batch_id=%s ORDER BY created_at
                """,
                (payout_batch_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def transition(
        self, *, payout_batch_id: UUID, from_statuses: tuple[str, ...],
        to_status: str, actor: str, transaction_id: str | None = None,
        failure_reason: str | None = None,
    ) -> dict[str, Any] | None:
        time_field = {
            "approved": "approved_at", "processing": "started_at",
            "completed": "completed_at",
        }.get(to_status)
        assignments = ["status=%s", "updated_at=NOW()"]
        params: list[Any] = [to_status]
        if time_field:
            assignments.append(f"{time_field}=NOW()")
        if transaction_id is not None:
            assignments.append("transaction_id=%s")
            params.append(transaction_id)
        if failure_reason is not None:
            assignments.append("failure_reason=%s")
            params.append(failure_reason)
        if to_status == "approved":
            assignments.append("approved_by=%s")
            params.append(actor)
        params.extend([payout_batch_id, list(from_statuses)])
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE seymour_engine.payout_batches
                SET {', '.join(assignments)}
                WHERE payout_batch_id=%s AND status=ANY(%s)
                RETURNING *
                """,
                params,
            )
            row = cursor.fetchone()
            if row:
                if to_status != "approved":
                    cursor.execute(
                        """
                        UPDATE seymour_engine.payout_items
                        SET status=%s, transaction_id=COALESCE(%s, transaction_id),
                            failure_reason=COALESCE(%s, failure_reason),
                            completed_at=CASE
                                WHEN %s='completed' THEN NOW() ELSE completed_at
                            END
                        WHERE payout_batch_id=%s
                        """,
                        (
                            to_status, transaction_id, failure_reason,
                            to_status, payout_batch_id,
                        ),
                    )
                self._event(cursor, payout_batch_id, to_status, actor, {
                    "transactionId": transaction_id, "failureReason": failure_reason,
                })
                connection.commit()
                return dict(row)
            return None

    def events(self, payout_batch_id: UUID) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM seymour_engine.payout_events
                WHERE payout_batch_id=%s ORDER BY created_at
                """,
                (payout_batch_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def _event(
        cursor: Any, payout_batch_id: UUID, event_type: str,
        actor: str, details: dict[str, Any],
    ) -> None:
        cursor.execute(
            """
            INSERT INTO seymour_engine.payout_events (
                payout_event_id, payout_batch_id, event_type, actor, details
            ) VALUES (%s,%s,%s,%s,%s)
            """,
            (uuid4(), payout_batch_id, event_type, actor, Jsonb(details)),
        )
