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
    return ApiResult.ok("Hello world")


@router.get("/div")
async def say_div():
    try:
        num = 1 / 0
        return ApiResult.ok(num)
    except Exception as exc:
        logger.exception("Health check '/div' failed")
        return ApiResult.fail(msg=f"除零错误：{exc}", code=ErrorCode.SYSTEM_ERROR.get_code())
