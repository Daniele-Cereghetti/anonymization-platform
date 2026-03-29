"""
Modulo Identificazione
======================
Hybrid NER pipeline: Presidio/spaCy (pattern-based, fast) + LLM (semantic, multilingual).

Strategy:
  1. Lingua detects the document language automatically.
  2. Presidio runs regex/rule-based recognizers with the matching spaCy model → catches
     structured PII (email, IBAN, phone, credit card, etc.) reliably.
  3. LLM runs full NER on the document → catches names, organizations, addresses and
     anything semantically complex or language-specific.
  4. Results are merged: LLM entities take precedence; Presidio entities that don't
     overlap with any LLM entity are added.

Presidio requires at least one spaCy model installed.  If none are found the module
falls back gracefully to LLM-only mode and logs a warning.
Lingua is optional: if not installed, language detection is skipped and Italian is used
as the default language for Presidio.
"""

import logging
from typing import List, Optional

from ..domain.entities import Entity, EntityCategory
from .llm_ner_service import LLMNerService
from ..infrastructure.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Supported spaCy models per language
# ---------------------------------------------------------------------------

_SPACY_MODELS: dict[str, str] = {
    "it": "it_core_news_sm",
    "en": "en_core_web_sm",
    "fr": "fr_core_news_sm",
    "de": "de_core_news_sm",
}

_DEFAULT_LANG = "it"


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


# ---------------------------------------------------------------------------
# Language detection (lingua — optional)
# ---------------------------------------------------------------------------

_lingua_detector = None
_lingua_loaded = False


def _get_lingua_detector():
    global _lingua_detector, _lingua_loaded
    if not _lingua_loaded:
        try:
            from lingua import Language, LanguageDetectorBuilder
            _lingua_detector = (
                LanguageDetectorBuilder
                .from_languages(Language.ITALIAN, Language.ENGLISH, Language.FRENCH, Language.GERMAN)
                .build()
            )
            logger.debug("Lingua language detector initialised.")
        except ImportError:
            logger.warning(
                "lingua-language-detector not installed. Language detection disabled. "
                "Install with: pip install lingua-language-detector"
            )
            _lingua_detector = None
        _lingua_loaded = True
    return _lingua_detector


def _detect_language(text: str) -> str:
    """Returns a two-letter language code (e.g. 'it', 'en') or the default."""
    detector = _get_lingua_detector()
    if detector is None:
        return _DEFAULT_LANG
    try:
        from lingua import Language
        result = detector.detect_language_of(text)
        if result is None:
            return _DEFAULT_LANG
        lang_map = {
            Language.ITALIAN: "it",
            Language.ENGLISH: "en",
            Language.FRENCH:  "fr",
            Language.GERMAN:  "de",
        }
        return lang_map.get(result, _DEFAULT_LANG)
    except Exception as exc:
        logger.debug("Language detection failed (%s), using default '%s'.", exc, _DEFAULT_LANG)
        return _DEFAULT_LANG


# ---------------------------------------------------------------------------
# Presidio loader (lazy, optional)
# ---------------------------------------------------------------------------

_analyzer = None
_supported_langs: set[str] = set()
_analyzer_loaded = False


def _load_presidio_analyzer():
    """
    Returns (AnalyzerEngine, supported_lang_codes) or (None, set()) if unavailable.
    Only loads spaCy models that are actually installed; warns for missing ones.
    """
    try:
        import spacy
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        available = []
        for lang_code, model_name in _SPACY_MODELS.items():
            if spacy.util.is_package(model_name):
                available.append({"lang_code": lang_code, "model_name": model_name})
            else:
                logger.info(
                    "spaCy model '%s' not installed — language '%s' will not be used by Presidio. "
                    "Install with: python -m spacy download %s",
                    model_name, lang_code, model_name,
                )

        if not available:
            logger.warning(
                "No supported spaCy models found. Falling back to LLM-only identification. "
                "Install at least one model, e.g.: python -m spacy download it_core_news_sm"
            )
            return None, set()

        config = {"nlp_engine_name": "spacy", "models": available}
        provider = NlpEngineProvider(nlp_configuration=config)
        nlp_engine = provider.create_engine()
        supported = {m["lang_code"] for m in available}
        analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=list(supported),
        )
        logger.info("Presidio loaded with language(s): %s", sorted(supported))
        return analyzer, supported

    except Exception as exc:
        logger.warning(
            "Presidio/spaCy not available (%s). "
            "Falling back to LLM-only identification. "
            "Install with: pip install presidio-analyzer spacy",
            exc,
        )
        return None, set()


def _get_analyzer():
    global _analyzer, _supported_langs, _analyzer_loaded
    if not _analyzer_loaded:
        _analyzer, _supported_langs = _load_presidio_analyzer()
        _analyzer_loaded = True
    return _analyzer, _supported_langs


# ---------------------------------------------------------------------------
# NER helpers
# ---------------------------------------------------------------------------

def _run_presidio(content: str, allowed_categories: List[str], lang: str) -> List[Entity]:
    analyzer, supported_langs = _get_analyzer()
    if analyzer is None:
        return []

    # Use detected language if its model is installed, otherwise pick any available one.
    effective_lang = lang if lang in supported_langs else next(iter(supported_langs), None)
    if effective_lang is None:
        return []
    if effective_lang != lang:
        logger.debug(
            "spaCy model for '%s' not installed; using '%s' as fallback for Presidio.",
            lang, effective_lang,
        )

    try:
        results = analyzer.analyze(
            text=content,
            language=effective_lang,
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
    Language is detected automatically from the document content.
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

        lang = _detect_language(content)
        logger.debug("Detected document language: %s", lang)

        ner_entities = _run_presidio(content, categories, lang)
        llm_entities = _run_llm_ner(content, categories, self.client)

        entities = _merge(ner_entities, llm_entities)

        logger.debug(
            "Identification: lang=%s ner=%d llm=%d merged=%d",
            lang, len(ner_entities), len(llm_entities), len(entities),
        )
        return entities
