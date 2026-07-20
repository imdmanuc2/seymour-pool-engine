from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from seymour_pool_engine.database import engine_connection


class DiagnosticRepository:
    """Persistence boundary for diagnostic and readiness runs."""

    def save_run(
        self,
        *,
        pool_id: str | None,
        operation: str,
        status: str,
        readiness_score: int,
        summary: str,
        checks: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> UUID:
        run_id = uuid4()
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.diagnostic_runs (
                    diagnostic_run_id, pool_id, operation, status,
                    readiness_score, completed_at, summary, metadata
                ) VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s)
                """,
                (
                    run_id,
                    pool_id,
                    operation,
                    status,
                    readiness_score,
                    summary,
                    Jsonb(metadata or {}),
                ),
            )
            for check in checks:
                cursor.execute(
                    """
                    INSERT INTO seymour_engine.diagnostic_checks (
                        diagnostic_check_id, diagnostic_run_id, component,
                        status, summary, details
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        uuid4(),
                        run_id,
                        check["component"],
                        check["status"],
                        check["summary"],
                        Jsonb(check.get("details", {})),
                    ),
                )
            connection.commit()
        return run_id

    def list_runs(self, *, pool_id: str | None, limit: int) -> list[dict[str, Any]]:
        query = """
            SELECT diagnostic_run_id, pool_id, operation, status,
                   readiness_score, started_at, completed_at, summary, metadata
            FROM seymour_engine.diagnostic_runs
            WHERE (%s IS NULL OR pool_id = %s)
            ORDER BY started_at DESC
            LIMIT %s
        """
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, (pool_id, pool_id, limit))
            return [dict(row) for row in cursor.fetchall()]
