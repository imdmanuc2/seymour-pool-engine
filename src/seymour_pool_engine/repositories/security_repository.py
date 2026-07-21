from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from seymour_pool_engine.database import engine_connection


class SecurityRepository:
    def create_principal(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.security_principals(
                    principal_id, principal_type, principal_name, display_name, email,
                    password_hash, status, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *
                """,
                (
                    uuid4(), values["principal_type"], values["principal_name"],
                    values.get("display_name"), values.get("email"), values.get("password_hash"),
                    values.get("status", "active"), Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def list_principals(self) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seymour_engine.security_principals "
                "ORDER BY principal_type, principal_name"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_principal_by_name(
        self, principal_type: str, principal_name: str
    ) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seymour_engine.security_principals "
                "WHERE principal_type=%s AND principal_name=%s",
                (principal_type, principal_name),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_principal(self, principal_id: UUID) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seymour_engine.security_principals WHERE principal_id=%s",
                (principal_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_roles(self) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT * FROM seymour_engine.security_roles ORDER BY role_name")
            return [dict(row) for row in cursor.fetchall()]

    def grant_role(self, principal_id: UUID, role_name: str, granted_by: str) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.security_principal_roles(
                    principal_id, role_id, granted_by
                )
                SELECT %s, role_id, %s FROM seymour_engine.security_roles WHERE role_name=%s
                ON CONFLICT (principal_id, role_id) DO UPDATE SET granted_by=EXCLUDED.granted_by
                RETURNING principal_id, role_id, granted_at, granted_by
                """,
                (principal_id, granted_by, role_name),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Role does not exist")
            connection.commit()
            return dict(row)

    def permissions_for_principal(self, principal_id: UUID) -> list[str]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT DISTINCT p.permission_name
                FROM seymour_engine.security_principal_roles pr
                JOIN seymour_engine.security_role_permissions rp ON rp.role_id=pr.role_id
                JOIN seymour_engine.security_permissions p ON p.permission_id=rp.permission_id
                WHERE pr.principal_id=%s ORDER BY p.permission_name
                """,
                (principal_id,),
            )
            return [row["permission_name"] for row in cursor.fetchall()]

    def create_api_key(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.security_api_keys(
                    api_key_id, principal_id, key_name, key_prefix, key_hash,
                    expires_at, created_by, metadata
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *
                """,
                (
                    uuid4(), values["principal_id"], values["key_name"], values["key_prefix"],
                    values["key_hash"], values.get("expires_at"), values["created_by"],
                    Jsonb(values.get("metadata", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def find_active_api_key(self, key_hash: str) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT k.*, p.principal_type, p.principal_name, p.status
                FROM seymour_engine.security_api_keys k
                JOIN seymour_engine.security_principals p ON p.principal_id=k.principal_id
                WHERE k.key_hash=%s AND k.revoked_at IS NULL
                  AND (k.expires_at IS NULL OR k.expires_at > NOW()) AND p.status='active'
                """,
                (key_hash,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def touch_api_key(self, api_key_id: UUID) -> None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "UPDATE seymour_engine.security_api_keys SET last_used_at=NOW() "
                "WHERE api_key_id=%s",
                (api_key_id,),
            )
            connection.commit()

    def revoke_api_key(self, api_key_id: UUID) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "UPDATE seymour_engine.security_api_keys SET revoked_at=NOW() "
                "WHERE api_key_id=%s RETURNING *",
                (api_key_id,),
            )
            row = cursor.fetchone()
            connection.commit()
            return dict(row) if row else None

    def record_event(self, **values: Any) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.security_events(
                    security_event_id, principal_id, event_type, outcome, actor, resource,
                    client_ip, correlation_id, details
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *
                """,
                (
                    uuid4(), values.get("principal_id"), values["event_type"], values["outcome"],
                    values["actor"], values.get("resource"), values.get("client_ip"),
                    values.get("correlation_id"), Jsonb(values.get("details", {})),
                ),
            )
            row = dict(cursor.fetchone())
            connection.commit()
            return row

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM seymour_engine.security_events ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
