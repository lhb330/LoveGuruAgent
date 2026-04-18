"""DAO基类模块

提供数据访问对象(DAO)的基类，封装SQLAlchemy会话管理。
所有DAO类都继承此类，共享数据库会话和基础操作方法。
"""
from sqlalchemy.orm import Session


class BaseDAO:
    """DAO基类
    
    所有数据访问对象都应该继承此类。
    提供SQLAlchemy会话管理和基础数据库操作。
    
    Attributes:
        session: SQLAlchemy数据库会话对象
    """

    def __init__(self, session: Session):
        """初始化DAO
        
        Args:
            session: SQLAlchemy数据库会话对象
        """
        self.session = session

    def flush(self) -> None:
        """刷新会话，将变更发送到数据库但不提交
        
        用于在执行多个操作后统一提交，或者获取自增ID等场景。
        flush会将SQL语句发送到数据库，但事务还未提交。
        """
        self.session.flush()

    def rollback(self) -> None:
        """回滚当前事务
        
        当发生异常或需要取消操作时调用，撤销所有未提交的变更。
        """
        self.session.rollback()
