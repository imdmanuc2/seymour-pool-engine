from datetime import UTC, datetime
from typing import Any

from psycopg.types.json import Jsonb

from seymour_pool_engine.database import engine_connection


class InstallationRepository:
    def register(
        self,
        *,
        installation_id: str,
        display_name: str,
        environment: str,
        hostname: str,
        engine_version: str,
        provider_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)

        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.installations (
                    installation_id,
                    display_name,
                    environment,
                    hostname,
                    first_seen_at,
                    last_seen_at,
                    engine_version,
                    provider_name,
                    updated_at,
                    metadata
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (installation_id) DO UPDATE SET
                    display_name = EXCLUDED.display_name,
                    environment = EXCLUDED.environment,
                    hostname = EXCLUDED.hostname,
                    last_seen_at = EXCLUDED.last_seen_at,
                    engine_version = EXCLUDED.engine_version,
                    provider_name = EXCLUDED.provider_name,
                    updated_at = EXCLUDED.updated_at,
                    metadata = (
                        seymour_engine.installations.metadata
                        || EXCLUDED.metadata
                    )
                RETURNING *
                """,
                (
                    installation_id,
                    display_name,
                    environment,
                    hostname,
                    now,
                    now,
                    engine_version,
                    provider_name,
                    now,
                    Jsonb(metadata or {}),
                ),
            )
            row = cursor.fetchone()
            connection.commit()

        return dict(row)
