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
import re
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
    "MEDICAL_LICENSE":   (EntityCategory.IDENTIFICATIVI,    "licenza_medica"),
    "CRYPTO":            (EntityCategory.DATI_FINANZIARI,   "crypto_wallet"),
    "IT_LICENSE_PLATE":  (EntityCategory.IDENTIFICATIVI,    "targa"),
    "IT_IDENTITY_CARD":  (EntityCategory.IDENTIFICATIVI,    "carta_identita"),
    "IT_IDENTITY_CARD_ELECTRONIC": (EntityCategory.IDENTIFICATIVI, "carta_identita"),
    "CH_AVS_NUMBER":     (EntityCategory.IDENTIFICATIVI,    "numero_avs"),
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

        from presidio_analyzer import Pattern, PatternRecognizer, RecognizerRegistry

        config = {"nlp_engine_name": "spacy", "models": available}
        provider = NlpEngineProvider(nlp_configuration=config)
        nlp_engine = provider.create_engine()
        supported = {m["lang_code"] for m in available}

        # Build a custom registry: start from predefined recognizers, then add
        # Italian-specific recognizers for license plates and identity cards.
        registry = RecognizerRegistry(supported_languages=list(supported))
        registry.load_predefined_recognizers(languages=list(supported))
        for lang in supported:
            registry.add_recognizer(PatternRecognizer(
                supported_entity="IT_LICENSE_PLATE",
                name="ItLicensePlateRecognizer",
                supported_language=lang,
                patterns=[Pattern(
                    name="italian_license_plate",
                    regex=_IT_LICENSE_PLATE_REGEX,
                    score=_IT_LICENSE_PLATE_SCORE,
                )],
                context=["targa", "veicolo", "auto", "autovettura"],
            ))
            registry.add_recognizer(PatternRecognizer(
                supported_entity="IT_IDENTITY_CARD",
                name="ItIdentityCardRecognizer",
                supported_language=lang,
                patterns=[Pattern(
                    name="italian_identity_card",
                    regex=_IT_IDENTITY_CARD_REGEX,
                    score=_IT_IDENTITY_CARD_SCORE,
                )],
                context=[
                    "CI", "carta identità", "carta d'identità",
                    "documento identità", "carta di identità",
                    "ril.", "rilasciata", "rilasciato",
                ],
            ))
            registry.add_recognizer(PatternRecognizer(
                supported_entity="CH_AVS_NUMBER",
                name="ChAvsNumberRecognizer",
                supported_language=lang,
                patterns=[Pattern(
                    name="swiss_avs_number",
                    regex=_CH_AVS_NUMBER_REGEX,
                    score=_CH_AVS_NUMBER_SCORE,
                )],
                context=["avs", "ahv", "assicurazione", "previdenza"],
            ))

        analyzer = AnalyzerEngine(
            registry=registry,
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

    try:
        _nlp_obj = analyzer.nlp_engine.get_nlp(effective_lang)
    except Exception:
        _nlp_obj = None

    entities: List[Entity] = []
    for result in results:
        mapping = _PRESIDIO_ENTITY_MAP.get(result.entity_type)
        if mapping is None:
            continue
        value = content[result.start:result.end].strip()
        if not value:
            continue

        # Reclassify: spaCy PERSON beats NRP in overlap resolution, so a codice fiscale
        # may arrive here tagged as PERSON.  Override the mapping when the value matches
        # the Italian fiscal-code pattern exactly.
        effective_presidio_type = result.entity_type
        if result.entity_type == "PERSON" and _IT_FISCAL_CODE_RE.match(value):
            nrp_mapping = _PRESIDIO_ENTITY_MAP.get("NRP")
            if nrp_mapping is not None:
                mapping = nrp_mapping
                effective_presidio_type = "NRP"

        cat, etype = mapping
        if allowed_categories and cat.value not in allowed_categories:
            continue

        if _is_semantic_false_positive(value, effective_presidio_type, _nlp_obj, lang):
            logger.debug(
                "Filtered semantic NER false positive '%s' (%s).",
                value, result.entity_type,
            )
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

# Entity types detected by spaCy's statistical model — context-dependent and
# prone to false positives (e.g. sentence-initial capitalised words in Italian).
# These are only added to the final result when the LLM independently found an
# overlapping entity, confirming the detection is semantically meaningful.
#
# Structural types (email, IBAN, phone, …) are regex/rule-based and remain
# always trusted without LLM confirmation.
_SEMANTIC_NER_TYPES: frozenset[str] = frozenset({
    "nome_cognome",        # PERSON
    "nome_azienda",        # ORGANIZATION
    "nome_organizzazione", # ORGANIZATION (alternate mapping)
    "indirizzo",           # LOCATION
})

# ---------------------------------------------------------------------------
# False-positive filter for semantic NER types
# ---------------------------------------------------------------------------

# Presidio entity types that go through semantic filtering (spaCy statistical NER).
# Structural types (EMAIL, IBAN, PHONE, ...) are regex-based and do not need filtering.
_SEMANTIC_PRESIDIO_TYPES: frozenset[str] = frozenset({"PERSON", "LOCATION", "ORGANIZATION"})

# Language-aware deny-list of document/form-field labels, methodology terms,
# and common capitalised words that spaCy consistently misclassifies as named entities.
# "common" entries are checked regardless of the detected language.
_NER_DENY_LIST: dict[str, frozenset[str]] = {
    "common": frozenset({
        # Methodology terms (tagged PROPN across all languages)
        "agile", "scrum", "lean", "kanban", "pmp",
        # Acronyms / cross-language field labels
        "wms", "pmo", "iban",
    }),
    "it": frozenset({
        # CV / form field labels
        "nome", "cognome", "indirizzo", "telefono", "email", "sede", "iban",
        "documento", "linkedin", "formazione", "standardizzazione", "supporto",
        "riferimenti", "codice fiscale", "profilo", "curriculum vitae",
        "competenze", "esperienza", "disponibili", "certificazioni", "contatti",
        "dati personali",
        # Contract / legal section headers
        "locatore", "conduttore", "conduttrice", "firme", "firma",
        "durata", "canone", "deposito", "causale", "verbale", "clausole",
        "preavviso", "parti", "fornitore", "cliente", "sede legale",
        # Medical record section headers
        "paziente", "ricovero", "anamnesi", "diagnosi", "farmaci", "terapia",
        "tessera sanitaria", "cartella clinica", "allergie",
        # Italian verbs / common words capitalised at line start
        "amo", "pianificare", "ridurre",
        "implementazione", "creazione", "migrazione",
    }),
    "de": frozenset({
        # CV / form field labels
        "persönliche daten", "geburtsdatum", "geburtsort", "telefon", "adresse",
        "steuernummer", "kompetenzen", "publikationen", "standort", "ausweisdokument",
        "profil", "erfahrung", "ausbildung", "fähigkeiten", "referenzen",
        # Contract / org labels
        "arbeitgeber", "abteilung", "firmenname",
    }),
    "fr": frozenset({
        # CV / form field labels
        "nom et prénom", "adresse", "téléphone", "code fiscal", "lieu",
        "pour", "analyste", "compétences", "formation", "expérience",
        "références", "employeur", "société", "département",
    }),
    "en": frozenset({
        # CV / form field labels
        "name", "address", "phone", "skills", "education",
        "references", "employer", "company", "department",
        "date of birth", "place of birth", "nationality",
    }),
}

# Partial IBAN substrings (e.g. "IT60 X054") that spaCy tags as LOCATION but are
# already fully captured by the IBAN_CODE recognizer.  A real IBAN is ≥15 chars
# without spaces; anything shorter matching the country-code+check-digit prefix is
# a fragment and should be dropped.
_PARTIAL_IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[\sA-Z0-9]*$")
_IBAN_MIN_LEN_NO_SPACES = 15

# Regex to detect Italian fiscal codes (16 chars: 6 letters + 2 digits + letter + 2 digits
# + letter + 3 digits + letter) misclassified by spaCy as PERSON.
_IT_FISCAL_CODE_RE = re.compile(
    r"^[A-Z]{6}\d{2}[A-EHLMPR-T]\d{2}[A-Z]\d{3}[A-Z]$",
    re.IGNORECASE,
)

# Pattern objects for custom Presidio recognizers (instantiated lazily per language in
# _load_presidio_analyzer to avoid importing presidio_analyzer at module level).
_IT_LICENSE_PLATE_REGEX = r"\b[A-Z]{2}\d{3}[A-Z]{2}\b"          # post-1994: FP123XY
_IT_LICENSE_PLATE_SCORE = 0.5                                     # boosted to ~0.85 by context
_IT_IDENTITY_CARD_REGEX = r"\b[A-Z]{2}\d{7}\b"                    # AA1234567 (2 letters + 7 digits)
_IT_IDENTITY_CARD_SCORE = 0.65                                    # specific enough to not require context boost
_CH_AVS_NUMBER_REGEX = r"\b756\.\d{4}\.\d{4}\.\d{2}\b"           # 756.XXXX.XXXX.XX (Swiss AVS/AHV)
_CH_AVS_NUMBER_SCORE = 0.85                                       # highly specific pattern


def _is_semantic_false_positive(
    value: str,
    presidio_entity_type: str,
    nlp_obj,
    lang: str = "it",
) -> bool:
    """
    Returns True if *value* is likely a false positive for a semantic Presidio entity type.

    Applied only to PERSON / LOCATION / ORGANIZATION (statistical spaCy NER); structural
    types (EMAIL, IBAN, PHONE, …) are regex-based and are never filtered here.

    Three layers (cheapest first):
      1. Deny-list  — exact/prefix match on language-specific document section labels and
                      capitalised words that spaCy consistently misclassifies.
                      Checks both the "common" bucket and the detected-language bucket.
      2. Partial IBAN regex — drops substrings like "IT60 X054" already fully captured
                      by the IBAN_CODE recognizer.
      3. POS filter — discard if spaCy finds no PROPN token in the span; real names,
                      cities, and company names always contain at least one PROPN.
    """
    if presidio_entity_type not in _SEMANTIC_PRESIDIO_TYPES:
        return False

    stripped = value.strip()
    lowered = stripped.lower()

    # Layer 1: deny-list — merge common + language-specific entries
    deny = _NER_DENY_LIST.get("common", frozenset()) | _NER_DENY_LIST.get(lang, frozenset())
    if lowered in deny:
        return True
    # Multi-line spans: "Formazione\n- Laurea Magistrale …" → first line is "formazione"
    first_line = lowered.split("\n")[0].strip().rstrip(":–—-").strip()
    if first_line in deny:
        return True
    # Prefix match: "Profilo Project Manager" starts with "profilo "
    if any(lowered.startswith(term + " ") for term in deny):
        return True

    # Layer 2: partial IBAN regex
    no_spaces = stripped.replace(" ", "")
    if _PARTIAL_IBAN_RE.match(stripped) and len(no_spaces) < _IBAN_MIN_LEN_NO_SPACES:
        return True

    # Layer 3: POS filter — no PROPN token → not a named entity
    if nlp_obj is not None:
        doc = nlp_obj(stripped)
        if not any(token.pos_ == "PROPN" for token in doc):
            return True

    return False


def _overlaps(val_a: str, val_b: str) -> bool:
    """True if either value is a substring of the other."""
    a, b = val_a.lower(), val_b.lower()
    return a in b or b in a


def _merge(ner_entities: List[Entity], llm_entities: List[Entity]) -> List[Entity]:
    """
    LLM entities take precedence.

    Structural NER entities (email, IBAN, phone, …) are added when they don't
    overlap with any LLM entity — regex-based detectors are highly reliable.

    Semantic NER entities (person, org, location) are added ONLY when the LLM
    found an overlapping entity — spaCy's model can produce false positives on
    sentence-initial capitalised words, so LLM confirmation is required.
    """
    merged = list(llm_entities)

    for ner_ent in ner_entities:
        overlapping_llm = [e for e in llm_entities if _overlaps(ner_ent.value, e.value)]

        if ner_ent.entity_type in _SEMANTIC_NER_TYPES:
            # Semantic: only add if the LLM independently confirmed it.
            if overlapping_llm:
                ner_ent.source = "merged"
                merged.append(ner_ent)
            else:
                logger.debug(
                    "Discarding unconfirmed semantic NER entity '%s' (%s) — "
                    "not found by LLM.",
                    ner_ent.value, ner_ent.entity_type,
                )
        else:
            # Structural: add if not already covered by the LLM.
            if not overlapping_llm:
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
