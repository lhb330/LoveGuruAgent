"""pgvector向量服务模块

提供PostgreSQL向量数据库的管理和操作功能。
包括知识库文档导入、向量生成、数据库初始化等。
"""
import logging
from pathlib import Path

from sqlalchemy import text

from langchain_text_splitters import RecursiveCharacterTextSplitter

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
        self.settings = get_settings()
        self.llm_service = get_llm_service()


    def split_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
        """使用语义切片分割文本
        
        使用LangChain的RecursiveCharacterTextSplitter进行语义切片，
        优先在段落、句子等语义边界处分割，保持文本的完整性。
        
        Args:
            text: 要分割的文本
            chunk_size: 每个片段的最大字符数
            overlap: 相邻片段之间的重叠字符数
            
        Returns:
            分割后的文本片段列表
        """
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
            separators=[
                "\n\n",      # 段落分隔
                "\n",        # 换行
                "。", "！", "？",  # 中文句子结束符
                ".", "!", "?",   # 英文句子结束符
                "；", ";",       # 分号
                "，", ",",       # 逗号
                " ",            # 空格
                ""              # 字符级别
            ]
        )
        
        chunks = splitter.split_text(text)
        return chunks

    def rebuild_from_docs(self) -> dict:
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
        docs_dir = self.settings.knowledge_docs_path
        docs_dir.mkdir(parents=True, exist_ok=True)
        return sorted(docs_dir.glob("*.md"))


class VectorBootstrapService:
    def __init__(self) -> None:
        self.vector_service = PGVectorService()

    def vectorTableHasData(self) -> bool:
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
        """
        if self.vectorTableHasData():
            logger.info("Vector table already has data, skip bootstrap.")
            return

        try:
            self.vector_service.rebuild_from_docs()
        except LLMInvokeException as exc:
            logger.error("Vector bootstrap skipped because embedding service is unavailable: %s", exc)
        except Exception as exc:
            logger.exception("Vector bootstrap failed: %s", exc)
