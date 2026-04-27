"""用户长期记忆数据访问层

提供 UserMemory 实体的数据库操作方法，包括记忆的存储、检索、更新和淘汰。
"""
from collections.abc import Sequence
from typing import Optional

from sqlalchemy import delete, select, update, func
from sqlalchemy.orm import Session

from entity.user_memory import UserMemory
from .base_dao import BaseDAO


class UserMemoryDAO(BaseDAO):
    """用户长期记忆 DAO

    提供长期记忆的 CRUD 操作：
    - 按 user_id 检索所有记忆
    - 按 user_id + memory_key 查询/更新特定记忆
    - 记忆淘汰（按重要度和时间）
    - 按相关性检索记忆（简单关键词匹配）
    """

    def __init__(self, session: Session):
        super().__init__(session)

    def save_memory(
        self,
        user_id: str,
        memory_key: str,
        memory_value: str,
        importance: float = 0.5,
        source_conversation_id: Optional[str] = None,
    ) -> UserMemory:
        """保存或更新一条记忆

        如果 user_id + memory_key 已存在，则更新记忆内容和重要度；
        否则创建新记忆。

        Args:
            user_id: 用户标识
            memory_key: 记忆类别/标识
            memory_value: 记忆内容
            importance: 重要度评分（0.0~1.0）
            source_conversation_id: 来源会话ID

        Returns:
            UserMemory: 保存/更新后的记忆实体
        """
        # 先查找是否已存在
        stmt = select(UserMemory).where(
            UserMemory.user_id == user_id,
            UserMemory.memory_key == memory_key,
        )
        existing = self.session.execute(stmt).scalars().first()

        if existing:
            # 更新已有记忆（提高重要度取最大值）
            existing.memory_value = memory_value
            existing.importance = max(existing.importance, importance)
            existing.source_conversation_id = source_conversation_id
            self.flush()
            return existing

        # 创建新记忆
        memory = UserMemory(
            user_id=user_id,
            memory_key=memory_key,
            memory_value=memory_value,
            importance=importance,
            source_conversation_id=source_conversation_id,
        )
        self.session.add(memory)
        self.flush()
        return memory

    def get_memories_by_user(
        self, user_id: str, min_importance: float = 0.0, limit: int = 50
    ) -> Sequence[UserMemory]:
        """获取用户的所有长期记忆

        Args:
            user_id: 用户标识
            min_importance: 最低重要度过滤
            limit: 最大返回条数

        Returns:
            Sequence[UserMemory]: 记忆列表，按重要度降序排列
        """
        stmt = (
            select(UserMemory)
            .where(
                UserMemory.user_id == user_id,
                UserMemory.importance >= min_importance,
            )
            .order_by(UserMemory.importance.desc(), UserMemory.update_time.desc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def get_memory_by_key(self, user_id: str, memory_key: str) -> Optional[UserMemory]:
        """按 key 查询特定记忆

        Args:
            user_id: 用户标识
            memory_key: 记忆类别/标识

        Returns:
            Optional[UserMemory]: 记忆实体，不存在则返回 None
        """
        stmt = select(UserMemory).where(
            UserMemory.user_id == user_id,
            UserMemory.memory_key == memory_key,
        )
        return self.session.execute(stmt).scalars().first()

    def search_memories(self, user_id: str, query: str, limit: int = 10) -> Sequence[UserMemory]:
        """按关键词检索用户记忆（简单文本匹配）

        Args:
            user_id: 用户标识
            query: 检索关键词
            limit: 最大返回条数

        Returns:
            Sequence[UserMemory]: 匹配的记忆列表
        """
        stmt = (
            select(UserMemory)
            .where(
                UserMemory.user_id == user_id,
                UserMemory.memory_value.contains(query),
            )
            .order_by(UserMemory.importance.desc())
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()

    def delete_memory(self, user_id: str, memory_key: str) -> bool:
        """删除指定记忆

        Args:
            user_id: 用户标识
            memory_key: 记忆类别/标识

        Returns:
            bool: 是否删除成功
        """
        stmt = delete(UserMemory).where(
            UserMemory.user_id == user_id,
            UserMemory.memory_key == memory_key,
        )
        result = self.session.execute(stmt)
        return result.rowcount > 0

    def evict_low_importance(self, user_id: str, max_entries: int = 100) -> int:
        """淘汰低重要度记忆

        当用户记忆数超过 max_entries 时，删除重要度最低的旧记忆。

        Args:
            user_id: 用户标识
            max_entries: 最大保留记忆数

        Returns:
            int: 被淘汰的记忆数量
        """
        # 获取当前记忆总数
        count_stmt = select(func.count()).where(UserMemory.user_id == user_id)
        total = self.session.execute(count_stmt).scalar()

        if total <= max_entries:
            return 0

        # 需要淘汰的数量
        to_remove = total - max_entries

        # 按重要度升序 + 时间升序，淘汰最不重要的旧记忆
        subquery = (
            select(UserMemory.id)
            .where(UserMemory.user_id == user_id)
            .order_by(UserMemory.importance.asc(), UserMemory.update_time.asc())
            .limit(to_remove)
            .subquery()
        )

        delete_stmt = delete(UserMemory).where(UserMemory.id.in_(subquery))
        result = self.session.execute(delete_stmt)
        return result.rowcount or 0
