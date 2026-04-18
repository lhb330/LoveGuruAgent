from collections.abc import Generator
import json

from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import TypeDecorator

from config.settings import get_settings

settings = get_settings()


class ChineseJSON(TypeDecorator):
    """自定义 JSON 类型，支持中文字符直接存储（不转义为 Unicode）"""
    impl = None  # 使用数据库默认的 JSON 类型
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # 使用 ensure_ascii=False 保持中文字符
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)


class Base(DeclarativeBase):
    """Base ORM model."""


engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db_session() -> Generator:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def vector_column() -> Vector:
    return Vector(settings.vector_dimension)
