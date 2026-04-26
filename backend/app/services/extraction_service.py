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
from collections import defaultdict
from typing import List, Optional

from ..domain.document import ExtractionResult
from ..domain.entities import EntityCategory
from ..infrastructure.llm.ollama_client import OllamaClient
from .anonymization_service import build_replacement
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
        doc_type_override: Optional[str] = None,
    ) -> ExtractionResult:
        if categories is None:
            categories = [c.value for c in EntityCategory]

        start = time.monotonic()

        # Stage 1: hybrid NER
        entities = self._identification.identify(content=content, categories=categories)

        # Stage 2: contextual role assignment
        entities, doc_type = self._semantic_roles.assign_roles(
            content=content,
            entities=entities,
            doc_type_override=doc_type_override,
        )

        # Stage 3 (preview): compute the placeholder each entity will get
        # in the anonymised document.  Lets the frontend show the final
        # role-aware replacement (e.g. [DATA_NASCITA_CANDIDATO_1]) already
        # in the mapping table, instead of a generic [DATA_NASCITA_1].
        # Iterate longest-first so numbering matches the actual anonymise
        # pass which sorts the same way before substitution.
        preview_counters: defaultdict = defaultdict(int)
        for entity in sorted(entities, key=lambda e: len(e.value), reverse=True):
            entity.proposed_replacement = build_replacement(entity, preview_counters)

        elapsed_ms = int((time.monotonic() - start) * 1000)

        return ExtractionResult(
            document_id=document_id,
            entities=entities,
            categories_requested=categories,
            processing_time_ms=elapsed_ms,
            model=self.client.model,
            document_type=doc_type,
        )
