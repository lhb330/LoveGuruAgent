from pydantic import BaseModel, Field

from common.constants import MessageType
from config.database import SessionLocal
from dao.chat_message_dao import ChatMessageDAO
from harness.graph_builder import build_chat_graph


class ChatRequest(BaseModel):
    conversation_id: str = Field(..., description="会话 ID")
    message: str = Field(..., description="用户消息")


class ChatService:
    def __init__(self) -> None:
        self.graph = build_chat_graph()

    def chat(self, request: ChatRequest) -> dict:
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            try:
                dao.save_message(
                    conversation_id=request.conversation_id,
                    message_type=MessageType.USER.value,
                    content=request.message,
                    role="user",
                )

                state = self.graph.invoke(
                    {
                        "conversation_id": request.conversation_id,
                        "user_message": request.message,
                    }
                )
                reply = state["assistant_reply"]

                dao.save_message(
                    conversation_id=request.conversation_id,
                    message_type=MessageType.ASSISTANT.value,
                    content=reply,
                    role="assistant",
                )
                session.commit()
            except Exception:
                session.rollback()
                raise

            return {
                "conversation_id": request.conversation_id,
                "reply": reply,
                "references": state.get("references", []),
            }

    def history(self, conversation_id: str) -> list[dict]:
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            messages = dao.list_messages(conversation_id)
            return [
                {
                    "id": item.id,
                    "conversation_id": item.conversation_id,
                    "message_type": item.message_type,
                    "role": item.role,
                    "content": item.content,
                    "create_time": item.create_time.isoformat(),
                }
                for item in messages
            ]

    def clear(self, conversation_id: str) -> dict:
        with SessionLocal() as session:
            dao = ChatMessageDAO(session)
            try:
                deleted = dao.clear_messages(conversation_id)
                session.commit()
            except Exception:
                session.rollback()
                raise
            return {"conversation_id": conversation_id, "deleted": deleted}
