from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from ...services.audit_service import compute_file_hash, log_event
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

    file_hash = compute_file_hash(raw)
    document_id = _cache.store(markdown)

    log_event(
        "document_uploaded",
        document_id,
        file_hash=file_hash,
        filename=file.filename or "",
        file_size_bytes=len(raw),
    )

    return ConvertResponse(
        document_id=document_id,
        filename=file.filename or "",
        content=markdown,
        char_count=len(markdown),
    )
