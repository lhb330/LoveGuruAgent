"""聊天消息实体模型

定义聊天消息表的ORM映射，用于存储用户和AI的对话记录。
对应数据库表: t_ai_chat_message
"""
from datetime import datetime

from sqlalchemy import DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class ChatMessage(Base):
    """聊天消息实体类
    
    存储聊天会话中的每条消息，包括用户消息和AI回复。
    
    Attributes:
        id: 主键ID，自增
        conversation_id: 会话ID，用于关联同一会话的多条消息
        message_type: 消息类型（如text、image等）
        content: 消息内容
        role: 消息角色（user表示用户，assistant表示AI）
        create_time: 创建时间，自动设置为当前时间
    """
    __tablename__ = "t_ai_chat_message"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键ID")
    conversation_id: Mapped[str] = mapped_column(nullable=False, index=True, comment="会话ID")
    message_type: Mapped[str] = mapped_column(nullable=False, comment="消息类型")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="消息内容")
    role: Mapped[str] = mapped_column(nullable=False, comment="消息角色(user/assistant)")
    create_time: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(), 
        nullable=False, 
        comment="创建时间"
    )
