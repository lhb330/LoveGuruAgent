from config.database import SessionLocal
from dao.knowledge_embedding_dao import KnowledgeEmbeddingDAO
from services.llm.factory import get_llm_service


class RAGService:
    def __init__(self) -> None:
        self.llm_service = get_llm_service()

    def retrieve(self, question: str, top_k: int = 3) -> list[dict]:
        embedding = self.llm_service.embed_text(question)
        with SessionLocal() as session:
            dao = KnowledgeEmbeddingDAO(session)
            rows = dao.similarity_search(embedding, limit=top_k)
            return [
                {
                    "doc_name": row.doc_name,
                    "content": row.content,
                    "metadata": row.metadata_json or {},
                }
                for row in rows
            ]
