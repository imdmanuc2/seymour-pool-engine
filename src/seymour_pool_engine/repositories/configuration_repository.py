from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from seymour_pool_engine.database.connections import engine_connection


class ConfigurationRepository:
    def upsert_profile_revision(
        self,
        *,
        profile_key: str,
        domain: str,
        configuration: dict[str, Any],
        checksum: str,
        change_summary: str,
        changed_by: str,
    ) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.configuration_profiles (
                    configuration_profile_id, profile_key, domain
                ) VALUES (%s, %s, %s)
                ON CONFLICT (profile_key) DO UPDATE
                SET domain=EXCLUDED.domain, updated_at=NOW()
                RETURNING *
                """,
                (uuid4(), profile_key, domain),
            )
            profile = dict(cursor.fetchone())
            cursor.execute(
                """
                SELECT * FROM seymour_engine.configuration_revisions
                WHERE configuration_profile_id=%s
                ORDER BY revision_number DESC LIMIT 1
                """,
                (profile["configuration_profile_id"],),
            )
            previous = cursor.fetchone()
            revision_number = 1 if previous is None else previous["revision_number"] + 1
            revision_id = uuid4()
            if previous is not None:
                cursor.execute(
                    """
                    UPDATE seymour_engine.configuration_revisions
                    SET status='superseded'
                    WHERE configuration_revision_id=%s AND status='active'
                    """,
                    (previous["configuration_revision_id"],),
                )
            cursor.execute(
                """
                INSERT INTO seymour_engine.configuration_revisions (
                    configuration_revision_id, configuration_profile_id, revision_number,
                    configuration, checksum, status, change_summary, changed_by,
                    previous_revision_id
                ) VALUES (%s,%s,%s,%s,%s,'active',%s,%s,%s)
                RETURNING *
                """,
                (
                    revision_id,
                    profile["configuration_profile_id"],
                    revision_number,
                    Jsonb(configuration),
                    checksum,
                    change_summary,
                    changed_by,
                    previous["configuration_revision_id"] if previous else None,
                ),
            )
            revision = dict(cursor.fetchone())
            cursor.execute(
                """
                UPDATE seymour_engine.configuration_profiles
                SET active_revision_id=%s, updated_at=NOW()
                WHERE configuration_profile_id=%s
                """,
                (revision_id, profile["configuration_profile_id"]),
            )
            connection.commit()
            return {**profile, **revision}

    def get_active(self, *, profile_key: str) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.profile_key, p.domain, r.*
                FROM seymour_engine.configuration_profiles p
                JOIN seymour_engine.configuration_revisions r
                  ON r.configuration_revision_id=p.active_revision_id
                WHERE p.profile_key=%s
                """,
                (profile_key,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_active(self) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.profile_key, p.domain, r.*
                FROM seymour_engine.configuration_profiles p
                JOIN seymour_engine.configuration_revisions r
                  ON r.configuration_revision_id=p.active_revision_id
                ORDER BY p.profile_key
                """
            )
            return [dict(row) for row in cursor.fetchall()]

    def history(self, *, profile_key: str) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.profile_key, p.domain, r.*
                FROM seymour_engine.configuration_profiles p
                JOIN seymour_engine.configuration_revisions r
                  ON r.configuration_profile_id=p.configuration_profile_id
                WHERE p.profile_key=%s
                ORDER BY r.revision_number DESC
                """,
                (profile_key,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def rollback(
        self, *, profile_key: str, revision_number: int, changed_by: str
    ) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.configuration_profile_id, p.domain, r.*
                FROM seymour_engine.configuration_profiles p
                JOIN seymour_engine.configuration_revisions r
                  ON r.configuration_profile_id=p.configuration_profile_id
                WHERE p.profile_key=%s AND r.revision_number=%s
                """,
                (profile_key, revision_number),
            )
            target = cursor.fetchone()
        if target is None:
            return None
        return self.upsert_profile_revision(
            profile_key=profile_key,
            domain=target["domain"],
            configuration=target["configuration"],
            checksum=target["checksum"],
            change_summary=f"Rollback to revision {revision_number}",
            changed_by=changed_by,
        )

    def record_validation(self, **values: Any) -> None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.configuration_validation_results (
                    configuration_validation_result_id, profile_key, domain, valid,
                    errors, warnings, configuration_checksum
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    uuid4(),
                    values["profile_key"],
                    values["domain"],
                    values["valid"],
                    Jsonb(values["errors"]),
                    Jsonb(values["warnings"]),
                    values["checksum"],
                ),
            )
            connection.commit()

    def record_export(self, *, checksum: str, profile_count: int, actor: str) -> UUID:
        export_id = uuid4()
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.configuration_exports (
                    configuration_export_id, export_version, profile_count,
                    payload_checksum, exported_by
                ) VALUES (%s,1,%s,%s,%s)
                """,
                (export_id, profile_count, checksum, actor),
            )
            connection.commit()
        return export_id

    def record_import(
        self,
        *,
        checksum: str,
        profile_count: int,
        actor: str,
        status: str,
        error_message: str | None = None,
    ) -> UUID:
        import_id = uuid4()
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.configuration_imports (
                    configuration_import_id, export_version, payload_checksum,
                    imported_by, status, profile_count, error_message
                ) VALUES (%s,1,%s,%s,%s,%s,%s)
                """,
                (import_id, checksum, actor, status, profile_count, error_message),
            )
            connection.commit()
        return import_id
