from typing import Any
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from seymour_pool_engine.database import engine_connection


class HealthMonitoringRepository:
    """Persistence boundary for health observations and operational alerts."""

    def save_observation(
        self,
        *,
        scope_type: str,
        scope_id: str | None,
        component: str,
        status: str,
        summary: str,
        details: dict[str, Any] | None = None,
    ) -> UUID:
        observation_id = uuid4()
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO seymour_engine.health_observations (
                    health_observation_id, scope_type, scope_id, component,
                    status, summary, details
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    observation_id,
                    scope_type,
                    scope_id,
                    component,
                    status,
                    summary,
                    Jsonb(details or {}),
                ),
            )
            connection.commit()
        return observation_id

    def list_observations(
        self,
        *,
        scope_type: str | None,
        scope_id: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT health_observation_id, scope_type, scope_id, component,
                       status, summary, details, observed_at
                FROM seymour_engine.health_observations
                WHERE (%s IS NULL OR scope_type = %s)
                  AND (%s IS NULL OR scope_id = %s)
                ORDER BY observed_at DESC
                LIMIT %s
                """,
                (scope_type, scope_type, scope_id, scope_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def upsert_alert(
        self,
        *,
        scope_type: str,
        scope_id: str | None,
        component: str,
        severity: str,
        fingerprint: str,
        summary: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT alert_id, status
                FROM seymour_engine.alerts
                WHERE fingerprint = %s
                  AND status IN ('open', 'acknowledged', 'suppressed')
                FOR UPDATE
                """,
                (fingerprint,),
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    """
                    UPDATE seymour_engine.alerts
                    SET severity = %s,
                        summary = %s,
                        details = %s,
                        occurrence_count = occurrence_count + 1,
                        last_seen_at = NOW(),
                        status = CASE
                            WHEN status = 'suppressed'
                                 AND suppressed_until IS NOT NULL
                                 AND suppressed_until <= NOW()
                            THEN 'open'
                            ELSE status
                        END
                    WHERE alert_id = %s
                    RETURNING *
                    """,
                    (severity, summary, Jsonb(details or {}), existing["alert_id"]),
                )
                alert = dict(cursor.fetchone())
                event_type = "updated"
            else:
                alert_id = uuid4()
                cursor.execute(
                    """
                    INSERT INTO seymour_engine.alerts (
                        alert_id, scope_type, scope_id, component, severity,
                        status, fingerprint, summary, details
                    ) VALUES (%s, %s, %s, %s, %s, 'open', %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        alert_id,
                        scope_type,
                        scope_id,
                        component,
                        severity,
                        fingerprint,
                        summary,
                        Jsonb(details or {}),
                    ),
                )
                alert = dict(cursor.fetchone())
                event_type = "opened"
            self._insert_event(cursor, alert["alert_id"], event_type, None, summary)
            connection.commit()
            return alert

    def resolve_alert(self, *, fingerprint: str, message: str) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE seymour_engine.alerts
                SET status = 'resolved', resolved_at = NOW(), last_seen_at = NOW()
                WHERE fingerprint = %s
                  AND status IN ('open', 'acknowledged', 'suppressed')
                RETURNING *
                """,
                (fingerprint,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            alert = dict(row)
            self._insert_event(cursor, alert["alert_id"], "resolved", "system", message)
            connection.commit()
            return alert

    def list_alerts(
        self,
        *,
        status: str | None,
        severity: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT *
                FROM seymour_engine.alerts
                WHERE (%s IS NULL OR status = %s)
                  AND (%s IS NULL OR severity = %s)
                ORDER BY last_seen_at DESC
                LIMIT %s
                """,
                (status, status, severity, severity, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def acknowledge_alert(self, *, alert_id: UUID, actor: str) -> dict[str, Any] | None:
        return self._transition_alert(
            alert_id=alert_id,
            status="acknowledged",
            event_type="acknowledged",
            actor=actor,
            extra_sql="acknowledged_at = NOW(), acknowledged_by = %s",
            extra_values=(actor,),
            message=f"Alert acknowledged by {actor}",
        )

    def suppress_alert(
        self,
        *,
        alert_id: UUID,
        actor: str,
        until: Any,
        reason: str,
    ) -> dict[str, Any] | None:
        return self._transition_alert(
            alert_id=alert_id,
            status="suppressed",
            event_type="suppressed",
            actor=actor,
            extra_sql="suppressed_until = %s, suppression_reason = %s",
            extra_values=(until, reason),
            message=reason,
        )

    def get_alert_events(self, *, alert_id: UUID) -> list[dict[str, Any]]:
        with engine_connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT alert_event_id, alert_id, event_type, actor,
                       message, metadata, occurred_at
                FROM seymour_engine.alert_events
                WHERE alert_id = %s
                ORDER BY occurred_at DESC
                """,
                (alert_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def _transition_alert(
        self,
        *,
        alert_id: UUID,
        status: str,
        event_type: str,
        actor: str,
        extra_sql: str,
        extra_values: tuple[Any, ...],
        message: str,
    ) -> dict[str, Any] | None:
        with engine_connection() as connection, connection.cursor() as cursor:
            query = f"""
                UPDATE seymour_engine.alerts
                SET status = %s, {extra_sql}, last_seen_at = NOW()
                WHERE alert_id = %s
                  AND status IN ('open', 'acknowledged', 'suppressed')
                RETURNING *
            """
            cursor.execute(query, (status, *extra_values, alert_id))
            row = cursor.fetchone()
            if not row:
                return None
            alert = dict(row)
            self._insert_event(cursor, alert_id, event_type, actor, message)
            connection.commit()
            return alert

    @staticmethod
    def _insert_event(cursor, alert_id: UUID, event_type: str, actor: str | None, message: str):
        cursor.execute(
            """
            INSERT INTO seymour_engine.alert_events (
                alert_event_id, alert_id, event_type, actor, message
            ) VALUES (%s, %s, %s, %s, %s)
            """,
            (uuid4(), alert_id, event_type, actor, message),
        )
