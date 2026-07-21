from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from seymour_pool_engine.database.connections import engine_connection


class ReliabilityRepository:
    def list_profiles(self) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM seymour_engine.backup_profiles ORDER BY profile_key")
            return [dict(row) for row in cursor.fetchall()]

    def get_profile(self, profile_key: str) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seymour_engine.backup_profiles WHERE profile_key=%s", (profile_key,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def upsert_profile(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.backup_profiles (
                    backup_profile_id, profile_key, display_name, enabled, backup_type,
                    schedule_expression, retention_days, encryption_required, compression, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (profile_key) DO UPDATE SET
                    display_name=EXCLUDED.display_name, enabled=EXCLUDED.enabled,
                    backup_type=EXCLUDED.backup_type,
                    schedule_expression=EXCLUDED.schedule_expression,
                    retention_days=EXCLUDED.retention_days,
                    encryption_required=EXCLUDED.encryption_required,
                    compression=EXCLUDED.compression, metadata=EXCLUDED.metadata, updated_at=NOW()
                RETURNING *
            """,
                (
                    uuid4(),
                    values["profile_key"],
                    values["display_name"],
                    values.get("enabled", True),
                    values["backup_type"],
                    values.get("schedule_expression"),
                    values.get("retention_days", 30),
                    values.get("encryption_required", True),
                    values.get("compression", "gzip"),
                    Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def list_targets(self) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM seymour_engine.backup_targets ORDER BY target_key")
            return [dict(row) for row in cursor.fetchall()]

    def upsert_target(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.backup_targets (
                    backup_target_id,target_key,target_type,location,enabled,encryption_key_reference,metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (target_key) DO UPDATE SET target_type=EXCLUDED.target_type,
                    location=EXCLUDED.location,enabled=EXCLUDED.enabled,
                    encryption_key_reference=EXCLUDED.encryption_key_reference,
                    metadata=EXCLUDED.metadata,updated_at=NOW()
                RETURNING *
            """,
                (
                    uuid4(),
                    values["target_key"],
                    values["target_type"],
                    values["location"],
                    values.get("enabled", True),
                    values.get("encryption_key_reference"),
                    Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def create_run(
        self, profile_id: UUID, target_id: UUID, requested_by: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO seymour_engine.backup_runs
                (backup_run_id,backup_profile_id,backup_target_id,status,requested_by,metadata)
                VALUES (%s,%s,%s,'queued',%s,%s) RETURNING *""",
                (uuid4(), profile_id, target_id, requested_by, Jsonb(metadata)),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def list_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seymour_engine.backup_runs ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def record_artifact(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO seymour_engine.backup_artifacts
                (backup_artifact_id,backup_run_id,artifact_type,relative_path,size_bytes,sha256_checksum,
                 encrypted,encryption_algorithm) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                (
                    uuid4(),
                    values["backup_run_id"],
                    values["artifact_type"],
                    values["relative_path"],
                    values["size_bytes"],
                    values["sha256_checksum"],
                    values.get("encrypted", False),
                    values.get("encryption_algorithm"),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def record_integrity_check(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO seymour_engine.backup_integrity_checks
                (backup_integrity_check_id,backup_artifact_id,status,expected_checksum,observed_checksum,checked_by,details)
                VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *""",
                (
                    uuid4(),
                    values["backup_artifact_id"],
                    values["status"],
                    values["expected_checksum"],
                    values.get("observed_checksum"),
                    values["checked_by"],
                    Jsonb(values.get("details", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def create_restore_run(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO seymour_engine.restore_runs
                (restore_run_id,backup_run_id,mode,status,requested_by,target_environment)
                VALUES (%s,%s,%s,'queued',%s,%s) RETURNING *""",
                (
                    uuid4(),
                    values["backup_run_id"],
                    values["mode"],
                    values["requested_by"],
                    values["target_environment"],
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def list_playbooks(self) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seymour_engine.disaster_recovery_playbooks ORDER BY playbook_key"
            )
            return [dict(row) for row in cursor.fetchall()]
