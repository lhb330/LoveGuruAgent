import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from common.ApiResult import ApiResult
from common.ErrorCode import ErrorCode

logger = logging.getLogger(__name__)


class BusinessException(Exception):
    def __init__(self, message: str, code: int = ErrorCode.BUSINESS.get_code()):
        self.message = message
        self.code = code
        super().__init__(message)


class LLMInvokeException(BusinessException):
    def __init__(self, message: str = "AI service invocation failed"):
        msg = message or ErrorCode.LLM_CALL_ERROR.get_msg()
        super().__init__(message=msg, code=ErrorCode.LLM_CALL_ERROR.get_code())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def handle_business_exception(request: Request, exc: BusinessException) -> JSONResponse:
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
