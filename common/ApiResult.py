"""统一API响应结果封装

提供标准化的API响应格式，包含code（状态码）、msg（消息）、data（数据）三个字段。
支持泛型，可以指定data的具体类型。
"""
from pydantic import BaseModel
from typing import Optional, TypeVar, Generic
from common.ErrorCode import ErrorCode

# 定义泛型类型变量，用于支持不同类型的响应数据
T = TypeVar('T')


class ApiResult(BaseModel, Generic[T]):
    """统一的API响应结果模型
    
    所有API接口都使用此模型返回数据，确保响应格式一致。
    支持泛型，data字段可以是任意类型。
    
    Attributes:
        code: 业务状态码，0表示成功，非0表示失败
        msg: 响应消息，成功时为"success"，失败时为错误描述
        data: 响应数据，可以是任意类型，成功时返回实际数据，失败时为None
    """
    code: int
    msg: str
    data: Optional[T] = None

    @staticmethod
    def ok(data: Optional[T] = None) -> "ApiResult[T]":
        """创建成功的响应结果
        
        Args:
            data: 要返回的业务数据，可选
            
        Returns:
            ApiResult: 状态码为0的成功响应对象
            
        Example:
            >>> ApiResult.ok({"user_id": 123})
            ApiResult(code=0, msg="success", data={"user_id": 123})
        """
        return ApiResult(
            code=ErrorCode.SUCCESS.get_code(),
            msg=ErrorCode.SUCCESS.get_msg(),
            data=data
        )

    @staticmethod
    def fail(msg: str, code: int = ErrorCode.SYSTEM_ERROR.get_code()) -> "ApiResult[T]":
        """创建失败的响应结果
        
        Args:
            msg: 错误消息描述
            code: 错误状态码，默认为系统错误码
            
        Returns:
            ApiResult: 包含错误信息的失败响应对象
            
        Example:
            >>> ApiResult.fail("参数错误", code=400)
            ApiResult(code=400, msg="参数错误", data=None)
        """
        return ApiResult(code=code, msg=msg)