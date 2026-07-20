from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from seymour_pool_engine.services.diagnostic_service import (
    get_diagnostic_runs,
    run_pool_diagnostics,
)

router = APIRouter(prefix="/operations", tags=["operations"])


class DiagnosticRequest(BaseModel):
    pool_id: str | None = None
    persist: bool = True


@router.post("/diagnostics")
def diagnostics(request: DiagnosticRequest) -> dict:
    try:
        return run_pool_diagnostics(pool_id=request.pool_id, persist=request.persist)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Pool diagnostics failed") from exc


@router.get("/readiness")
def readiness(
    pool_id: Annotated[str | None, Query(alias="poolId")] = None,
    persist: Annotated[bool, Query()] = False,
) -> dict:
    try:
        return run_pool_diagnostics(pool_id=pool_id, persist=persist)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Pool readiness check failed") from exc


@router.get("/runs")
def runs(
    pool_id: Annotated[str | None, Query(alias="poolId")] = None,
    limit: Annotated[int, Query()] = 50,
) -> dict:
    try:
        return get_diagnostic_runs(pool_id=pool_id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Diagnostic run query failed") from exc
