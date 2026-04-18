"""向量知识库控制器

提供知识库向量管理接口，支持重建向量索引。
用于管理文档的embedding向量数据。
"""
from fastapi import APIRouter

from common.ApiResult import ApiResult
from services.vector.pgvector_service import PGVectorService

# 创建路由器
router = APIRouter()


@router.post("/rebuild")
def rebuild_vector_index():
    """重建知识库向量索引接口
    
    扫描docs目录下的所有Markdown文档，重新生成embedding向量并存储到数据库。
    通常在更新知识库文档后调用。
    
    Returns:
        ApiResult: 包含导入统计信息的响应（文档数、向量数等）
        
    Example:
        >>> POST /api/v1/vector/rebuild
        {"code": 0, "msg": "success", "data": {"docs_count": 3, "vectors_count": 150}}
        
    Note:
        - 会先清空旧的向量数据
        - 耗时较长，取决于文档数量和embedding模型速度
        - 应用启动时会自动执行一次
    """
    service = PGVectorService()
    return ApiResult.ok(service.rebuild_from_docs())
