from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from seymour_pool_engine.database import engine_connection


class WalletRepository:
    def create_wallet(self, **values: Any) -> dict[str, Any]:
        wallet_id = uuid4()
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.wallets (
                    wallet_id, wallet_key, pool_id, coin, network, purpose, address,
                    status, validation_status, descriptor_reference, secret_reference,
                    created_by, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'pending',%s,%s,%s,%s)
                RETURNING *
                """,
                (
                    wallet_id,
                    values["wallet_key"],
                    values.get("pool_id"),
                    values["coin"],
                    values["network"],
                    values["purpose"],
                    values["address"],
                    values["status"],
                    values.get("descriptor_reference"),
                    values.get("secret_reference"),
                    values["created_by"],
                    Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            self._event(cursor, wallet_id, "created", values["created_by"], {})
            connection.commit()
            return row

    def list_wallets(self, *, coin: str | None, purpose: str | None) -> list[dict[str, Any]]:
        where: list[str] = []
        params: list[Any] = []
        if coin:
            where.append("coin=%s")
            params.append(coin)
        if purpose:
            where.append("purpose=%s")
            params.append(purpose)
        clause = " WHERE " + " AND ".join(where) if where else ""
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seymour_engine.wallets" + clause + " ORDER BY created_at",
                params,
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_wallet(self, wallet_id: UUID) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seymour_engine.wallets WHERE wallet_id=%s", (wallet_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_status(self, *, wallet_id: UUID, status: str, actor: str) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE seymour_engine.wallets
                SET status=%s, updated_at=NOW()
                WHERE wallet_id=%s
                RETURNING *
                """,
                (status, wallet_id),
            )
            row = cursor.fetchone()
            if row:
                self._event(cursor, wallet_id, status, actor, {})
                connection.commit()
                return dict(row)
            return None

    def set_validation(
        self, *, wallet_id: UUID, valid: bool, actor: str, details: dict[str, Any]
    ) -> dict[str, Any] | None:
        state = "valid" if valid else "invalid"
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE seymour_engine.wallets
                SET validation_status=%s, validated_at=NOW(), updated_at=NOW()
                WHERE wallet_id=%s
                RETURNING *
                """,
                (state, wallet_id),
            )
            row = cursor.fetchone()
            if row:
                self._event(cursor, wallet_id, "validated", actor, details)
                connection.commit()
                return dict(row)
            return None

    def wallet_events(self, wallet_id: UUID) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM seymour_engine.wallet_events
                WHERE wallet_id=%s ORDER BY created_at
                """,
                (wallet_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def upsert_worker_payout(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.worker_payout_addresses (
                    worker_payout_address_id, worker_id, coin, network, address,
                    status, validation_status, changed_by, metadata
                ) VALUES (%s,%s,%s,%s,%s,'active','pending',%s,%s)
                ON CONFLICT (worker_id, coin, network) DO UPDATE SET
                    address=EXCLUDED.address,
                    status='active',
                    validation_status='pending',
                    validated_at=NULL,
                    changed_by=EXCLUDED.changed_by,
                    updated_at=NOW()
                RETURNING *
                """,
                (
                    uuid4(),
                    values["worker_id"],
                    values["coin"],
                    values["network"],
                    values["address"],
                    values["changed_by"],
                    Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def worker_payouts(self, worker_id: UUID) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM seymour_engine.worker_payout_addresses
                WHERE worker_id=%s ORDER BY coin, network
                """,
                (worker_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def _event(cursor: Any, wallet_id: UUID, event_type: str, actor: str, details: dict[str, Any]) -> None:
        cursor.execute(
            """
            INSERT INTO seymour_engine.wallet_events (
                wallet_event_id, wallet_id, event_type, actor, details
            ) VALUES (%s,%s,%s,%s,%s)
            """,
            (uuid4(), wallet_id, event_type, actor, Jsonb(details)),
        )
