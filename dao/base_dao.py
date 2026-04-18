from sqlalchemy.orm import Session


class BaseDAO:
    """DAO base class that shares a SQLAlchemy session."""

    def __init__(self, session: Session):
        self.session = session

    def flush(self) -> None:
        self.session.flush()

    def rollback(self) -> None:
        self.session.rollback()
