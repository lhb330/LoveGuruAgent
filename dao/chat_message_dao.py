"""聊天消息数据访问层

提供ChatMessage实体的数据库操作方法，包括保存、查询、删除等。
"""
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
        """保存单条聊天消息"""
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
        """批量保存聊天消息"""
        if not messages:
            return 0

        entities = [ChatMessage(**msg) for msg in messages]
        self.session.add_all(entities)
        self.flush()
        return len(entities)

    def list_messages(self, conversation_id: str) -> Sequence[ChatMessage]:
        """查询指定会话的所有消息,按创建时间和ID升序排列，确保消息顺序正确。"""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.create_time.asc(), ChatMessage.id.asc())
        )
        return self.session.execute(stmt).scalars().all()

    def list_all_messages(self) -> Sequence[ChatMessage]:
        """查询所有会话"""
        stmt = (
            select(ChatMessage)
            .order_by(ChatMessage.create_time.desc())
        )
        return self.session.execute(stmt).scalars().all()

    def list_count(self) -> int:
        count = len(self.list_all_messages())
        return count

    def max_seq(self) -> int:
        count = self.list_count()
        return count + 1 if count > 0 else 1

    def clear_messages(self, conversation_id: str) -> int:
        """删除会话"""
        stmt = delete(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
        result = self.session.execute(stmt)
        return result.rowcount or 0

    def list_grouped_by_conversation(self) -> list[dict]:
        """
        按conversation_id分组查询消息，以role=user为准,
        将相同conversation_id的消息合并成一条记录，
        以role=user的消息内容作为该对话的代表内容。
        """
        stmt = (
            select(
                ChatMessage.conversation_id,
                ChatMessage.role,
                ChatMessage.content,
                ChatMessage.create_time
            )
            .order_by(
                ChatMessage.conversation_id.asc(),
                ChatMessage.create_time.asc(),
                ChatMessage.id.asc()
            )
        )
        
        results = self.session.execute(stmt).all()
        
        # 按conversation_id分组处理
        conversation_map = {}
        
        for row in results:
            conv_id = row.conversation_id
            
            if conv_id not in conversation_map:
                conversation_map[conv_id] = {
                    'conversation_id': conv_id,
                    'user_messages': [],
                    'assistant_messages': [],
                    'latest_user_time': None,
                    'total_count': 0
                }
            
            conversation_map[conv_id]['total_count'] += 1
            
            if row.role == 'user':
                conversation_map[conv_id]['user_messages'].append({
                    'content': row.content,
                    'create_time': row.create_time
                })
                # 更新最新的user消息时间
                if (conversation_map[conv_id]['latest_user_time'] is None or 
                    row.create_time > conversation_map[conv_id]['latest_user_time']):
                    conversation_map[conv_id]['latest_user_time'] = row.create_time
            else:
                conversation_map[conv_id]['assistant_messages'].append({
                    'content': row.content,
                    'create_time': row.create_time
                })
        
        # 构建返回结果，以最新的user消息为准
        result = []
        for conv_id, data in conversation_map.items():
            # 以最后一条user消息的内容为准
            user_content = ''
            if data['user_messages']:
                user_content = data['user_messages'][-1]['content']
            
            result.append({
                'conversation_id': conv_id,
                'user_content': user_content,
                'create_time': data['latest_user_time'].isoformat() if data['latest_user_time'] else None,
                'message_count': data['total_count']
            })
        
        # 按时间降序排列
        result.sort(key=lambda x: x['create_time'] or '', reverse=True)
        
        return result
