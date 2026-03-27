from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from ...domain.document import AnonymizationResult
from ...domain.entities import Entity
from ...services.anonymization_service import AnonymizationService

router = APIRouter()
_service = AnonymizationService()


class AnonymizeRequest(BaseModel):
    document_id: str
    content: str
    entities: List[Entity]


@router.post("/anonymize", response_model=AnonymizationResult)
async def anonymize_document(req: AnonymizeRequest):
    return _service.anonymize(
        content=req.content,
        entities=req.entities,
        document_id=req.document_id,
    )
