"""健康检查控制器

提供应用健康检查和测试接口。
用于监控应用运行状态和测试异常处理机制。

生产部署检查项：
- / : 基础健康检查
- /ready : 就绪检查（含 checkpointer 连通性）
- /div : 异常处理测试
"""
import logging

from fastapi import APIRouter
from sqlalchemy import select

from common.ApiResult import ApiResult
from common.ErrorCode import ErrorCode

logger = logging.getLogger(__name__)

# 创建路由路由器
router = APIRouter()


@router.get("/")
async def health_check():
    """基础健康检查"""
    return ApiResult.ok("Hello world")


@router.get("/ready")
async def readiness_check():
    """就绪检查 - 检查所有关键依赖是否就绪
    
    检查项：
    - 数据库连接
    - Checkpointer 状态
    - LLM 服务可用性
    """
    checks = {
        "database": "unknown",
        "checkpointer": "unknown",
        "llm": "unknown",
    }
    
    # 1. 检查数据库连接
    try:
        from config.database import engine
        with engine.connect() as conn:
            conn.execute(select(1))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
        logger.warning(f"数据库健康检查失败: {e}")
    
    # 2. 检查 Checkpointer 状态
    try:
        from main import get_chat_service
        service = get_chat_service()
        if service and service.checkpointer:
            checks["checkpointer"] = "healthy"
        elif service and not service.checkpointer:
            checks["checkpointer"] = "disabled"
        else:
            checks["checkpointer"] = "not_initialized"
    except Exception as e:
        checks["checkpointer"] = f"error: {str(e)}"
        logger.warning(f"Checkpointer 健康检查失败: {e}")
    
    # 3. 检查 LLM 服务可用性
    try:
        from services.llm.factory import get_llm_service
        llm = get_llm_service()
        if llm:
            checks["llm"] = "healthy"
        else:
            checks["llm"] = "not_initialized"
    except Exception as e:
        checks["llm"] = f"error: {str(e)}"
        logger.warning(f"LLM 健康检查失败: {e}")
    
    # 判断整体状态
    all_healthy = all(v == "healthy" or v == "disabled" for v in checks.values())
    
    return ApiResult.ok({
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
    })


@router.get("/div")
async def say_div():
    try:
        num = 1 / 0
        return ApiResult.ok(num)
    except Exception as exc:
        logger.exception("Health check '/div' failed")
        return ApiResult.fail(msg=f"除零错误：{exc}", code=ErrorCode.SYSTEM_ERROR.get_code())
