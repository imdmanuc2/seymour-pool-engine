from fastapi import APIRouter

from seymour_pool_engine.api.routes import (
    health_router,
    miningcore_router,
    system_router,
    workers_router,
)

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(health_router)
api_router.include_router(miningcore_router)
api_router.include_router(workers_router)
