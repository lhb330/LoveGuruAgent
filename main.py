from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from common.exceptions import register_exception_handlers
from config.logger import setup_logging
from config.settings import get_settings
from controller.health_controller import router as health_router
from controller.chat_controller import router as chat_router
from controller.vector_controller import router as vector_router
from services.vector.pgvector_service import VectorBootstrapService

API_PREFIX = "/api"

@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    setup_logging(settings)
    bootstrap = VectorBootstrapService()
    bootstrap.initialize()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        version="0.1.0",
        lifespan=lifespan,
    )
    register_exception_handlers(app)
    app.include_router(health_router, prefix=f"{API_PREFIX}/v1/health", tags=["健康检查模块"])
    app.include_router(chat_router, prefix=f"{API_PREFIX}/v1/chat", tags=["chat"])
    app.include_router(vector_router, prefix=f"{API_PREFIX}/v1/vector", tags=["vector"])
    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
