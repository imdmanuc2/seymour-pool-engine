from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg.types.json import Jsonb

from seymour_pool_engine.database.connections import engine_connection


class IntegrationRepository:
    def compatibility(self) -> list[dict[str, Any]]:
        with engine_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM seymour_engine.compatibility_matrix ORDER BY consumer")
            return list(cur.fetchall())

    def checklist(self, release_version: str) -> list[dict[str, Any]]:
        with engine_connection() as conn, conn.cursor() as cur:
            cur.execute(
                (
                    "SELECT * FROM seymour_engine.release_checklists "
                    "WHERE release_version=%s ORDER BY item_key"
                ),
                (release_version,),
            )
            return list(cur.fetchall())

    def find_command(self, client_key: str, idempotency_key: str) -> dict[str, Any] | None:
        with engine_connection() as conn, conn.cursor() as cur:
            cur.execute(
                (
                    "SELECT * FROM seymour_engine.integration_commands "
                    "WHERE client_key=%s AND idempotency_key=%s"
                ),
                (client_key, idempotency_key),
            )
            return cur.fetchone()

    def create_command(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as conn, conn.cursor() as cur:
            values = {
                **values,
                "parameters": Jsonb(values["parameters"]),
                "result": Jsonb(values["result"]),
            }
            cur.execute(
                (
                    "INSERT INTO seymour_engine.integration_commands "
                    "(client_key,idempotency_key,correlation_id,capability,target_type,target_id,"
                    "parameters,status,result,completed_at) VALUES "
                    "(%(client_key)s,%(idempotency_key)s,%(correlation_id)s,%(capability)s,"
                    "%(target_type)s,%(target_id)s,%(parameters)s,'completed',%(result)s,now()) "
                    "RETURNING *"
                ),
                values,
            )
            row = cur.fetchone()
            conn.commit()
            return row

    def command(self, command_id: UUID) -> dict[str, Any] | None:
        with engine_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM seymour_engine.integration_commands WHERE command_id=%s",
                (command_id,),
            )
            return cur.fetchone()
