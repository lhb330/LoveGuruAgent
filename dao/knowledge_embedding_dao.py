from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from entity.knowledge_embedding import KnowledgeEmbedding
from .base_dao import BaseDAO


class KnowledgeEmbeddingDAO(BaseDAO):
    def __init__(self, session: Session):
        super().__init__(session)
    # 判断表中是否有数据
    def has_data(self) -> bool:
        stmt = select(KnowledgeEmbedding.id).limit(1)
        return self.session.scalar(stmt) is not None

    def list_docs(self) -> Sequence[KnowledgeEmbedding]:
        stmt = select(KnowledgeEmbedding).order_by(KnowledgeEmbedding.id.asc())
        return self.session.execute(stmt).scalars().all()

    def delete_all(self) -> int:
        result = self.session.execute(delete(KnowledgeEmbedding))
        return result.rowcount or 0

    """单个保存"""
    def save_embedding(
        self,
        doc_name: str,
        content: str,
        metadata: dict,
        embedding: list[float],
    ) -> KnowledgeEmbedding:
        row = KnowledgeEmbedding(
            doc_name=doc_name,
            content=content,
            metadata_json=metadata,
            embedding=embedding,
        )
        self.session.add(row)
        self.flush()
        return row

    def similarity_search(self, query_embedding: list[float], limit: int = 3) -> Sequence[KnowledgeEmbedding]:
        stmt = (
            select(KnowledgeEmbedding)
            .order_by(KnowledgeEmbedding.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()
