from __future__ import annotations

from typing import Any

from seymour_pool_engine.database.connections import engine_connection


class NodeFailoverRepository:
    def record(self, *, endpoint: str, event_type: str, detail: str | None = None) -> None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.bitcoin_rpc_failover_events
                    (endpoint, event_type, detail)
                VALUES (%s, %s, %s)
                """,
                (endpoint, event_type, detail),
            )
            connection.commit()

    def history(self, limit: int = 100) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT event_id, endpoint, event_type, detail, created_at
                FROM seymour_engine.bitcoin_rpc_failover_events
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            return list(cursor.fetchall())
