from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from seymour_pool_engine.services.reliability_service import ReliabilityService

router = APIRouter(prefix="/reliability", tags=["reliability-backup-recovery"])


class ProfileRequest(BaseModel):
    display_name: str = Field(alias="displayName")
    enabled: bool = True
    backup_type: str = Field(alias="backupType")
    schedule_expression: str | None = Field(default=None, alias="scheduleExpression")
    retention_days: int = Field(default=30, alias="retentionDays")
    encryption_required: bool = Field(default=True, alias="encryptionRequired")
    compression: str = "gzip"
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class TargetRequest(BaseModel):
    target_type: str = Field(alias="targetType")
    location: str
    enabled: bool = True
    encryption_key_reference: str | None = Field(default=None, alias="encryptionKeyReference")
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class BackupRequest(BaseModel):
    target_id: UUID = Field(alias="targetId")
    requested_by: str = Field(default="api", alias="requestedBy")
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class RestoreRequest(BaseModel):
    mode: str = "validate"
    requested_by: str = Field(default="api", alias="requestedBy")
    target_environment: str = Field(default="validation", alias="targetEnvironment")
    model_config = {"populate_by_name": True}


def call(method: str, **kwargs: Any):
    try:
        return getattr(ReliabilityService(), method)(**kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Reliability operation failed") from exc


@router.get("/backup-profiles")
def profiles():
    return call("profiles")


@router.put("/backup-profiles/{profile_key}")
def put_profile(profile_key: str, request: ProfileRequest):
    return call("put_profile", profile_key=profile_key, **request.model_dump())


@router.get("/backup-targets")
def targets():
    return call("targets")


@router.put("/backup-targets/{target_key}")
def put_target(target_key: str, request: TargetRequest):
    return call("put_target", target_key=target_key, **request.model_dump())


@router.post("/backup-profiles/{profile_key}/runs", status_code=202)
def request_backup(profile_key: str, request: BackupRequest):
    return call("request_backup", profile_key=profile_key, **request.model_dump())


@router.get("/backup-runs")
def runs(limit: int = 100):
    return call("runs", limit=limit)


@router.post("/backup-runs/{backup_run_id}/restore-runs", status_code=202)
def request_restore(backup_run_id: UUID, request: RestoreRequest):
    return call("request_restore", backup_run_id=backup_run_id, **request.model_dump())


@router.get("/disaster-recovery-playbooks")
def playbooks():
    return call("playbooks")
