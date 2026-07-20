import hashlib
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from seymour_pool_engine.database import test_engine_database, test_miningcore_database
from seymour_pool_engine.repositories.health_monitoring_repository import (
    HealthMonitoringRepository,
)

repository = HealthMonitoringRepository()

_STATUS_MAP = {
    "online": "healthy",
    "offline": "critical",
    "disabled": "disabled",
}


def _fingerprint(scope_type: str, scope_id: str | None, component: str) -> str:
    value = f"{scope_type}:{scope_id or '-'}:{component}"
    return hashlib.sha256(value.encode()).hexdigest()


def _probe(component: str, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "component": component,
        "status": _STATUS_MAP.get(result.get("status"), "warning"),
        "summary": result.get("summary", "No health summary available"),
        "details": result.get("details", {}),
    }


def collect_health(
    *,
    scope_type: str = "engine",
    scope_id: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    observations = [
        _probe("engine-database", test_engine_database()),
        _probe("miningcore-database", test_miningcore_database()),
    ]
    saved = []
    alerts = []
    for observation in observations:
        if persist:
            observation_id = repository.save_observation(
                scope_type=scope_type,
                scope_id=scope_id,
                component=observation["component"],
                status=observation["status"],
                summary=observation["summary"],
                details=observation["details"],
            )
            saved.append(str(observation_id))
        fingerprint = _fingerprint(scope_type, scope_id, observation["component"])
        if observation["status"] in {"warning", "critical"}:
            severity = observation["status"]
            if persist:
                alert = repository.upsert_alert(
                    scope_type=scope_type,
                    scope_id=scope_id,
                    component=observation["component"],
                    severity=severity,
                    fingerprint=fingerprint,
                    summary=observation["summary"],
                    details=observation["details"],
                )
                alerts.append(alert)
        elif observation["status"] == "healthy" and persist:
            repository.resolve_alert(
                fingerprint=fingerprint,
                message=f"{observation['component']} returned to healthy",
            )

    enabled = [item for item in observations if item["status"] != "disabled"]
    if any(item["status"] == "critical" for item in enabled):
        status = "critical"
    elif any(item["status"] == "warning" for item in enabled):
        status = "warning"
    else:
        status = "healthy"
    return {
        "scopeType": scope_type,
        "scopeId": scope_id,
        "status": status,
        "observedAt": datetime.now(UTC),
        "observations": observations,
        "observationIds": saved,
        "alertsCreatedOrUpdated": len(alerts),
    }


def list_health_observations(
    *,
    scope_type: str | None = None,
    scope_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    _validate_limit(limit)
    rows = repository.list_observations(
        scope_type=scope_type,
        scope_id=scope_id,
        limit=limit,
    )
    return {"count": len(rows), "observations": rows}


def list_alerts(
    *,
    status: str | None = None,
    severity: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    _validate_limit(limit)
    valid_statuses = {"open", "acknowledged", "resolved", "suppressed"}
    valid_severities = {"warning", "critical"}
    if status is not None and status not in valid_statuses:
        raise ValueError("invalid alert status")
    if severity is not None and severity not in valid_severities:
        raise ValueError("invalid alert severity")
    rows = repository.list_alerts(status=status, severity=severity, limit=limit)
    return {"count": len(rows), "alerts": rows}


def acknowledge_alert(*, alert_id: UUID, actor: str) -> dict[str, Any]:
    actor = actor.strip()
    if not actor:
        raise ValueError("actor is required")
    alert = repository.acknowledge_alert(alert_id=alert_id, actor=actor)
    if not alert:
        raise LookupError("active alert not found")
    return alert


def suppress_alert(
    *,
    alert_id: UUID,
    actor: str,
    until: datetime,
    reason: str,
) -> dict[str, Any]:
    if until.tzinfo is None:
        raise ValueError("until must include a timezone")
    if until <= datetime.now(UTC):
        raise ValueError("until must be in the future")
    if not actor.strip() or not reason.strip():
        raise ValueError("actor and reason are required")
    alert = repository.suppress_alert(
        alert_id=alert_id,
        actor=actor.strip(),
        until=until,
        reason=reason.strip(),
    )
    if not alert:
        raise LookupError("active alert not found")
    return alert


def get_alert_events(*, alert_id: UUID) -> dict[str, Any]:
    events = repository.get_alert_events(alert_id=alert_id)
    return {"count": len(events), "events": events}


def _validate_limit(limit: int) -> None:
    if limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500")
