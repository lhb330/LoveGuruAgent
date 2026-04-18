"""聊天消息数据访问层

提供ChatMessage实体的数据库操作方法，包括保存、查询、删除等。
"""
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from entity.chat_message import ChatMessage
from .base_dao import BaseDAO


class ChatMessageDAO(BaseDAO):
    """聊天消息数据访问对象
    
    封装对t_ai_chat_message表的所有数据库操作。
    
    Attributes:
        session: SQLAlchemy数据库会话对象（继承自BaseDAO）
    """
    
    def __init__(self, session: Session):
        """初始化聊天消息DAO
        
        Args:
            session: SQLAlchemy数据库会话对象
        """
        super().__init__(session)

    def save_message(
        self,
        conversation_id: str,
        message_type: str,
        content: str,
        role: str,
    ) -> ChatMessage:
        """保存单条聊天消息
        
        Args:
            conversation_id: 会话ID
            message_type: 消息类型
            content: 消息内容
            role: 消息角色(user/assistant)
            
        Returns:
            ChatMessage: 保存后的消息对象（包含自增ID）
        """
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
        """批量保存聊天消息
        
        Args:
            messages: 消息字典列表，每个字典包含消息字段
            
        Returns:
            int: 实际保存的消息数量
        """
        if not messages:
            return 0

        entities = [ChatMessage(**msg) for msg in messages]
        self.session.add_all(entities)
        self.flush()
        return len(entities)

    def list_messages(self, conversation_id: str) -> Sequence[ChatMessage]:
        """查询指定会话的所有消息
        
        按创建时间和ID升序排列，确保消息顺序正确。
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            Sequence[ChatMessage]: 消息对象列表
        """
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.create_time.asc(), ChatMessage.id.asc())
        )
        return self.session.execute(stmt).scalars().all()

    def clear_messages(self, conversation_id: str) -> int:
        """清空指定会话的所有消息
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            int: 删除的消息数量
        """
        stmt = delete(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
        result = self.session.execute(stmt)
        return result.rowcount or 0
