from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
import logging

from common.exceptions import register_exception_handlers
from config.logger import setup_logging
from config.settings import get_settings
from config.checkpointer import init_checkpointer, close_checkpointer
from controller.health_controller import router as health_router
from controller.chat_controller import router as chat_router
from controller.vector_controller import router as vector_router
from services.vector.pgvector_service import VectorBootstrapService
from services.chat.chat_service import ChatService

logger = logging.getLogger(__name__)

API_PREFIX = "/api"

# 全局 ChatService 单例（由 lifespan 初始化）
_chat_service: ChatService = None


def get_chat_service() -> ChatService:
    """获取全局 ChatService 单例
    
    由 lifespan 在应用启动时初始化，确保 checkpointer 已就绪。
    
    Returns:
        ChatService: 全局聊天服务实例
    """
    return _chat_service


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _chat_service
    settings = get_settings()
    setup_logging(settings)
    
    # 初始化向量服务
    bootstrap = VectorBootstrapService()
    bootstrap.initialize()
    
    # 初始化 Checkpointer（持久执行）
    checkpointer = None
    try:
        checkpointer = await init_checkpointer()
        logger.info("Checkpointer 初始化成功")
    except Exception as e:
        logger.warning(f"Checkpointer 初始化失败，降级为 MemorySaver: {e}")
        checkpointer = await init_checkpointer()  # init_checkpointer 内部已有 MemorySaver 回退
    
    # 创建全局 ChatService（注入 checkpointer）
    _chat_service = ChatService(checkpointer=checkpointer)
    logger.info("ChatService 初始化完成（已注入 checkpointer）")
    
    yield
    
    # 优雅关闭：关闭 checkpointer 连接池
    await close_checkpointer()
    logger.info("Checkpointer 已关闭")


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
