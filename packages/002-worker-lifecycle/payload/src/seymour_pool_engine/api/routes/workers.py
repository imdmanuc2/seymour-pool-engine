from fastapi import APIRouter, HTTPException, Query

from seymour_pool_engine.services.worker_service import get_workers, synchronize_workers

router = APIRouter(prefix="/workers", tags=["workers"])


@router.get("")
def workers(
    pool_id: str | None = Query(default=None, alias="poolId"),
    state: str | None = Query(default=None),
    provider: str | None = Query(default=None),
) -> dict:
    try:
        return get_workers(
            pool_id=pool_id,
            lifecycle_state=state,
            provider_name=provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Worker inventory query failed") from exc


@router.post("/sync")
def sync_workers(
    pool_id: str | None = Query(default=None, alias="poolId"),
) -> dict:
    try:
        return synchronize_workers(pool_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Worker provider synchronization failed") from exc
