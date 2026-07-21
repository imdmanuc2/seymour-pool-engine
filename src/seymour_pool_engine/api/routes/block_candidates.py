from fastapi import APIRouter, Query

from seymour_pool_engine.repositories.block_candidate_repository import BlockCandidateRepository

router = APIRouter(prefix="/block-candidates", tags=["block-candidates"])


@router.get("/status")
def candidate_status() -> dict[str, object]:
    return BlockCandidateRepository().status()


@router.get("")
def recent_candidates(limit: int = Query(default=50, ge=1, le=500)) -> dict[str, object]:
    return {"items": BlockCandidateRepository().list_recent(limit), "limit": limit}
