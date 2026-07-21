from typing import Any
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from seymour_pool_engine.services.integration_service import IntegrationService

router = APIRouter(tags=["integration"])


class CommandRequest(BaseModel):
    capability: str
    targetType: str = Field(default="engine")
    targetId: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


@router.get("/version")
def version() -> dict[str, Any]:
    return IntegrationService().version()


@router.get("/integration/status")
def status() -> dict[str, str]:
    return {"status": "online", "contractVersion": "1.0"}


@router.get("/integration/summary")
def summary() -> dict[str, Any]:
    return IntegrationService().summary()


@router.get("/integration/compatibility")
def compatibility() -> dict[str, Any]:
    service = IntegrationService()
    return {"items": [service._serialize(item) for item in service.repository.compatibility()]}


@router.get("/release/readiness")
def readiness() -> dict[str, Any]:
    return IntegrationService().readiness()


@router.post("/integration/commands")
def submit_command(
    body: CommandRequest,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    correlation_id: str | None = Header(None, alias="X-Correlation-ID"),
    client_key: str = Header("nexus-command-center", alias="X-Integration-Client"),
) -> dict[str, Any]:
    try:
        return IntegrationService().submit_command(
            client_key=client_key,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            capability=body.capability,
            target_type=body.targetType,
            target_id=body.targetId,
            parameters=body.parameters,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/integration/commands/{command_id}")
def command(command_id: UUID) -> dict[str, Any]:
    service = IntegrationService()
    row = service.repository.command(command_id)
    if not row:
        raise HTTPException(status_code=404, detail="Command not found")
    return service._serialize(row)
