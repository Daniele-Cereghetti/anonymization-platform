"""
Anonymization Service
=====================
Applies semantic replacements following section 2.1.4 of the project documentation.

Replacement strategy (utility-preserving, as per Francopoulo & Schaub / Albanese et al.):

  persone_fisiche / persone_giuridiche WITH semantic_role
    → role-based label:  "fornitore1", "paziente1", "azienda_fornitrice1"

  persone_fisiche / persone_giuridiche WITHOUT semantic_role
    → generic label:     "persona1", "organizzazione1"

  All other categories (dati_contatto, identificativi, dati_finanziari, dati_temporali)
    → bracketed placeholder: "[EMAIL_1]", "[IBAN_1]", "[TELEFONO_1]"

Consistency guarantee: within a single document, the same original value always
receives the same replacement.  The mapping table lives only in RAM and is discarded
after the call (irreversibility — section 2.1.5).
"""

import time
from collections import defaultdict
from typing import List

from ..domain.document import AnonymizationResult
from ..domain.entities import AnonymizationMapping, Entity, EntityCategory

# Categories that receive role-based (readable) labels
_ROLE_CATEGORIES = {EntityCategory.PERSONE_FISICHE, EntityCategory.PERSONE_GIURIDICHE}

# Bracketed placeholder templates for structured-data categories
_BRACKET_PLACEHOLDER: dict[str, str] = {
    EntityCategory.DATI_CONTATTO.value:    "CONTATTO",
    EntityCategory.IDENTIFICATIVI.value:   "ID",
    EntityCategory.DATI_FINANZIARI.value:  "DATO_FIN",
    EntityCategory.DATI_TEMPORALI.value:   "DATA",
}

# More specific placeholders keyed by entity_type (override the category default)
_TYPE_PLACEHOLDER: dict[str, str] = {
    "email":            "EMAIL",
    "telefono":         "TELEFONO",
    "indirizzo":        "INDIRIZZO",
    "cap_citta":        "CAP",
    "url":              "URL",
    "iban":             "IBAN",
    "numero_carta":     "CARTA",
    "conto_bancario":   "CONTO",
    "bic_swift":        "BIC",
    "codice_fiscale":   "CODICE_FISCALE",
    "passaporto":       "PASSAPORTO",
    "patente":          "PATENTE",
    "carta_identita":   "CARTA_IDENTITA",
    "tessera_sanitaria":"TESSERA_SANITARIA",
    "targa":            "TARGA",
    "numero_avs":       "AVS",
    "partita_iva":      "PARTITA_IVA",
    "data_nascita":     "DATA_NASCITA",
    "data_contratto":   "DATA_CONTRATTO",
    "data_evento":      "DATA",
    "scadenza":         "SCADENZA",
}


def _build_replacement(entity: Entity, counters: defaultdict) -> str:
    if entity.category in _ROLE_CATEGORIES:
        if entity.semantic_role:
            label = entity.semantic_role.lower().replace(" ", "_")
        elif entity.category == EntityCategory.PERSONE_FISICHE:
            label = "persona"
        else:
            label = "organizzazione"
        counters[label] += 1
        return f"{label}{counters[label]}"
    else:
        # Bracketed placeholder — prefer entity_type-specific label
        label = _TYPE_PLACEHOLDER.get(
            entity.entity_type,
            _BRACKET_PLACEHOLDER.get(entity.category.value, "ENTITA"),
        )
        counters[label] += 1
        return f"[{label}_{counters[label]}]"


class AnonymizationService:
    def anonymize(
        self,
        content: str,
        entities: List[Entity],
        document_id: str,
    ) -> AnonymizationResult:
        start = time.monotonic()

        # Deduplicate and sort longest-first to avoid partial replacements
        seen: set = set()
        unique: List[Entity] = []
        for e in sorted(entities, key=lambda x: len(x.value), reverse=True):
            if e.value not in seen:
                seen.add(e.value)
                unique.append(e)

        counters: defaultdict = defaultdict(int)
        mappings: List[AnonymizationMapping] = []

        for entity in unique:
            replacement = _build_replacement(entity, counters)
            mappings.append(
                AnonymizationMapping(
                    original=entity.value,
                    replacement=replacement,
                    category=entity.category,
                    entity_type=entity.entity_type,
                )
            )

        # Apply replacements (in-memory only — mapping is not persisted)
        anonymized = content
        for mapping in mappings:
            anonymized = anonymized.replace(mapping.original, mapping.replacement)

        elapsed_ms = int((time.monotonic() - start) * 1000)

        return AnonymizationResult(
            document_id=document_id,
            original_content=content,
            anonymized_content=anonymized,
            mappings=mappings,
            processing_time_ms=elapsed_ms,
        )
