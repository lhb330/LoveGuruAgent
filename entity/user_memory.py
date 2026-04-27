"""用户长期记忆实体模型

定义用户长期记忆表的ORM映射，用于存储从对话中提取的关键事实。
对应数据库表: t_user_memory

LangGraph 全面记忆（Comprehensive Memory）功能：
- 跨会话长期记忆存储
- 对话结束后自动提取关键事实
- 下次对话开始时检索相关记忆注入 Prompt
"""
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class UserMemory(Base):
    """用户长期记忆实体类
    
    存储从用户对话中提取的关键信息，包括：
    - 用户偏好、习惯、重要经历
    - 情感状态、关系状况
    - 关键决策和里程碑事件
    
    Attributes:
        id: 主键ID，自增
        user_id: 用户标识
        memory_key: 记忆类别/标识（如 "relationship_status", "partner_name"）
        memory_value: 记忆内容
        importance: 重要度评分（0.0~1.0），用于记忆淘汰策略
        source_conversation_id: 来源会话ID，追溯记忆来源
        create_time: 创建时间
        update_time: 最后更新时间
    """
    __tablename__ = "t_user_memory"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键ID")
    user_id: Mapped[str] = mapped_column(nullable=False, index=True, comment="用户标识")
    memory_key: Mapped[str] = mapped_column(nullable=False, comment="记忆类别/标识")
    memory_value: Mapped[str] = mapped_column(Text, nullable=False, comment="记忆内容")
    importance: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.5, comment="重要度评分(0.0~1.0)"
    )
    source_conversation_id: Mapped[str | None] = mapped_column(
        nullable=True, comment="来源会话ID"
    )
    create_time: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="最后更新时间",
    )
