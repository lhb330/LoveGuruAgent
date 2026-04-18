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
    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm_service = get_llm_service()

    def ensure_database(self) -> None:
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        Base.metadata.create_all(bind=engine)

    """文档切片按字符长度切 + overlap（重叠）"""
    def split_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
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
        docs = self._scan_docs()
        with SessionLocal() as session:
            dao = KnowledgeEmbeddingDAO(session)
            try:
                #dao.delete_all()
                imported = 0

                for doc_path in docs:
                    content = read_text_file(doc_path)
                    # 文件名（不带后缀）
                    filename = doc_path.stem
                    # 分类：从文件名中提取，比如“单身篇”、“已婚篇”，你可以按自己规则改
                    if "单身篇" in filename:
                        category = "单身篇"
                    elif "已婚篇" in filename:
                        category = "已婚篇"
                    else:
                        category = "恋爱篇"
                    # ✨ 切片
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
