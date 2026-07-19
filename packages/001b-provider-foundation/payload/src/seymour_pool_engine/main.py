from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from seymour_pool_engine.api import api_router
from seymour_pool_engine.config import get_settings
from seymour_pool_engine.identity import get_or_create_installation_id
from seymour_pool_engine.services import register_installation


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_or_create_installation_id()
    register_installation()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.product_name,
        version=settings.version,
        description=(
            "Management, orchestration, health, and integration API "
            "for Seymour Pool."
        ),
        lifespan=lifespan,
    )

    app.include_router(api_router, prefix=f"/api/{settings.api_version}")

    @app.get("/", tags=["root"])
    def root() -> dict:
        return {
            "product": settings.product_name,
            "version": settings.version,
            "apiVersion": settings.api_version,
            "systemEndpoint": f"/api/{settings.api_version}/system",
            "healthEndpoint": f"/api/{settings.api_version}/health",
            "documentation": "/docs",
        }

    return app


app = create_app()


def run() -> None:
    settings = get_settings()

    uvicorn.run(
        "seymour_pool_engine.main:app",
        host=settings.bind_host,
        port=settings.bind_port,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    run()
