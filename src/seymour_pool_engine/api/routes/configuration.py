from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from seymour_pool_engine.services.configuration_service import ConfigurationService

router = APIRouter(prefix="/config", tags=["configuration"])


class ConfigurationRequest(BaseModel):
    profile_key: str = Field(alias="profileKey")
    domain: str
    configuration: dict[str, Any]
    change_summary: str = Field(default="Configuration updated", alias="changeSummary")
    changed_by: str = Field(default="api", alias="changedBy")
    model_config = {"populate_by_name": True}


class ValidationRequest(BaseModel):
    profile_key: str = Field(alias="profileKey")
    domain: str
    configuration: dict[str, Any]
    model_config = {"populate_by_name": True}


class ExportRequest(BaseModel):
    actor: str = "api"


class ImportRequest(BaseModel):
    payload: dict[str, Any]
    checksum: str
    actor: str = "api"


class RollbackRequest(BaseModel):
    changed_by: str = Field(default="api", alias="changedBy")
    model_config = {"populate_by_name": True}


@router.get("")
def get_configuration(
    profile_key: Annotated[str | None, Query(alias="profileKey")] = None,
) -> Any:
    try:
        return ConfigurationService().get(profile_key=profile_key)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Configuration lookup failed") from exc


@router.put("")
def put_configuration(request: ConfigurationRequest) -> dict[str, Any]:
    try:
        return ConfigurationService().put(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Configuration update failed") from exc


@router.post("/validate")
def validate_configuration(request: ValidationRequest) -> dict[str, Any]:
    try:
        return ConfigurationService().validate(**request.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Configuration validation failed") from exc


@router.get("/history")
def configuration_history(
    profile_key: Annotated[str, Query(alias="profileKey")],
) -> list[dict[str, Any]]:
    try:
        return ConfigurationService().history(profile_key=profile_key)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Configuration history failed") from exc


@router.post("/export")
def export_configuration(request: ExportRequest) -> dict[str, Any]:
    try:
        return ConfigurationService().export(actor=request.actor)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Configuration export failed") from exc


@router.post("/import")
def import_configuration(request: ImportRequest) -> dict[str, Any]:
    try:
        return ConfigurationService().import_backup(**request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Configuration import failed") from exc


@router.post("/rollback/{revision_number}")
def rollback_configuration(
    revision_number: int,
    profile_key: Annotated[str, Query(alias="profileKey")],
    request: RollbackRequest,
) -> dict[str, Any]:
    try:
        return ConfigurationService().rollback(
            profile_key=profile_key,
            revision_number=revision_number,
            changed_by=request.changed_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Configuration rollback failed") from exc
