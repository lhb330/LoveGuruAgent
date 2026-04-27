"""聊天控制器

提供聊天相关的HTTP接口，包括发送消息、查询历史、清空会话等。
负责参数接收、调用业务层、返回响应。

LangGraph五大核心功能集成：
- 持久执行：/send 和 /send-stream 携带 thread_id 实现断点续传
- 人工参与：/approve 接口用于敏感词拦截后的人工审批
- 生产部署：/resume 接口用于断点续传恢复
"""
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json
from pydantic import BaseModel, Field

from common.ApiResult import ApiResult
from services.chat.chat_service import ChatRequest, ChatService

# 创建路由器
router = APIRouter()
logger = logging.getLogger(__name__)


class ApproveRequest(BaseModel):
    """人工审批请求模型
    
    Attributes:
        conversation_id: 会话ID
        approved: 是否审批通过
        override_reply: 人工指定的回复内容（可选）
    """
    conversation_id: str = Field(..., description="会话ID")
    approved: bool = Field(..., description="是否审批通过")
    override_reply: str = Field(None, description="人工指定的回复内容（可选）")


def _get_service() -> ChatService:
    """获取全局 ChatService（从 main 注入，延迟导入避免循环引用）"""
    from main import get_chat_service
    return get_chat_service()


@router.get("/new-conversation-id")
def get_new_conversation_id(service: ChatService = Depends(_get_service)):
    """获取新的会话ID"""
    try:
        conversation_id = service.get_conv_id()
        return ApiResult.ok({"conversation_id": conversation_id})
    except Exception as e:
        logger.error(f"获取新会话ID失败: error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"获取新会话ID失败: {str(e)}")

@router.post("/send")
def send_message(request: ChatRequest, service: ChatService = Depends(_get_service)):
    try:
        return ApiResult.ok(service.chat(request))
    except Exception as e:
        logger.error(f"发送消息失败: conversation_id={request.conversation_id}, error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"发送消息失败: {str(e)}")

@router.post("/send-stream")
async def send_message_stream(request: ChatRequest, service: ChatService = Depends(_get_service)):
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
def get_all_history(service: ChatService = Depends(_get_service)):
    """获取所有聊天历史接口"""
    try:
        return ApiResult.ok(service.historyAllMessage())
    except Exception as e:
        logger.error(f"获取所有历史记录失败: error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"获取所有历史记录失败: {str(e)}")


@router.get("/history/grouped")
def get_grouped_history(service: ChatService = Depends(_get_service)):
    """获取会话的聊天历史分组"""
    try:
        return ApiResult.ok(service.get_conversation_groups())
    except Exception as e:
        logger.error(f"获取分组历史记录失败: error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"获取分组历史记录失败: {str(e)}")


@router.get("/history/{conversation_id}")
def get_history(conversation_id: str, service: ChatService = Depends(_get_service)):
    """获取指定会话的聊天历史"""
    try:
        return ApiResult.ok(service.history(conversation_id))
    except Exception as e:
        logger.error(f"获取历史记录失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"获取历史记录失败: {str(e)}")


@router.delete("/{conversation_id}")
def clear_history(conversation_id: str, service: ChatService = Depends(_get_service)):
    """清空指定会话的聊天历史"""
    try:
        return ApiResult.ok(service.clear(conversation_id))
    except Exception as e:
        logger.error(f"清空历史记录失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"清空历史记录失败: {str(e)}")


# ===================== 【人工参与：审批恢复接口】 =====================
@router.post("/approve")
def approve_message(request: ApproveRequest, service: ChatService = Depends(_get_service)):
    """人工审批接口
    
    对被敏感词拦截的消息进行人工审批：
    - 审批通过：恢复图执行，继续生成回复
    - 审批拒绝：返回预设的安全回复
    - 覆盖回复：审批者可以直接指定回复内容
    """
    try:
        result = service.approve_message(
            conversation_id=request.conversation_id,
            approved=request.approved,
            override_reply=request.override_reply,
        )
        return ApiResult.ok(result)
    except Exception as e:
        logger.error(f"审批处理失败: conversation_id={request.conversation_id}, error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"审批处理失败: {str(e)}")


# ===================== 【生产部署：断点续传恢复接口】 =====================
@router.post("/resume/{conversation_id}")
def resume_conversation(conversation_id: str, service: ChatService = Depends(_get_service)):
    """断点续传恢复接口
    
    基于 thread_id（conversation_id）恢复因异常中断的对话。
    LangGraph 的 checkpointer 会自动从最后保存的状态继续执行。
    """
    try:
        result = service.resume_conversation(conversation_id)
        return ApiResult.ok(result)
    except Exception as e:
        logger.error(f"断点续传恢复失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
        return ApiResult.fail(msg=f"断点续传恢复失败: {str(e)}")
