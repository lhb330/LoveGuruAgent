from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base, vector_column, ChineseJSON


class KnowledgeEmbedding(Base):
    __tablename__ = "t_knowledge_embedding"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_name: Mapped[str | None] = mapped_column(nullable=True, index=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", ChineseJSON, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(vector_column(), nullable=True)
