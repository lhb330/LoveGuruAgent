"""DAO基类模块

提供数据访问对象(DAO)的基类，封装SQLAlchemy会话管理。
所有DAO类都继承此类，共享数据库会话和基础操作方法。
"""
from sqlalchemy.orm import Session


class BaseDAO:
    def __init__(self, session: Session):
        self.session = session

    def flush(self) -> None:
        """刷新会话，将变更发送到数据库但不提交
        用于在执行多个操作后统一提交，或者获取自增ID等场景。
        flush会将SQL语句发送到数据库，但事务还未提交。
        """
        self.session.flush()

    def rollback(self) -> None:
        self.session.rollback()
