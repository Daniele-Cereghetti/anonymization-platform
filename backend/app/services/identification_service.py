"""
Modulo Identificazione
======================
Hybrid NER pipeline: Presidio/spaCy (pattern-based, fast) + LLM (semantic, multilingual).

Strategy:
  1. Presidio runs regex/rule-based recognizers → catches structured PII (email, IBAN,
     phone, credit card, etc.) reliably across all languages.
  2. LLM runs full NER on the document → catches names, organizations, addresses and
     anything semantically complex or language-specific.
  3. Results are merged: LLM entities take precedence; Presidio entities that don't
     overlap with any LLM entity are added.

Presidio requires a spaCy NLP engine.  If the model is not installed the module falls
back gracefully to LLM-only mode and logs a warning.
"""

import logging
from typing import List, Optional

from ..domain.entities import Entity, EntityCategory
from .llm_ner_service import LLMNerService
from ..infrastructure.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Presidio → internal category mapping
# ---------------------------------------------------------------------------

_PRESIDIO_ENTITY_MAP: dict[str, tuple[EntityCategory, str]] = {
    "PERSON":         (EntityCategory.PERSONE_FISICHE,   "nome_cognome"),
    "ORGANIZATION":   (EntityCategory.PERSONE_GIURIDICHE, "nome_azienda"),
    "EMAIL_ADDRESS":  (EntityCategory.DATI_CONTATTO,     "email"),
    "PHONE_NUMBER":   (EntityCategory.DATI_CONTATTO,     "telefono"),
    "IBAN_CODE":      (EntityCategory.DATI_FINANZIARI,   "iban"),
    "CREDIT_CARD":    (EntityCategory.DATI_FINANZIARI,   "numero_carta"),
    "LOCATION":       (EntityCategory.DATI_CONTATTO,     "indirizzo"),
    "DATE_TIME":      (EntityCategory.DATI_TEMPORALI,    "data_evento"),
    "NRP":            (EntityCategory.IDENTIFICATIVI,    "codice_fiscale"),
    "IP_ADDRESS":     (EntityCategory.DATI_CONTATTO,     "ip_address"),
    "URL":            (EntityCategory.DATI_CONTATTO,     "url"),
    "MEDICAL_LICENSE":(EntityCategory.IDENTIFICATIVI,    "licenza_medica"),
    "CRYPTO":         (EntityCategory.DATI_FINANZIARI,   "crypto_wallet"),
}

_PRESIDIO_LANG_FALLBACK = "en"


# ---------------------------------------------------------------------------
# Presidio loader (lazy, optional)
# ---------------------------------------------------------------------------

def _load_presidio_analyzer():
    """Returns an AnalyzerEngine or None if presidio / spaCy are not available."""
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
        provider = NlpEngineProvider(nlp_configuration=config)
        nlp_engine = provider.create_engine()
        return AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])
    except Exception as exc:
        logger.warning(
            "Presidio/spaCy not available (%s). "
            "Falling back to LLM-only identification. "
            "Install with: pip install presidio-analyzer spacy && "
            "python -m spacy download en_core_web_sm",
            exc,
        )
        return None


# Module-level singleton (initialised once per process)
_analyzer = None
_analyzer_loaded = False


def _get_analyzer():
    global _analyzer, _analyzer_loaded
    if not _analyzer_loaded:
        _analyzer = _load_presidio_analyzer()
        _analyzer_loaded = True
    return _analyzer


# ---------------------------------------------------------------------------
# NER helpers
# ---------------------------------------------------------------------------

def _run_presidio(content: str, allowed_categories: List[str]) -> List[Entity]:
    analyzer = _get_analyzer()
    if analyzer is None:
        return []

    try:
        results = analyzer.analyze(
            text=content,
            language=_PRESIDIO_LANG_FALLBACK,
            entities=list(_PRESIDIO_ENTITY_MAP.keys()),
        )
    except Exception as exc:
        logger.warning("Presidio analysis failed: %s", exc)
        return []

    entities: List[Entity] = []
    for result in results:
        mapping = _PRESIDIO_ENTITY_MAP.get(result.entity_type)
        if mapping is None:
            continue
        cat, etype = mapping
        if allowed_categories and cat.value not in allowed_categories:
            continue
        value = content[result.start:result.end].strip()
        if not value:
            continue
        entities.append(
            Entity(
                value=value,
                category=cat,
                entity_type=etype,
                confidence=result.score,
                source="ner",
            )
        )
    return entities


def _run_llm_ner(
    content: str,
    allowed_categories: List[str],
    client: OllamaClient,
) -> List[Entity]:
    svc = LLMNerService(client)
    entities = svc.extract(content=content, categories=allowed_categories)
    for e in entities:
        e.source = "llm"
    return entities


# ---------------------------------------------------------------------------
# Merge strategy
# ---------------------------------------------------------------------------

def _overlaps(val_a: str, val_b: str) -> bool:
    """True if either value is a substring of the other."""
    a, b = val_a.lower(), val_b.lower()
    return a in b or b in a


def _merge(ner_entities: List[Entity], llm_entities: List[Entity]) -> List[Entity]:
    """
    LLM entities take precedence.
    Add NER entities only if they don't overlap with any LLM entity.
    Mark merged entities with source='merged'.
    """
    merged = list(llm_entities)

    for ner_ent in ner_entities:
        dominated = any(_overlaps(ner_ent.value, e.value) for e in merged)
        if not dominated:
            ner_ent.source = "merged"
            merged.append(ner_ent)

    return merged


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

class IdentificationService:
    """
    Orchestrates Presidio/spaCy NER + LLM NER and merges results.
    """

    def __init__(self, client: OllamaClient):
        self.client = client

    def identify(
        self,
        content: str,
        categories: Optional[List[str]] = None,
    ) -> List[Entity]:
        if categories is None:
            categories = [c.value for c in EntityCategory]

        ner_entities = _run_presidio(content, categories)
        llm_entities = _run_llm_ner(content, categories, self.client)

        entities = _merge(ner_entities, llm_entities)

        logger.debug(
            "Identification: ner=%d llm=%d merged=%d",
            len(ner_entities),
            len(llm_entities),
            len(entities),
        )
        return entities
