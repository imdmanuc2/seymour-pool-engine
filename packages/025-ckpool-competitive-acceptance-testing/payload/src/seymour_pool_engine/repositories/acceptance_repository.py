from __future__ import annotations

import json
from typing import Any

from seymour_pool_engine.database import engine_connection


class AcceptanceRepository:
    def record(self, profile: str, report: dict[str, Any]) -> str:
        with engine_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO seymour_engine.acceptance_test_runs "
                    "(profile,status,checks_total,checks_passed,duration_ms,report,"
                    "completed_at) VALUES (%s,%s,%s,%s,%s,%s::jsonb,NOW()) "
                    "RETURNING run_id",
                    (
                        profile,
                        report["status"],
                        report["checksTotal"],
                        report["checksPassed"],
                        report["durationMs"],
                        json.dumps(report),
                    ),
                )
                run_id = cursor.fetchone()[0]
            connection.commit()
        return str(run_id)

    def recent(self, limit: int = 25) -> list[dict[str, Any]]:
        with engine_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT run_id,profile,status,checks_total,checks_passed,"
                    "duration_ms,report,started_at,completed_at "
                    "FROM seymour_engine.acceptance_test_runs "
                    "ORDER BY started_at DESC LIMIT %s",
                    (limit,),
                )
                rows = cursor.fetchall()
        return [
            {
                "runId": str(row[0]),
                "profile": row[1],
                "status": row[2],
                "checksTotal": row[3],
                "checksPassed": row[4],
                "durationMs": float(row[5] or 0),
                "report": row[6],
                "startedAt": row[7],
                "completedAt": row[8],
            }
            for row in rows
        ]
