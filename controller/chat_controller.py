"""聊天控制器

提供聊天相关的HTTP接口，包括发送消息、查询历史、清空会话等。
负责参数接收、调用业务层、返回响应。
"""
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json

from common.ApiResult import ApiResult
from services.chat.chat_service import ChatRequest, ChatService

# 创建路由器
router = APIRouter()
logger = logging.getLogger(__name__)


def get_chat_service() -> ChatService:
    return ChatService()


@router.get("/new-conversation-id")
def get_new_conversation_id(service: ChatService = Depends(get_chat_service)):
    """获取新的会话ID"""
    try:
        conversation_id = service.get_conv_id()
        return ApiResult.ok({"conversation_id": conversation_id})
    except Exception as e:
        logger.error(f"获取新会话ID失败: error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"获取新会话ID失败: {str(e)}")

@router.post("/send")
def send_message(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    try:
        return ApiResult.ok(service.chat(request))
    except Exception as e:
        logger.error(f"发送消息失败: conversation_id={request.conversation_id}, error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"发送消息失败: {str(e)}")

@router.post("/send-stream")
async def send_message_stream(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    try:
        return StreamingResponse(
            service.chat_stream(request),
            media_type="text/event-stream; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    except Exception as e:
        logger.error(f"流式发送失败: conversation_id={request.conversation_id}, error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"流式发送失败: {str(e)}")


@router.get("/history/all")
def get_all_history(service: ChatService = Depends(get_chat_service)):
    """获取所有聊天历史接口"""
    try:
        return ApiResult.ok(service.historyAllMessage())
    except Exception as e:
        logger.error(f"获取所有历史记录失败: error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"获取所有历史记录失败: {str(e)}")


@router.get("/history/grouped")
def get_grouped_history(service: ChatService = Depends(get_chat_service)):
    """获取会话的聊天历史分组"""
    try:
        return ApiResult.ok(service.get_conversation_groups())
    except Exception as e:
        logger.error(f"获取分组历史记录失败: error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"获取分组历史记录失败: {str(e)}")


@router.get("/history/{conversation_id}")
def get_history(conversation_id: str, service: ChatService = Depends(get_chat_service)):
    """获取指定会话的聊天历史"""
    try:
        return ApiResult.ok(service.history(conversation_id))
    except Exception as e:
        logger.error(f"获取历史记录失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"获取历史记录失败: {str(e)}")


@router.delete("/{conversation_id}")
def clear_history(conversation_id: str, service: ChatService = Depends(get_chat_service)):
    """清空指定会话的聊天历史"""
    try:
        return ApiResult.ok(service.clear(conversation_id))
    except Exception as e:
        logger.error(f"清空历史记录失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"清空历史记录失败: {str(e)}")



