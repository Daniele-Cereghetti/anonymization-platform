from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...domain.document import ExtractionResult
from ...infrastructure.llm.ollama_client import OllamaClient, OllamaError
from ...services.audit_service import log_event
from ...services.cache_service import CacheService
from ...services.extraction_service import ExtractionService

router = APIRouter()
_cache = CacheService()


class ExtractRequest(BaseModel):
    document_id: str
    categories: Optional[List[str]] = None
    document_type: Optional[str] = None


@router.post("/extract", response_model=ExtractionResult)
async def extract_entities(req: ExtractRequest):
    content = _cache.get(req.document_id)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Document '{req.document_id}' not found or expired.")

    client = OllamaClient()
    if not client.is_available():
        raise HTTPException(status_code=503, detail="LLM service not available. Is Ollama running?")

    service = ExtractionService(client)
    try:
        result = service.extract(
            content=content,
            document_id=req.document_id,
            categories=req.categories,
            doc_type_override=req.document_type,
        )
    except OllamaError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    log_event(
        "entities_extracted",
        req.document_id,
        entity_count=len(result.entities),
    )
    return result
