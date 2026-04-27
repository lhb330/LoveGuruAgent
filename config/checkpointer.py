# 初始化 PostgreSQL Checkpointer，用于 LangGraph 状态持久化

import logging
from typing import Optional

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.memory import MemorySaver

from config.settings import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

_checkpointer: Optional[AsyncPostgresSaver] = None
_pool: Optional[AsyncConnectionPool] = None


async def init_checkpointer() -> AsyncPostgresSaver:
    """初始化 PostgreSQL Checkpointer，用于 LangGraph 状态持久化"""
    global _checkpointer, _pool

    if not settings.enable_checkpointer:
        logger.info("Checkpointer disabled, using MemorySaver fallback")
        _checkpointer = MemorySaver()
        return _checkpointer

    db_uri = settings.checkpointer_uri
    logger.info(f"Initializing AsyncPostgresSaver with URI: {db_uri[:50]}...")

    _pool = AsyncConnectionPool(
        conninfo=db_uri,
        max_size=20,
        min_size=2,
        timeout=30,  # 获取连接超时30秒
        max_lifetime=3600,  # 连接最大存活1小时
        max_idle=300,  # 空闲5分钟后回收
        kwargs={"autocommit": True},# CREATE INDEX CONCURRENTLY 需要在 autocommit 模式下执行
    )
    await _pool.open()  # 显式打开连接池
    _checkpointer = AsyncPostgresSaver(_pool)
    # 自动创建 LangGraph 检查点表（langgraph 自动命名为 checkpoint_*, write_*, 等）
    await _checkpointer.setup()
    logger.info("AsyncPostgresSaver initialized successfully")
    return _checkpointer


async def get_checkpointer() -> AsyncPostgresSaver:
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = await init_checkpointer()
    return _checkpointer



async def close_checkpointer():
    global _checkpointer, _pool
    try:
        if _pool:
            await _pool.close()
            logger.info("Checkpointer connection pool closed")
    except Exception as e:
        logger.warning(f"Error closing checkpointer pool: {e}")
    finally:
        _checkpointer = None
        _pool = None