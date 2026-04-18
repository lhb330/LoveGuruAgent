"""知识库向量实体模型

定义知识库向量表的ORM映射，用于存储文档的embedding向量。
对应数据库表: t_knowledge_embedding
"""
from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base, vector_column, ChineseJSON


class KnowledgeEmbedding(Base):
    """知识库向量实体类
    
    存储从Markdown文档生成的embedding向量，用于RAG检索。
    每个文档内容被转换为高维向量，通过余弦相似度进行检索。
    
    Attributes:
        id: 主键ID，自增
        doc_name: 文档名称，用于标识来源文档
        content: 文档原文内容
        metadata_json: 元数据信息（JSON格式），如文档路径、分段信息等
        embedding: 向量数据，由embedding模型生成，用于相似度检索
    """
    __tablename__ = "t_knowledge_embedding"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键ID")
    doc_name: Mapped[str | None] = mapped_column(nullable=True, index=True, comment="文档名称")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="文档原文内容")
    metadata_json: Mapped[dict | None] = mapped_column(
        "metadata", 
        ChineseJSON, 
        nullable=True, 
        comment="元数据(JSON)"
    )
    embedding: Mapped[list[float] | None] = mapped_column(
        vector_column(), 
        nullable=True, 
        comment="向量数据(embedding)"
    )
