from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...domain.document import AnonymizationResult
from ...domain.entities import Entity
from ...services.anonymization_service import AnonymizationService
from ...services.cache_service import CacheService

router = APIRouter()
_service = AnonymizationService()
_cache = CacheService()


class AnonymizeRequest(BaseModel):
    document_id: str
    entities: List[Entity]


@router.post("/anonymize", response_model=AnonymizationResult)
async def anonymize_document(req: AnonymizeRequest):
    content = _cache.get(req.document_id)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Document '{req.document_id}' not found or expired.")

    return _service.anonymize(
        content=content,
        entities=req.entities,
        document_id=req.document_id,
    )
