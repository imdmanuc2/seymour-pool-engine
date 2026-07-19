from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from seymour_pool_engine.database import engine_connection
from seymour_pool_engine.providers.models import WorkerSummary


class WorkerRepository:
    """Persistence boundary for SPE-owned worker inventory."""

    def synchronize(
        self,
        *,
        provider_name: str,
        observations: Iterable[WorkerSummary],
        active_after: datetime,
        pool_id: str | None = None,
    ) -> dict[str, int]:
        now = datetime.now(UTC)
        observed = list(observations)
        observed_keys: set[tuple[str, str, str]] = set()
        created = 0
        updated = 0
        marked_offline = 0

        with engine_connection() as connection, connection.cursor() as cursor:
            for observation in observed:
                worker_name = observation.worker or ""
                key = (observation.pool_id, observation.miner, worker_name)
                observed_keys.add(key)
                lifecycle_state = (
                    "active" if observation.observed_at >= active_after else "offline"
                )
                offline_since = None if lifecycle_state == "active" else observation.observed_at

                cursor.execute(
                    """
                    INSERT INTO seymour_engine.workers (
                        worker_id, provider_name, pool_id, miner, worker,
                        lifecycle_state, hashrate, shares_per_second,
                        first_seen_at, last_seen_at, provider_observed_at,
                        last_sync_at, offline_since, created_at, updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s, %s
                    )
                    ON CONFLICT (provider_name, pool_id, miner, worker) DO UPDATE SET
                        lifecycle_state = EXCLUDED.lifecycle_state,
                        hashrate = EXCLUDED.hashrate,
                        shares_per_second = EXCLUDED.shares_per_second,
                        last_seen_at = GREATEST(
                            seymour_engine.workers.last_seen_at,
                            EXCLUDED.last_seen_at
                        ),
                        provider_observed_at = EXCLUDED.provider_observed_at,
                        last_sync_at = EXCLUDED.last_sync_at,
                        offline_since = CASE
                            WHEN EXCLUDED.lifecycle_state = 'active' THEN NULL
                            WHEN seymour_engine.workers.lifecycle_state = 'active'
                                THEN EXCLUDED.last_sync_at
                            ELSE COALESCE(
                                seymour_engine.workers.offline_since,
                                EXCLUDED.offline_since
                            )
                        END,
                        updated_at = EXCLUDED.updated_at
                    RETURNING (xmax = 0) AS inserted
                    """,
                    (
                        str(uuid4()),
                        provider_name,
                        observation.pool_id,
                        observation.miner,
                        worker_name,
                        lifecycle_state,
                        observation.hashrate,
                        observation.shares_per_second,
                        observation.observed_at,
                        observation.observed_at,
                        observation.observed_at,
                        now,
                        offline_since,
                        now,
                        now,
                    ),
                )
                row = cursor.fetchone()
                if row and row["inserted"]:
                    created += 1
                else:
                    updated += 1

            query = """
                SELECT worker_id, pool_id, miner, worker
                FROM seymour_engine.workers
                WHERE provider_name = %s
                  AND lifecycle_state NOT IN ('disabled', 'retired')
            """
            params: list[Any] = [provider_name]
            if pool_id is not None:
                query += " AND pool_id = %s"
                params.append(pool_id)

            cursor.execute(query, tuple(params))
            for row in cursor.fetchall():
                key = (row["pool_id"], row["miner"], row["worker"])
                if key in observed_keys:
                    continue
                cursor.execute(
                    """
                    UPDATE seymour_engine.workers
                    SET lifecycle_state = 'offline',
                        hashrate = 0,
                        shares_per_second = 0,
                        offline_since = COALESCE(offline_since, %s),
                        last_sync_at = %s,
                        updated_at = %s
                    WHERE worker_id = %s
                      AND lifecycle_state <> 'offline'
                    """,
                    (now, now, now, row["worker_id"]),
                )
                marked_offline += cursor.rowcount

        return {
            "observed": len(observed),
            "created": created,
            "updated": updated,
            "markedOffline": marked_offline,
        }

    def list_workers(
        self,
        *,
        pool_id: str | None = None,
        lifecycle_state: str | None = None,
        provider_name: str | None = None,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                worker_id, provider_name, pool_id, miner, worker,
                lifecycle_state, hashrate, shares_per_second,
                first_seen_at, last_seen_at, provider_observed_at,
                last_sync_at, offline_since, created_at, updated_at, metadata
            FROM seymour_engine.workers
            WHERE TRUE
        """
        params: list[Any] = []
        if pool_id is not None:
            query += " AND pool_id = %s"
            params.append(pool_id)
        if lifecycle_state is not None:
            query += " AND lifecycle_state = %s"
            params.append(lifecycle_state)
        if provider_name is not None:
            query += " AND provider_name = %s"
            params.append(provider_name)
        query += " ORDER BY lifecycle_state, pool_id, miner, worker"

        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
