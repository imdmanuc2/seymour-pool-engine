from seymour_pool_engine.api.routes.health import router as health_router
from seymour_pool_engine.api.routes.miningcore import router as miningcore_router
from seymour_pool_engine.api.routes.system import router as system_router

__all__ = ["health_router", "miningcore_router", "system_router"]
