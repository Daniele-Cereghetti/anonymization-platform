from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from ...services.cache_service import CacheService
from ...services.conversion_service import ConversionError, ConversionService

router = APIRouter()
_service = ConversionService()
_cache = CacheService()


class ConvertResponse(BaseModel):
    document_id: str
    filename: str
    content: str
    char_count: int


@router.post("/convert", response_model=ConvertResponse)
async def convert_document(file: UploadFile = File(...)):
    raw = await file.read()
    try:
        markdown = _service.convert_to_markdown(raw, file.filename or "")
    except ConversionError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    document_id = _cache.store(markdown)
    return ConvertResponse(
        document_id=document_id,
        filename=file.filename or "",
        content=markdown,
        char_count=len(markdown),
    )
