"""数据库配置和连接管理模块

提供SQLAlchemy引擎、会话管理、自定义类型等数据库基础设施。
支持pgvector向量存储和中文JSON直接存储。
"""
from collections.abc import Generator
import json

from pgvector.sqlalchemy import Vector
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import TypeDecorator

from config.settings import get_settings

settings = get_settings()


class ChineseJSON(TypeDecorator):
    """自定义JSON类型装饰器，支持中文字符直接存储
    
    默认的JSON类型会将中文字符转义为Unicode（如"\u4e2d\u6587"），
    此类型确保中文字符以原始形式存储在数据库中。
    
    Attributes:
        impl: 使用数据库默认的JSON类型
        cache_ok: 标记此类型是否可以安全缓存
    """
    impl = None  # 使用数据库默认的 JSON 类型
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """将Python对象转换为数据库存储格式
        
        Args:
            value: Python对象（dict、list等）
            dialect: 数据库方言
            
        Returns:
            str: JSON格式字符串，中文字符不转义
        """
        if value is None:
            return None
        # 使用 ensure_ascii=False 保持中文字符
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        """将数据库存储格式转换为Python对象
        
        Args:
            value: 数据库中的JSON字符串或对象
            dialect: 数据库方言
            
        Returns:
            dict/list: 解析后的Python对象
        """
        if value is None:
            return None
        # 如果已经是 dict 或 list 对象，直接返回
        if isinstance(value, (dict, list)):
            return value
        # 否则从 JSON 字符串解析
        return json.loads(value)


class Base(DeclarativeBase):
    """ORM模型基类
    
    所有数据库实体模型都应继承此类。
    提供表映射、列定义等ORM基础功能。
    """
    pass


# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    future=True,
    pool_pre_ping=True,  # 连接前检查连接是否有效
)

# 创建会话工厂
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db_session() -> Generator:
    """获取数据库会话（依赖注入用）
    
    生成器函数，用于FastAPI的依赖注入。
    确保会话在使用后被正确关闭，即使发生异常。
    
    Yields:
        Session: SQLAlchemy数据库会话对象
        
    Example:
        >>> @app.get("/users")
        ... def get_users(db: Session = Depends(get_db_session)):
        ...     return db.query(User).all()
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def vector_column() -> Vector:
    """创建向量列定义
    
    根据配置中的向量维度创建pgvector向量列。
    用于存储embedding模型生成的向量数据。
    
    Returns:
        Vector: pgvector向量列对象
        
    Example:
        >>> class KnowledgeEmbedding(Base):
        ...     embedding = Column(vector_column())
    """
    return Vector(settings.vector_dimension)
