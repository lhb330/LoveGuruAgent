from pydantic import BaseModel
from typing import Optional, TypeVar, Generic
from common.ErrorCode import ErrorCode

T = TypeVar('T')

class ApiResult(BaseModel, Generic[T]):
    code: int
    msg: str
    data: Optional[T] = None

    @staticmethod
    def ok(data: Optional[T] = None) -> "ApiResult[T]":
        return ApiResult(
            code=ErrorCode.SUCCESS.get_code(),
            msg=ErrorCode.SUCCESS.get_msg(),
            data=data
        )

    @staticmethod
    def fail(msg: str, code: int = ErrorCode.SYSTEM_ERROR.get_code()) -> "ApiResult[T]":
        return ApiResult(code=code, msg=msg)