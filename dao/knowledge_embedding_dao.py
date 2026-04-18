"""知识库向量数据访问层

提供KnowledgeEmbedding实体的数据库操作方法，包括向量存储、相似度检索等。
"""
from collections.abc import Sequence

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from entity.knowledge_embedding import KnowledgeEmbedding
from .base_dao import BaseDAO


class KnowledgeEmbeddingDAO(BaseDAO):
    """知识库向量数据访问对象
    
    封装对t_knowledge_embedding表的所有数据库操作。
    支持向量相似度检索（余弦距离）。
    
    Attributes:
        session: SQLAlchemy数据库会话对象（继承自BaseDAO）
    """
    
    def __init__(self, session: Session):
        """初始化知识库向量DAO
        
        Args:
            session: SQLAlchemy数据库会话对象
        """
        super().__init__(session)
        
    def has_data(self) -> bool:
        """检查向量表中是否有数据
        
        Returns:
            bool: 如果表中有数据返回True，否则返回False
        """
        stmt = select(KnowledgeEmbedding.id).limit(1)
        return self.session.scalar(stmt) is not None

    def list_docs(self) -> Sequence[KnowledgeEmbedding]:
        """查询所有知识库向量记录
        
        Returns:
            Sequence[KnowledgeEmbedding]: 所有向量记录列表
        """
        stmt = select(KnowledgeEmbedding).order_by(KnowledgeEmbedding.id.asc())
        return self.session.execute(stmt).scalars().all()

    def delete_all(self) -> int:
        """删除所有知识库向量数据
        
        Returns:
            int: 删除的记录数量
        """
        result = self.session.execute(delete(KnowledgeEmbedding))
        return result.rowcount or 0

    def save_embedding(
        self,
        doc_name: str,
        content: str,
        metadata: dict,
        embedding: list[float],
    ) -> KnowledgeEmbedding:
        """保存单条向量数据
        
        Args:
            doc_name: 文档名称
            content: 文档原文内容
            metadata: 元数据字典
            embedding: 向量数据（浮点数列表）
            
        Returns:
            KnowledgeEmbedding: 保存后的向量对象
        """
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
        """向量相似度检索
        
        使用余弦距离计算相似度，距离越小表示越相似。
        
        Args:
            query_embedding: 查询向量
            limit: 返回的最大结果数量，默认3条
            
        Returns:
            Sequence[KnowledgeEmbedding]: 最相似的文档列表
        """
        stmt = (
            select(KnowledgeEmbedding)
            .order_by(KnowledgeEmbedding.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        return self.session.execute(stmt).scalars().all()
