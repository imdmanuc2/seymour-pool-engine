from __future__ import annotations

from datetime import datetime
from typing import Any

from seymour_pool_engine.database import engine_connection

DEFAULT_INITIAL_DIFFICULTY = 42.0


class StatisticsRepository:
    """Native statistics read model built from Seymour Stratum data."""

    @staticmethod
    def _work_expression(alias: str = "sub") -> str:
        # VarDiff history records the effective difficulty after each retarget.
        # Before the first retarget the production Stratum default is 42.
        return f"""
            COALESCE((
                SELECT h.new_difficulty::DOUBLE PRECISION
                FROM seymour_engine.stratum_difficulty_history h
                WHERE h.session_id = {alias}.session_id
                  AND h.created_at <= {alias}.created_at
                ORDER BY h.created_at DESC
                LIMIT 1
            ), {DEFAULT_INITIAL_DIFFICULTY})
        """

    def overview(self, *, since: datetime) -> dict[str, Any]:
        work = self._work_expression()
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    COALESCE(SUM({work}) FILTER (WHERE sub.accepted), 0)
                        AS accepted_difficulty,
                    COUNT(*) FILTER (WHERE sub.accepted) AS accepted_shares,
                    COUNT(*) FILTER (WHERE NOT sub.accepted) AS rejected_shares,
                    COUNT(DISTINCT sub.worker_name) FILTER (WHERE sub.accepted)
                        AS active_workers,
                    MAX(sub.created_at) AS last_share_at,
                    MAX(sub.created_at) FILTER (WHERE sub.accepted) AS last_accepted_at
                FROM seymour_engine.stratum_submissions sub
                WHERE sub.created_at >= %s
                """,
                (since,),
            )
            row = cursor.fetchone()
            return dict(row)

    def workers(self, *, since: datetime, limit: int = 1000) -> list[dict[str, Any]]:
        work = self._work_expression()
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                f"""
                WITH recent AS (
                    SELECT
                        sub.worker_name,
                        COALESCE(SUM({work}) FILTER (WHERE sub.accepted), 0)
                            AS accepted_difficulty,
                        COUNT(*) FILTER (WHERE sub.accepted) AS accepted_shares,
                        COUNT(*) FILTER (WHERE NOT sub.accepted) AS rejected_shares,
                        MAX(sub.created_at) AS last_share_at,
                        MAX(sub.created_at) FILTER (WHERE sub.accepted) AS last_accepted_at
                    FROM seymour_engine.stratum_submissions sub
                    WHERE sub.created_at >= %s
                      AND sub.worker_name IS NOT NULL
                      AND sub.worker_name <> ''
                    GROUP BY sub.worker_name
                ), latest_session AS (
                    SELECT DISTINCT ON (worker_name)
                        worker_name,
                        session_id,
                        remote_host,
                        remote_port,
                        connected_at,
                        disconnected_at,
                        authorized,
                        difficulty::DOUBLE PRECISION AS difficulty,
                        last_activity_at,
                        last_share_at AS session_last_share_at
                    FROM seymour_engine.stratum_sessions
                    WHERE worker_name IS NOT NULL AND worker_name <> ''
                    ORDER BY worker_name, connected_at DESC
                )
                SELECT
                    COALESCE(r.worker_name, s.worker_name) AS worker_name,
                    r.accepted_difficulty,
                    r.accepted_shares,
                    r.rejected_shares,
                    r.last_share_at,
                    r.last_accepted_at,
                    s.session_id,
                    s.remote_host,
                    s.remote_port,
                    s.connected_at,
                    s.disconnected_at,
                    s.authorized,
                    s.difficulty,
                    s.last_activity_at,
                    s.session_last_share_at
                FROM recent r
                FULL OUTER JOIN latest_session s ON s.worker_name = r.worker_name
                ORDER BY COALESCE(r.accepted_difficulty, 0) DESC,
                         COALESCE(r.worker_name, s.worker_name)
                LIMIT %s
                """,
                (since, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def worker(self, *, worker_name: str, since: datetime) -> dict[str, Any] | None:
        rows = self.workers(since=since, limit=5000)
        return next((row for row in rows if row["worker_name"] == worker_name), None)

    def engine(self, *, since: datetime) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE disconnected_at IS NULL) AS active_sessions,
                    COUNT(DISTINCT worker_name) FILTER (
                        WHERE disconnected_at IS NULL
                          AND worker_name IS NOT NULL
                          AND worker_name <> ''
                    ) AS connected_workers,
                    COUNT(*) FILTER (
                        WHERE disconnected_at IS NULL AND authorized
                    ) AS authorized_sessions,
                    COALESCE(SUM(messages_received) FILTER (
                        WHERE disconnected_at IS NULL
                    ), 0) AS messages_received,
                    COALESCE(SUM(messages_sent) FILTER (
                        WHERE disconnected_at IS NULL
                    ), 0) AS messages_sent
                FROM seymour_engine.stratum_sessions
                """
            )
            session_row = dict(cursor.fetchone())
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS submissions,
                    COUNT(*) FILTER (WHERE accepted) AS accepted,
                    COUNT(*) FILTER (WHERE NOT accepted) AS rejected,
                    MAX(created_at) AS latest_submission
                FROM seymour_engine.stratum_submissions
                WHERE created_at >= %s
                """,
                (since,),
            )
            return {**session_row, **dict(cursor.fetchone())}
