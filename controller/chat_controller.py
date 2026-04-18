from fastapi import APIRouter, Depends

from common.ApiResult import ApiResult
from services.chat.chat_service import ChatRequest, ChatService

router = APIRouter()


def get_chat_service() -> ChatService:
    return ChatService()


@router.post("/send")
def send_message(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    return ApiResult.ok(service.chat(request))


@router.get("/history/{conversation_id}")
def get_history(conversation_id: str, service: ChatService = Depends(get_chat_service)):
    return ApiResult.ok(service.history(conversation_id))


@router.delete("/{conversation_id}")
def clear_history(conversation_id: str, service: ChatService = Depends(get_chat_service)):
    return ApiResult.ok(service.clear(conversation_id))
