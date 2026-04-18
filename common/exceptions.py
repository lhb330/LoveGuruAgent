"""全局异常定义和处理机制

定义了项目中使用的所有自定义异常类，并提供全局异常处理器。
所有异常都会被捕获并转换为统一的ApiResult格式返回给前端。
"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common.ApiResult import ApiResult
from common.ErrorCode import ErrorCode

logger = logging.getLogger(__name__)


class BusinessException(Exception):
    """业务异常基类
    
    所有业务逻辑中的异常都应该继承此类，用于表示可预期的业务错误。
    例如：参数校验失败、资源不存在、权限不足等。
    
    Attributes:
        message: 错误消息描述
        code: 错误状态码，默认为业务错误码
    """
    def __init__(self, message: str, code: int = ErrorCode.BUSINESS.get_code()):
        """初始化业务异常
        
        Args:
            message: 错误消息描述
            code: 错误状态码，默认为业务错误码
        """
        self.message = message
        self.code = code
        super().__init__(message)


class LLMInvokeException(BusinessException):
    """大模型调用异常
    
    当调用AI大模型服务失败时抛出此异常。
    例如：API调用超时、token不足、模型服务不可用等。
    
    Attributes:
        message: 错误消息描述
        code: 错误状态码，固定为LLM调用错误码
    """
    def __init__(self, message: str = "AI service invocation failed"):
        """初始化LLM调用异常
        
        Args:
            message: 错误消息描述，如果为空则使用默认消息
        """
        msg = message or ErrorCode.LLM_CALL_ERROR.get_msg()
        super().__init__(message=msg, code=ErrorCode.LLM_CALL_ERROR.get_code())


def register_exception_handlers(app: FastAPI) -> None:
    """为FastAPI应用注册全局异常处理器
    
    注册两类异常处理器：
    1. BusinessException: 处理业务异常，返回200状态码和业务错误码
    2. Exception: 处理所有未预期的系统异常，返回500状态码
    
    Args:
        app: FastAPI应用实例
        
    Example:
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
    """
    @app.exception_handler(BusinessException)
    async def handle_business_exception(request: Request, exc: BusinessException) -> JSONResponse:
        """处理业务异常
        
        记录异常日志并返回统一的错误响应格式。
        
        Args:
            request: FastAPI请求对象
            exc: 捕获到的业务异常
            
        Returns:
            JSONResponse: 包含错误信息的JSON响应，HTTP状态码为200
        """
        logger.error(
            "[BusinessException] %s %s | code=%s | message=%s",
            request.method,
            request.url.path,
            exc.code,
            exc.message,
            exc_info=exc,
        )
        return JSONResponse(
            status_code=200,
            content=ApiResult.fail(msg=exc.message, code=exc.code).model_dump()
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        """处理未预期的系统异常
        
        记录完整的异常堆栈信息并返回系统错误响应。
        
        Args:
            request: FastAPI请求对象
            exc: 捕获到的异常对象
            
        Returns:
            JSONResponse: 包含错误信息的JSON响应，HTTP状态码为500
        """
        logger.exception(
            "[SystemException] %s %s | error=%s",
            request.method,
            request.url.path,
            str(exc)
        )
        return JSONResponse(
            status_code=500,
            content=ApiResult.fail(msg=str(exc), code=ErrorCode.SYSTEM_ERROR.get_code()).model_dump()
        )
