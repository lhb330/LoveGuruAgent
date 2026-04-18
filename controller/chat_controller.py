"""聊天控制器

提供聊天相关的HTTP接口，包括发送消息、查询历史、清空会话等。
负责参数接收、调用业务层、返回响应。
"""
import logging

from fastapi import APIRouter, Depends

from common.ApiResult import ApiResult
from services.chat.chat_service import ChatRequest, ChatService

# 创建路由器
router = APIRouter()
logger = logging.getLogger(__name__)


def get_chat_service() -> ChatService:
    """创建ChatService实例（依赖注入）
    
    Returns:
        ChatService: 聊天服务实例
    """
    return ChatService()


@router.post("/send")
def send_message(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    """发送聊天消息接口
    
    接收用户消息，调用AI生成回复，并保存聊天记录。
    
    Args:
        request: 聊天请求对象，包含conversation_id和message
        service: 聊天服务实例（依赖注入）
        
    Returns:
        ApiResult: 包含conversation_id、reply、references的响应
        
    Example:
        >>> POST /api/v1/chat/send
        >>> {"conversation_id": "test-001", "message": "你好"}
        {"code": 0, "msg": "success", "data": {"conversation_id": "test-001", "reply": "你好！", "references": []}}
    """
    try:
        return ApiResult.ok(service.chat(request))
    except Exception as e:
        logger.error(f"发送消息失败: conversation_id={request.conversation_id}, error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"发送消息失败: {str(e)}")


@router.get("/history/{conversation_id}")
def get_history(conversation_id: str, service: ChatService = Depends(get_chat_service)):
    """获取聊天历史接口
    
    查询指定会话的完整聊天记录。
    
    Args:
        conversation_id: 会话ID
        service: 聊天服务实例（依赖注入）
        
    Returns:
        ApiResult: 包含聊天历史消息列表的响应
        
    Example:
        >>> GET /api/v1/chat/history/test-001
        {"code": 0, "msg": "success", "data": [{"role": "user", "message": "你好"}, ...]}
    """
    try:
        return ApiResult.ok(service.history(conversation_id))
    except Exception as e:
        logger.error(f"获取历史记录失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"获取历史记录失败: {str(e)}")


@router.delete("/{conversation_id}")
def clear_history(conversation_id: str, service: ChatService = Depends(get_chat_service)):
    """清空聊天历史接口
    
    删除指定会话的所有聊天记录。
    
    Args:
        conversation_id: 会话ID
        service: 聊天服务实例（依赖注入）
        
    Returns:
        ApiResult: 操作结果
        
    Example:
        >>> DELETE /api/v1/chat/test-001
        {"code": 0, "msg": "success", "data": null}
    """
    try:
        return ApiResult.ok(service.clear(conversation_id))
    except Exception as e:
        logger.error(f"清空历史记录失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"清空历史记录失败: {str(e)}")
