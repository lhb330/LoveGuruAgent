"""健康检查控制器

提供应用健康检查和测试接口。
用于监控应用运行状态和测试异常处理机制。
"""
import logging

from fastapi import APIRouter

from common.ApiResult import ApiResult
from common.ErrorCode import ErrorCode

logger = logging.getLogger(__name__)

# 创建路由路由器
router = APIRouter()


@router.get("/")
async def health_check():
    """基础健康检查接口
    
    用于检测应用是否正常运行。
    
    Returns:
        ApiResult: 包含"Hello world"的成功响应
        
    Example:
        >>> GET /api/v1/health/
        {"code": 0, "msg": "success", "data": "Hello world"}
    """
    return ApiResult.ok("Hello world")


@router.get("/div")
async def say_div():
    """除零错误测试接口
    
    用于测试异常处理机制是否正常工作。
    故意触发除零异常，验证异常处理器能否正确捕获并返回错误响应。
    
    Returns:
        ApiResult: 成功时返回计算结果，失败时返回错误信息
        
    Note:
        此接口主要用于开发测试，生产环境应该移除
    """
    try:
        num = 1 / 0
        return ApiResult.ok(num)
    except Exception as exc:
        logger.exception("Health check '/div' failed")
        return ApiResult.fail(msg=f"除零错误：{exc}", code=ErrorCode.SYSTEM_ERROR.get_code())
