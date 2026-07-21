from __future__ import annotations

from typing import Any

from seymour_pool_engine.database import engine_connection
from seymour_pool_engine.engines.blocks.builder import AssembledBlock
from seymour_pool_engine.engines.jobs.models import StratumJob


class BlockCandidateRepository:
    def create(
        self,
        *,
        block: AssembledBlock,
        job: StratumJob,
        work_id: str | None,
    ) -> str:
        with engine_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO seymour_engine.bitcoin_block_candidates "
                    "(job_id,template_height,block_hash,header_hex,block_hex,"
                    "transaction_count,work_id) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s) "
                    "ON CONFLICT(block_hash) DO UPDATE SET updated_at=NOW() "
                    "RETURNING candidate_id",
                    (
                        job.job_id,
                        job.template_height,
                        block.block_hash,
                        block.header_hex,
                        block.block_hex,
                        block.transaction_count,
                        work_id,
                    ),
                )
                candidate_id = cursor.fetchone()[0]
            connection.commit()
        return str(candidate_id)

    def mark_submitted(
        self,
        candidate_id: str,
        *,
        accepted: bool,
        result: str | None,
        error: str | None,
    ) -> None:
        status = "accepted" if accepted else "rejected"
        with engine_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE seymour_engine.bitcoin_block_candidates SET submit_status=%s,"
                    "submit_result=%s,submit_error=%s,submitted_at=NOW(),updated_at=NOW() "
                    "WHERE candidate_id=%s",
                    (status, result, error, candidate_id),
                )
            connection.commit()

    def list_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with engine_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT candidate_id,job_id,template_height,block_hash,transaction_count,"
                    "submit_status,submit_result,submit_error,submitted_at,created_at "
                    "FROM seymour_engine.bitcoin_block_candidates "
                    "ORDER BY created_at DESC LIMIT %s",
                    (limit,),
                )
                rows = cursor.fetchall()
        return [
            {
                "candidateId": str(r[0]),
                "jobId": r[1],
                "height": r[2],
                "blockHash": r[3],
                "transactionCount": r[4],
                "submitStatus": r[5],
                "submitResult": r[6],
                "submitError": r[7],
                "submittedAt": r[8],
                "createdAt": r[9],
            }
            for r in rows
        ]

    def status(self) -> dict[str, Any]:
        with engine_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*),COUNT(*) FILTER(WHERE submit_status='accepted'),"
                    "COUNT(*) FILTER(WHERE submit_status='rejected'),MAX(submitted_at) "
                    "FROM seymour_engine.bitcoin_block_candidates"
                )
                row = cursor.fetchone()
        return {"total": row[0], "accepted": row[1], "rejected": row[2], "lastSubmittedAt": row[3]}
