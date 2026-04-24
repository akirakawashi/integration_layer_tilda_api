from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api.routers.v1.router import router as v1_router
from api.routers.v1.shemas import HealthResponse
from infrastructure.database.provider import DatabaseProvider
from setting import app_config
from setting.logging import configure_logging

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for the FastAPI application"""
    app.state.config = app_config

    await DatabaseProvider.init_engine()

    try:
        yield
    finally:
        await DatabaseProvider.dispose_engine()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(title=app_config.name, debug=app_config.debug, lifespan=lifespan)
    app.include_router(v1_router, prefix=app_config.api_prefix)

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    return app


app = create_app()


def main() -> None:
    uvicorn.run("api.app:app", host=app_config.host, port=app_config.port)


if __name__ == "__main__":
    main()
