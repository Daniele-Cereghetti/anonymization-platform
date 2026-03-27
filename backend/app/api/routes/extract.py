from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...domain.document import ExtractionResult
from ...infrastructure.llm.ollama_client import OllamaClient, OllamaError
from ...services.extraction_service import ExtractionService

router = APIRouter()


class ExtractRequest(BaseModel):
    document_id: str
    content: str
    categories: Optional[List[str]] = None


@router.post("/extract", response_model=ExtractionResult)
async def extract_entities(req: ExtractRequest):
    client = OllamaClient()
    if not client.is_available():
        raise HTTPException(status_code=503, detail="LLM service not available. Is Ollama running?")

    service = ExtractionService(client)
    try:
        return service.extract(
            content=req.content,
            document_id=req.document_id,
            categories=req.categories,
        )
    except OllamaError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
