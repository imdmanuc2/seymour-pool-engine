from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from seymour_pool_engine.services.health_monitoring_service import (
    acknowledge_alert,
    collect_health,
    get_alert_events,
    list_alerts,
    list_health_observations,
    suppress_alert,
)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class HealthCollectionRequest(BaseModel):
    scope_type: str = "engine"
    scope_id: str | None = None
    persist: bool = True


class AlertAcknowledgeRequest(BaseModel):
    actor: str


class AlertSuppressRequest(BaseModel):
    actor: str
    until: datetime
    reason: str


@router.post("/health/collect")
def collect(request: HealthCollectionRequest) -> dict:
    try:
        return collect_health(
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            persist=request.persist,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Health collection failed") from exc


@router.get("/health/observations")
def observations(
    scope_type: Annotated[str | None, Query(alias="scopeType")] = None,
    scope_id: Annotated[str | None, Query(alias="scopeId")] = None,
    limit: Annotated[int, Query()] = 100,
) -> dict:
    try:
        return list_health_observations(
            scope_type=scope_type,
            scope_id=scope_id,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/alerts")
def alerts(
    status: Annotated[str | None, Query()] = None,
    severity: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query()] = 100,
) -> dict:
    try:
        return list_alerts(status=status, severity=severity, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge(alert_id: UUID, request: AlertAcknowledgeRequest) -> dict:
    try:
        return acknowledge_alert(alert_id=alert_id, actor=request.actor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/alerts/{alert_id}/suppress")
def suppress(alert_id: UUID, request: AlertSuppressRequest) -> dict:
    try:
        return suppress_alert(
            alert_id=alert_id,
            actor=request.actor,
            until=request.until,
            reason=request.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/alerts/{alert_id}/events")
def events(alert_id: UUID) -> dict:
    return get_alert_events(alert_id=alert_id)
