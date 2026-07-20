from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query

from seymour_pool_engine.services.statistics_service import (
    get_pool_statistics,
    get_statistics_overview,
    get_worker_statistics,
)

router = APIRouter(prefix="/statistics", tags=["statistics"])
Window = Literal["1m", "5m", "15m", "1h"]


@router.get("/overview")
def overview(window: Annotated[Window, Query()] = "5m") -> dict:
    try:
        return get_statistics_overview(window=window)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Statistics query failed") from exc


@router.get("/pools")
def pools(window: Annotated[Window, Query()] = "5m") -> dict:
    try:
        return get_pool_statistics(window=window)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Pool statistics query failed") from exc


@router.get("/workers")
def workers(
    window: Annotated[Window, Query()] = "5m",
    pool_id: Annotated[str | None, Query(alias="poolId")] = None,
    limit: Annotated[int, Query()] = 100,
) -> dict:
    try:
        return get_worker_statistics(window=window, pool_id=pool_id, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Worker statistics query failed") from exc
