from fastapi import APIRouter

from common.ApiResult import ApiResult
from services.vector.pgvector_service import PGVectorService

router = APIRouter()


@router.post("/rebuild")
def rebuild_vector_index():
    service = PGVectorService()
    return ApiResult.ok(service.rebuild_from_docs())
