from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from seymour_pool_engine.database import engine_connection


class BlockRepository:
    """Persistence for block candidates, lifecycle state, and immutable events."""

    def upsert(self, *, provider_name: str, observations: list[dict[str, Any]]) -> dict[str, int]:
        inserted = 0
        updated = 0
        events = 0
        with engine_connection() as connection, connection.cursor() as cursor:
            for observation in observations:
                cursor.execute(
                    """
                    SELECT block_id, status, confirmations
                    FROM seymour_engine.blocks
                    WHERE provider_name = %s AND provider_block_key = %s
                    FOR UPDATE
                    """,
                    (provider_name, observation["provider_block_key"]),
                )
                existing = cursor.fetchone()
                if existing is None:
                    block_id = uuid4()
                    cursor.execute(
                        """
                        INSERT INTO seymour_engine.blocks (
                            block_id, provider_name, provider_block_key, pool_id,
                            block_height, block_hash, status, confirmations,
                            network_difficulty, reward, miner, worker, share_id,
                            found_at, confirmed_at, orphaned_at, last_checked_at,
                            metadata
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            block_id,
                            provider_name,
                            observation["provider_block_key"],
                            observation["pool_id"],
                            observation["block_height"],
                            observation.get("block_hash"),
                            observation["status"],
                            observation["confirmations"],
                            observation.get("network_difficulty"),
                            observation.get("reward"),
                            observation.get("miner"),
                            observation.get("worker", ""),
                            observation.get("share_id"),
                            observation["found_at"],
                            observation.get("confirmed_at"),
                            observation.get("orphaned_at"),
                            observation.get("last_checked_at"),
                            Jsonb(observation.get("metadata", {})),
                        ),
                    )
                    self._insert_event(
                        cursor,
                        block_id=block_id,
                        event_type="discovered",
                        previous_status=None,
                        new_status=observation["status"],
                        confirmations=observation["confirmations"],
                        details={"providerBlockKey": observation["provider_block_key"]},
                    )
                    inserted += 1
                    events += 1
                    continue

                existing_row = dict(existing)
                block_id = existing_row["block_id"]
                previous_status = existing_row["status"]
                previous_confirmations = int(existing_row["confirmations"])
                cursor.execute(
                    """
                    UPDATE seymour_engine.blocks
                    SET pool_id = %s,
                        block_height = %s,
                        block_hash = COALESCE(%s, block_hash),
                        status = %s,
                        confirmations = %s,
                        network_difficulty = COALESCE(%s, network_difficulty),
                        reward = COALESCE(%s, reward),
                        miner = COALESCE(%s, miner),
                        worker = %s,
                        share_id = COALESCE(%s, share_id),
                        found_at = %s,
                        confirmed_at = %s,
                        orphaned_at = %s,
                        last_checked_at = %s,
                        metadata = metadata || %s,
                        updated_at = NOW()
                    WHERE block_id = %s
                    """,
                    (
                        observation["pool_id"],
                        observation["block_height"],
                        observation.get("block_hash"),
                        observation["status"],
                        observation["confirmations"],
                        observation.get("network_difficulty"),
                        observation.get("reward"),
                        observation.get("miner"),
                        observation.get("worker", ""),
                        observation.get("share_id"),
                        observation["found_at"],
                        observation.get("confirmed_at"),
                        observation.get("orphaned_at"),
                        observation.get("last_checked_at"),
                        Jsonb(observation.get("metadata", {})),
                        block_id,
                    ),
                )
                updated += 1
                if previous_status != observation["status"]:
                    self._insert_event(
                        cursor,
                        block_id=block_id,
                        event_type="status_changed",
                        previous_status=previous_status,
                        new_status=observation["status"],
                        confirmations=observation["confirmations"],
                    )
                    events += 1
                elif previous_confirmations != observation["confirmations"]:
                    self._insert_event(
                        cursor,
                        block_id=block_id,
                        event_type="confirmation_updated",
                        previous_status=previous_status,
                        new_status=observation["status"],
                        confirmations=observation["confirmations"],
                    )
                    events += 1
            connection.commit()
        return {"inserted": inserted, "updated": updated, "events": events}

    def list_blocks(
        self,
        *,
        pool_id: str | None = None,
        status: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = "SELECT * FROM seymour_engine.blocks WHERE TRUE"
        params: list[Any] = []
        if pool_id is not None:
            query += " AND pool_id = %s"
            params.append(pool_id)
        if status is not None:
            query += " AND status = %s"
            params.append(status)
        if since is not None:
            query += " AND found_at >= %s"
            params.append(since)
        query += " ORDER BY found_at DESC, block_height DESC LIMIT %s"
        params.append(limit)
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return [dict(row) for row in cursor.fetchall()]

    def get(self, block_id: UUID) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seymour_engine.blocks WHERE block_id = %s",
                (block_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def events(self, block_id: UUID) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM seymour_engine.block_events
                WHERE block_id = %s
                ORDER BY occurred_at, event_id
                """,
                (block_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def statistics(self, *, pool_id: str | None = None) -> dict[str, Any]:
        query = """
            SELECT
                COUNT(*) AS total_blocks,
                COUNT(*) FILTER (WHERE status = 'candidate') AS candidate_blocks,
                COUNT(*) FILTER (WHERE status = 'immature') AS immature_blocks,
                COUNT(*) FILTER (WHERE status = 'confirmed') AS confirmed_blocks,
                COUNT(*) FILTER (WHERE status = 'orphaned') AS orphaned_blocks,
                COALESCE(SUM(reward) FILTER (WHERE status = 'confirmed'), 0) AS confirmed_reward,
                MAX(found_at) AS last_block_at
            FROM seymour_engine.blocks
            WHERE TRUE
        """
        params: list[Any] = []
        if pool_id is not None:
            query += " AND pool_id = %s"
            params.append(pool_id)
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(query, tuple(params))
            return dict(cursor.fetchone())

    @staticmethod
    def _insert_event(
        cursor: Any,
        *,
        block_id: UUID,
        event_type: str,
        previous_status: str | None,
        new_status: str,
        confirmations: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        cursor.execute(
            """
            INSERT INTO seymour_engine.block_events (
                event_id, block_id, event_type, previous_status,
                new_status, confirmations, details
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                uuid4(),
                block_id,
                event_type,
                previous_status,
                new_status,
                confirmations,
                Jsonb(details or {}),
            ),
        )
