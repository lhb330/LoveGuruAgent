from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class ChatMessage(Base):
    __tablename__ = "t_ai_chat_message"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(nullable=False, index=True)
    message_type: Mapped[str] = mapped_column(nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(nullable=False)
    create_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
