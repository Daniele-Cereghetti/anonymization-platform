import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from ...services.conversion_service import ConversionError, ConversionService

router = APIRouter()
_service = ConversionService()


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

    return ConvertResponse(
        document_id=str(uuid.uuid4()),
        filename=file.filename or "",
        content=markdown,
        char_count=len(markdown),
    )
