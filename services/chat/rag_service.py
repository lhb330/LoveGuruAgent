"""RAG检索服务模块

提供基于检索增强生成(RAG)的知识库查询功能。
将用户问题转换为向量，然后在向量数据库中进行相似度检索。
"""
from config.database import SessionLocal
from dao.knowledge_embedding_dao import KnowledgeEmbeddingDAO
from services.llm.factory import get_llm_service


class RAGService:
    """RAG检索服务类
    
    负责从知识库中检索与用户问题相关的文档。
    工作流程：
    1. 将用户问题通过embedding模型转换为向量
    2. 在pgvector中进行余弦相似度检索
    3. 返回最相似的文档列表
    
    Attributes:
        llm_service: LLM服务实例，用于调用embedding模型
    """
    
    def __init__(self) -> None:
        """初始化RAG服务
        
        获取LLM服务实例，用于后续的embedding生成。
        """
        self.llm_service = get_llm_service()

    def retrieve(self, question: str, top_k: int = 3) -> list[dict]:
        """检索与问题相关的知识库文档
        
        使用向量相似度检索，找出与用户问题最相似的top_k个文档。
        
        Args:
            question: 用户问题文本
            top_k: 返回的最相似文档数量，默认3个
            
        Returns:
            list[dict]: 相似文档列表，每个文档包含doc_name、content、metadata
            
        Example:
            >>> rag = RAGService()
            >>> results = rag.retrieve("如何表白", top_k=2)
            [{'doc_name': '恋爱筒.md', 'content': '...', 'metadata': {...}}]
        """
        # 将问题转换为向量
        embedding = self.llm_service.embed_text(question)
        
        # 在数据库中检索相似向量
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
