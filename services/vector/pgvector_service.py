"""pgvector向量服务模块

提供PostgreSQL向量数据库的管理和操作功能。
包括知识库文档导入、向量生成、数据库初始化等。
"""
import json
import logging
from pathlib import Path

from sqlalchemy import text

from common.exceptions import LLMInvokeException
from common.utils import read_text_file
from config.database import Base, SessionLocal, engine
from config.settings import get_settings
from dao.knowledge_embedding_dao import KnowledgeEmbeddingDAO
from services.llm.factory import get_llm_service

logger = logging.getLogger(__name__)


class PGVectorService:
    """pgvector向量服务类
    
    负责管理PostgreSQL中的向量数据，包括：
    1. 数据库扩展初始化（pgvector扩展）
    2. 文档扫描和读取
    3. 文本切片（chunking）
    4. 向量生成和存储
    5. 重建向量索引
    
    Attributes:
        settings: 应用配置实例
        llm_service: LLM服务实例，用于生成embedding
    """
    
    def __init__(self) -> None:
        """初始化pgvector服务
        
        获取配置和LLM服务实例。
        """
        self.settings = get_settings()
        self.llm_service = get_llm_service()

    def ensure_database(self) -> None:
        """确保数据库扩展和表已创建
        
        创建pgvector扩展（如果不存在），并创建所有ORM定义的表。
        在应用启动时调用。
        """
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=engine)

    def split_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
        """将文本按字符长度切片，支持重叠
        
        将长文本切分为多个小块，每个小块有固定大小的重叠部分，
        确保上下文信息不丢失。
        
        Args:
            text: 要切片的原始文本
            chunk_size: 每个切片的大小（字符数），默认500
            overlap: 相邻切片的重叠大小（字符数），默认100
            
        Returns:
            list[str]: 切片后的文本列表
            
        Example:
            >>> split_text("ABCDEFG", chunk_size=3, overlap=1)
            ['ABC', 'CDE', 'EFG']
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap

        return chunks

    def rebuild_from_docs(self) -> dict:
        """从文档目录重建向量索引
        
        扫描docs目录下的所有Markdown文档，执行以下操作：
        1. 读取文档内容
        2. 按字符长度切片
        3. 为每个切片生成embedding向量
        4. 保存到数据库
        
        Returns:
            dict: 包含导入统计信息的字典
                - imported: 导入的切片数量
                - docs_dir: 文档目录路径
                
        Raises:
            Exception: 数据库操作或embedding生成失败时抛出
        """
        docs = self._scan_docs()
        with SessionLocal() as session:
            dao = KnowledgeEmbeddingDAO(session)
            try:
                #dao.delete_all()  # 可选：先清空旧数据
                imported = 0

                for doc_path in docs:
                    content = read_text_file(doc_path)
                    # 文件名（不带后缀）
                    filename = doc_path.stem
                    # 分类：从文件名中提取，如"单身篇"、"已婚篇"
                    if "单身篇" in filename:
                        category = "单身篇"
                    elif "已婚篇" in filename:
                        category = "已婚篇"
                    else:
                        category = "恋爱篇"
                    # 切片
                    chunks = self.split_text(content)
                    for idx, chunk in enumerate(chunks):
                        embedding = self.llm_service.embed_text(chunk)
                        dao.save_embedding(
                            doc_name=doc_path.name,
                            content=chunk,
                            metadata={
                                "title": filename,
                                "category": category,
                                "filename": doc_path.name
                            },
                            embedding=embedding,
                        )
                        imported += 1

                session.commit()
            except Exception:
                session.rollback()
                raise

        return {
            "imported": imported,
            "docs_dir": str(self.settings.knowledge_docs_path),
        }

    def _scan_docs(self) -> list[Path]:
        """扫描知识库目录，获取所有Markdown文件
        
        Returns:
            list[Path]: Markdown文件路径列表，按文件名排序
        """
        docs_dir = self.settings.knowledge_docs_path
        docs_dir.mkdir(parents=True, exist_ok=True)
        return sorted(docs_dir.glob("*.md"))


class VectorBootstrapService:
    """向量数据库引导服务类
    
    在应用启动时自动初始化向量数据库。
    检查向量表是否有数据，如果没有则自动导入文档。
    
    Attributes:
        vector_service: pgvector服务实例
    """
    
    def __init__(self) -> None:
        """初始化引导服务
        
        创建pgvector服务实例。
        """
        self.vector_service = PGVectorService()

    def vectorTableHasData(self) -> bool:
        """检查向量表是否已有数据
        
        Returns:
            bool: 如果表中有数据返回True，否则返回False
        """
        with SessionLocal() as session:
            dao = KnowledgeEmbeddingDAO(session)
            return dao.has_data()

    def initialize(self) -> None:
        """初始化向量数据库
        
        应用启动时的引导流程：
        1. 检查向量表是否已有数据
        2. 如果有数据，跳过初始化
        3. 如果没有数据，创建数据库扩展和表
        4. 扫描文档目录，导入所有Markdown文档
        
        Note:
            - 如果文档目录为空，跳过初始化
            - 如果embedding服务不可用，记录错误但不阻止应用启动
            - 其他异常会记录完整堆栈信息
        """
        if self.vectorTableHasData():
            logger.info("Vector table already has data, skip bootstrap.")
            return

        self.vector_service.ensure_database()
        docs = self.vector_service._scan_docs()

        if not docs:
            logger.warning("No markdown documents found in docs directory, skip vector bootstrap.")
            return

        try:
            self.vector_service.rebuild_from_docs()
        except LLMInvokeException as exc:
            logger.error("Vector bootstrap skipped because embedding service is unavailable: %s", exc)
        except Exception as exc:
            logger.exception("Vector bootstrap failed: %s", exc)
