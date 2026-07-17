from fastapi import APIRouter

from seymour_pool_engine.services import get_system_information

router = APIRouter(tags=["system"])


@router.get("/system")
def system_information() -> dict:
    return get_system_information()
