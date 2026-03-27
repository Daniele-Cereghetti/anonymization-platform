"""
Extraction Service
==================
Orchestrates the two-stage /extract pipeline:

  Stage 1 – Modulo Identificazione (IdentificationService)
    Presidio/spaCy (pattern-based NER) + LLM (semantic NER) → merged entity list

  Stage 2 – Modulo Ruoli Semantici (SemanticRoleService)
    LLM assigns contextual roles to person / organisation entities
    e.g. "Marco Rossi" → semantic_role="fornitore"
"""

import time
from typing import List, Optional

from ..domain.document import ExtractionResult
from ..domain.entities import EntityCategory
from ..infrastructure.llm.ollama_client import OllamaClient
from .identification_service import IdentificationService
from .semantic_role_service import SemanticRoleService


class ExtractionService:
    def __init__(self, client: OllamaClient):
        self.client = client
        self._identification = IdentificationService(client)
        self._semantic_roles = SemanticRoleService(client)

    def extract(
        self,
        content: str,
        document_id: str,
        categories: Optional[List[str]] = None,
    ) -> ExtractionResult:
        if categories is None:
            categories = [c.value for c in EntityCategory]

        start = time.monotonic()

        # Stage 1: hybrid NER
        entities = self._identification.identify(content=content, categories=categories)

        # Stage 2: contextual role assignment
        entities = self._semantic_roles.assign_roles(content=content, entities=entities)

        elapsed_ms = int((time.monotonic() - start) * 1000)

        return ExtractionResult(
            document_id=document_id,
            entities=entities,
            categories_requested=categories,
            processing_time_ms=elapsed_ms,
            model=self.client.model,
        )
