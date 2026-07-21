import logging
from typing import Any
from uuid import UUID

from seymour_pool_engine.database import engine_connection
from seymour_pool_engine.engines.jobs.synthetic import SyntheticJob
from seymour_pool_engine.engines.session.models import StratumSession

logger = logging.getLogger(__name__)


class StratumRepository:
    def _run(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        try:
            with engine_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                connection.commit()
        except Exception:
            logger.exception("Stratum persistence operation failed")

    def create_session(self, s: StratumSession) -> None:
        self._run(
            "INSERT INTO seymour_engine.stratum_sessions "
            "(session_id,remote_host,remote_port,extranonce1,extranonce2_size,difficulty) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            (
                s.session_id,
                s.remote_host,
                s.remote_port,
                s.extranonce1,
                s.extranonce2_size,
                s.difficulty,
            ),
        )

    def update_session(self, s: StratumSession) -> None:
        self._run(
            "UPDATE seymour_engine.stratum_sessions SET user_agent=%s,worker_name=%s,"
            "subscribed=%s,authorized=%s,last_activity_at=NOW(),"
            "messages_received=%s,messages_sent=%s,submissions_received=%s "
            "WHERE session_id=%s",
            (
                s.user_agent,
                s.worker_name,
                s.subscribed,
                s.authorized,
                s.messages_received,
                s.messages_sent,
                s.submissions_received,
                s.session_id,
            ),
        )

    def close_session(self, session_id: UUID, reason: str) -> None:
        self._run(
            "UPDATE seymour_engine.stratum_sessions SET disconnected_at=NOW(),disconnect_reason=%s "
            "WHERE session_id=%s",
            (reason, session_id),
        )

    def record_job(self, job: SyntheticJob) -> None:
        self._run(
            "INSERT INTO seymour_engine.stratum_jobs "
            "(job_id,previous_block_hash,coinbase1,coinbase2,merkle_branches,"
            "version,nbits,ntime,clean_jobs) "
            "VALUES (%s,%s,%s,%s,'[]'::jsonb,%s,%s,%s,%s) "
            "ON CONFLICT(job_id) DO NOTHING",
            (
                job.job_id,
                job.previous_block_hash,
                job.coinbase1,
                job.coinbase2,
                job.version,
                job.nbits,
                job.ntime,
                job.clean_jobs,
            ),
        )

    def record_submission(self, s: StratumSession, params: list[Any]) -> None:
        values = params + [None] * 5
        self._run(
            "INSERT INTO seymour_engine.stratum_submissions "
            "(session_id,worker_name,job_id,extranonce2,ntime,nonce,accepted) "
            "VALUES (%s,%s,%s,%s,%s,%s,TRUE)",
            (s.session_id, s.worker_name, values[1], values[2], values[3], values[4]),
        )

    def status(self) -> dict[str, Any]:
        with engine_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FILTER(WHERE disconnected_at IS NULL),"
                    "COUNT(*) FILTER(WHERE disconnected_at IS NULL AND authorized),"
                    "COALESCE(SUM(submissions_received),0) FROM seymour_engine.stratum_sessions"
                )
                row = cursor.fetchone()
        return {
            "activeSessions": row[0],
            "authorizedSessions": row[1],
            "submissions": row[2],
        }

    def sessions(self, limit: int) -> list[dict[str, Any]]:
        with engine_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT session_id,remote_host,remote_port,worker_name,subscribed,"
                    "authorized,difficulty,connected_at,last_activity_at,disconnected_at "
                    "FROM seymour_engine.stratum_sessions ORDER BY connected_at DESC LIMIT %s",
                    (limit,),
                )
                rows = cursor.fetchall()
        return [
            {
                "sessionId": str(r[0]),
                "remoteHost": r[1],
                "remotePort": r[2],
                "workerName": r[3],
                "subscribed": r[4],
                "authorized": r[5],
                "difficulty": float(r[6]),
                "connectedAt": r[7],
                "lastActivityAt": r[8],
                "disconnectedAt": r[9],
            }
            for r in rows
        ]
