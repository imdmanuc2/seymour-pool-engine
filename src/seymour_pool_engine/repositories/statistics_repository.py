from datetime import datetime
from typing import Any

from seymour_pool_engine.database import engine_connection


class StatisticsRepository:
    """Read model for rolling mining statistics derived from persisted shares."""

    def overview(self, *, since: datetime) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(difficulty) FILTER (
                        WHERE share_status = 'accepted'
                    ), 0)::DOUBLE PRECISION AS accepted_difficulty,
                    COUNT(*) FILTER (WHERE share_status = 'accepted') AS accepted_shares,
                    COUNT(*) FILTER (WHERE share_status = 'rejected') AS rejected_shares,
                    COUNT(*) FILTER (WHERE share_status = 'stale') AS stale_shares,
                    COUNT(DISTINCT worker_id) FILTER (
                        WHERE worker_id IS NOT NULL AND share_status = 'accepted'
                    ) AS active_workers,
                    COUNT(DISTINCT pool_id) AS active_pools,
                    MAX(provider_created_at) AS last_share_at
                FROM seymour_engine.shares
                WHERE provider_created_at >= %s
                """,
                (since,),
            )
            return dict(cursor.fetchone())

    def pools(self, *, since: datetime) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    pool_id,
                    COALESCE(SUM(difficulty) FILTER (
                        WHERE share_status = 'accepted'
                    ), 0)::DOUBLE PRECISION AS accepted_difficulty,
                    COUNT(*) FILTER (WHERE share_status = 'accepted') AS accepted_shares,
                    COUNT(*) FILTER (WHERE share_status = 'rejected') AS rejected_shares,
                    COUNT(*) FILTER (WHERE share_status = 'stale') AS stale_shares,
                    COUNT(DISTINCT worker_id) FILTER (
                        WHERE worker_id IS NOT NULL AND share_status = 'accepted'
                    ) AS active_workers,
                    MAX(provider_created_at) AS last_share_at
                FROM seymour_engine.shares
                WHERE provider_created_at >= %s
                GROUP BY pool_id
                ORDER BY pool_id
                """,
                (since,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def workers(
        self,
        *,
        since: datetime,
        pool_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                worker_id,
                pool_id,
                miner,
                worker,
                COALESCE(SUM(difficulty) FILTER (
                    WHERE share_status = 'accepted'
                ), 0)::DOUBLE PRECISION AS accepted_difficulty,
                COUNT(*) FILTER (WHERE share_status = 'accepted') AS accepted_shares,
                COUNT(*) FILTER (WHERE share_status = 'rejected') AS rejected_shares,
                COUNT(*) FILTER (WHERE share_status = 'stale') AS stale_shares,
                MAX(provider_created_at) AS last_share_at
            FROM seymour_engine.shares
            WHERE provider_created_at >= %s
        """
        params: list[Any] = [since]
        if pool_id is not None:
            query += " AND pool_id = %s"
            params.append(pool_id)
        query += """
            GROUP BY worker_id, pool_id, miner, worker
            ORDER BY accepted_difficulty DESC, miner, worker
            LIMIT %s
        """
        params.append(limit)
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
