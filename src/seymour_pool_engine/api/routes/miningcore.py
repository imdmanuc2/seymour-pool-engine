from fastapi import APIRouter, HTTPException, Query

from seymour_pool_engine.services.miningcore_service import (
    get_miningcore_pools,
    get_miningcore_status,
    get_miningcore_workers,
)

router = APIRouter(prefix="/miningcore", tags=["miningcore"])


@router.get("/status")
def miningcore_status() -> dict:
    return get_miningcore_status()


@router.get("/pools")
def miningcore_pools() -> dict:
    try:
        return get_miningcore_pools()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="MiningCore provider query failed") from exc


@router.get("/workers")
def miningcore_workers(pool_id: str | None = Query(default=None, alias="poolId")) -> dict:
    try:
        return get_miningcore_workers(pool_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="MiningCore provider query failed") from exc
