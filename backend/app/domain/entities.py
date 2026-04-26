from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel


class EntityCategory(str, Enum):
    PERSONE_FISICHE = "persone_fisiche"
    PERSONE_GIURIDICHE = "persone_giuridiche"
    DATI_CONTATTO = "dati_contatto"
    IDENTIFICATIVI = "identificativi"
    DATI_FINANZIARI = "dati_finanziari"
    DATI_TEMPORALI = "dati_temporali"


class Entity(BaseModel):
    value: str
    category: EntityCategory
    entity_type: str  # e.g. "nome_cognome", "email", "codice_fiscale", "iban"
    confidence: Optional[float] = None
    # Set by IdentificationService: "ner" | "llm" | "merged"
    source: Optional[Literal["ner", "llm", "merged"]] = None
    # Set by SemanticRoleService: e.g. "fornitore", "paziente", "locatore"
    semantic_role: Optional[str] = None
    # Set by ExtractionService after Stage 2 — preview of the placeholder
    # that AnonymizationService will produce in the final document.
    proposed_replacement: Optional[str] = None


class AnonymizationMapping(BaseModel):
    original: str
    replacement: str
    category: EntityCategory
    entity_type: str
    semantic_role: Optional[str] = None
