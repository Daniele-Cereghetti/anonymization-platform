import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from .entities import Entity, AnonymizationMapping


class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    content: str
    language: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExtractionResult(BaseModel):
    document_id: str
    entities: List[Entity]
    categories_requested: List[str]
    processing_time_ms: int
    model: str
    document_type: Optional[str] = None


class AnonymizationResult(BaseModel):
    document_id: str
    original_content: str
    anonymized_content: str
    mappings: List[AnonymizationMapping]
    processing_time_ms: int
