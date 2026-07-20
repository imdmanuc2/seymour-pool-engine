from collections.abc import Iterable
from datetime import datetime
from typing import Any
from uuid import uuid4

from seymour_pool_engine.database import engine_connection
from seymour_pool_engine.providers.models import ShareSummary


class ShareRepository:
    """Persistence boundary for provider share observations."""

    def ingest(
        self,
        *,
        provider_name: str,
        observations: Iterable[ShareSummary],
    ) -> dict[str, int]:
        observed = list(observations)
        inserted = 0
        duplicates = 0

        with engine_connection() as connection, connection.cursor() as cursor:
            for observation in observed:
                cursor.execute(
                    """
                    INSERT INTO seymour_engine.shares (
                        share_id,
                        provider_name,
                        provider_share_key,
                        worker_id,
                        pool_id,
                        miner,
                        worker,
                        difficulty,
                        network_difficulty,
                        block_height,
                        ip_address,
                        user_agent,
                        provider_created_at,
                        metadata,
                        share_status
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        (
                            SELECT worker_id
                            FROM seymour_engine.workers
                            WHERE provider_name = %s
                              AND pool_id = %s
                              AND miner = %s
                              AND worker = %s
                            LIMIT 1
                        ),
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (provider_name, provider_share_key) DO NOTHING
                    """,
                    (
                        str(uuid4()),
                        provider_name,
                        observation.provider_share_key,
                        provider_name,
                        observation.pool_id,
                        observation.miner,
                        observation.worker or "",
                        observation.pool_id,
                        observation.miner,
                        observation.worker or "",
                        observation.difficulty,
                        observation.network_difficulty,
                        observation.block_height,
                        observation.ip_address,
                        observation.user_agent,
                        observation.created_at,
                        observation.metadata,
                        str(observation.metadata.get("shareStatus", "accepted")).lower(),
                    ),
                )
                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    duplicates += 1

        return {
            "observed": len(observed),
            "inserted": inserted,
            "duplicates": duplicates,
        }

    def list_shares(
        self,
        *,
        pool_id: str | None = None,
        miner: str | None = None,
        worker: str | None = None,
        provider_name: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT
                share_id,
                provider_name,
                provider_share_key,
                worker_id,
                pool_id,
                miner,
                worker,
                difficulty,
                network_difficulty,
                block_height,
                ip_address,
                user_agent,
                provider_created_at,
                ingested_at,
                metadata
            FROM seymour_engine.shares
            WHERE TRUE
        """
        params: list[Any] = []
        if pool_id is not None:
            query += " AND pool_id = %s"
            params.append(pool_id)
        if miner is not None:
            query += " AND miner = %s"
            params.append(miner)
        if worker is not None:
            query += " AND worker = %s"
            params.append(worker)
        if provider_name is not None:
            query += " AND provider_name = %s"
            params.append(provider_name)
        if since is not None:
            query += " AND provider_created_at > %s"
            params.append(since)
        query += " ORDER BY provider_created_at DESC LIMIT %s"
        params.append(limit)

        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]
