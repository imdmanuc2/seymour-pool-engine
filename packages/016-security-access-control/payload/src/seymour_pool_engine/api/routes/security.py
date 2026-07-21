from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from seymour_pool_engine.services.security_service import SecurityService

router = APIRouter(prefix="/security", tags=["security-access-control"])


class PrincipalRequest(BaseModel):
    principal_type: str = Field(alias="principalType")
    principal_name: str = Field(alias="principalName")
    display_name: str | None = Field(default=None, alias="displayName")
    email: str | None = None
    password: str | None = None
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class RoleGrantRequest(BaseModel):
    role_name: str = Field(alias="roleName")
    granted_by: str = Field(default="api", alias="grantedBy")
    model_config = {"populate_by_name": True}


class ApiKeyRequest(BaseModel):
    key_name: str = Field(alias="keyName")
    created_by: str = Field(default="api", alias="createdBy")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


def service_call(method: str, **kwargs: Any) -> Any:
    try:
        return getattr(SecurityService(), method)(**kwargs)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Security operation failed") from exc


@router.get("/principals")
def principals():
    return service_call("principals")


@router.post("/principals", status_code=201)
def create_principal(request: PrincipalRequest):
    return service_call("create_principal", **request.model_dump())


@router.get("/roles")
def roles():
    return service_call("roles")


@router.put("/principals/{principal_id}/roles")
def grant_role(principal_id: UUID, request: RoleGrantRequest):
    return service_call("grant_role", principal_id=principal_id, **request.model_dump())


@router.get("/principals/{principal_id}/permissions")
def permissions(principal_id: UUID):
    return service_call("permissions", principal_id=principal_id)


@router.post("/principals/{principal_id}/api-keys", status_code=201)
def issue_api_key(principal_id: UUID, request: ApiKeyRequest):
    return service_call("issue_api_key", principal_id=principal_id, **request.model_dump())


@router.delete("/api-keys/{api_key_id}")
def revoke_api_key(api_key_id: UUID):
    return service_call("revoke_api_key", api_key_id=api_key_id)


@router.get("/whoami")
def whoami(x_seymour_api_key: str = Header(alias="X-Seymour-API-Key")):
    return service_call("authenticate_api_key", raw_key=x_seymour_api_key)


@router.get("/authorize/{permission}")
def authorize(permission: str, x_seymour_api_key: str = Header(alias="X-Seymour-API-Key")):
    return service_call("authorize", raw_key=x_seymour_api_key, permission=permission)


@router.get("/events")
def events(limit: int = 100):
    return service_call("events", limit=limit)
