from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from entity.chat_message import ChatMessage
from .base_dao import BaseDAO


class ChatMessageDAO(BaseDAO):
    def __init__(self, session: Session):
        super().__init__(session)

    def save_message(
        self,
        conversation_id: str,
        message_type: str,
        content: str,
        role: str,
    ) -> ChatMessage:
        message = ChatMessage(
            conversation_id=conversation_id,
            message_type=message_type,
            content=content,
            role=role,
        )
        self.session.add(message)
        self.flush()
        return message

    def bulk_save_messages(self, messages: list[dict]) -> int:
        if not messages:
            return 0

        entities = [ChatMessage(**msg) for msg in messages]
        self.session.add_all(entities)
        self.flush()
        return len(entities)

    def list_messages(self, conversation_id: str) -> Sequence[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.create_time.asc(), ChatMessage.id.asc())
        )
        return self.session.execute(stmt).scalars().all()

    def clear_messages(self, conversation_id: str) -> int:
        stmt = delete(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
        result = self.session.execute(stmt)
        return result.rowcount or 0
