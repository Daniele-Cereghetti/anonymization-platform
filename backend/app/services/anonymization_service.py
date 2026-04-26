"""
Anonymization Service
=====================
Applies semantic replacements following section 2.1.4 of the project documentation.

Replacement strategy (utility-preserving, as per Francopoulo & Schaub / Albanese et al.):

  All placeholders share the uniform bracketed shape `[LABEL_N]`.

  persone_fisiche / persone_giuridiche WITH semantic_role
    → role-based label:  "[CANDIDATO_1]", "[PAZIENTE_1]", "[AZIENDA_FORNITRICE_1]"

  persone_fisiche / persone_giuridiche WITHOUT semantic_role
    → generic label:     "[PERSONA_1]", "[ORGANIZZAZIONE_1]"

  persone_fisiche sub-types that are not personal names (luogo_nascita,
  nazionalita, data_nascita) → dedicated label, suffixed with the owner role
  when ownership has been resolved: "[DATA_NASCITA_CANDIDATO_1]",
  "[LUOGO_NASCITA_PAZIENTE_1]".  Falls back to "[DATA_NASCITA_1]" when
  the owner is unknown.

  All other categories (dati_contatto, identificativi, dati_finanziari, dati_temporali)
    WITH ownership → context-aware placeholder: "[EMAIL_CANDIDATO_1]", "[INDIRIZZO_AZIENDA_FORNITRICE_1]"

  All other categories WITHOUT ownership
    → generic bracketed placeholder: "[EMAIL_1]", "[IBAN_1]", "[TELEFONO_1]"

Consistency guarantee: within a single document, the same original value always
receives the same replacement.  The mapping table lives only in RAM and is discarded
after the call (irreversibility — section 2.1.5).
"""

import re
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
    "numero_licenza":   "LICENZA",
    "data_nascita":     "DATA_NASCITA",
    "data_contratto":   "DATA_CONTRATTO",
    "data_evento":      "DATA",
    "scadenza":         "SCADENZA",
}

# Sotto-tipi di PERSONE_FISICHE che non sono nomi di persona (sono dati
# anagrafici geografici/temporali) e quindi non devono ricevere il label
# "persona" né essere collassati su un semantic_role di una persona.
_PERSON_SUBTYPE_PLACEHOLDER: dict[str, str] = {
    "luogo_nascita": "LUOGO_NASCITA",
    "nazionalita":   "NAZIONALITA",
    "data_nascita":  "DATA_NASCITA",
}


def _build_replacement(entity: Entity, counters: defaultdict) -> str:
    # 1) Sotto-tipi geografici/temporali di persone_fisiche → label dedicato,
    #    arricchito col ruolo del proprietario quando risolto via ownership
    if (
        entity.category in _ROLE_CATEGORIES
        and entity.entity_type in _PERSON_SUBTYPE_PLACEHOLDER
    ):
        label = _PERSON_SUBTYPE_PLACEHOLDER[entity.entity_type]
        if entity.semantic_role and entity.semantic_role != "documento":
            label = f"{label}_{entity.semantic_role.upper().replace(' ', '_')}"

    # 2) Persone fisiche / giuridiche "vere" → ruolo semantico o fallback
    elif entity.category in _ROLE_CATEGORIES:
        if entity.semantic_role:
            label = entity.semantic_role.upper().replace(" ", "_")
        elif entity.category == EntityCategory.PERSONE_FISICHE:
            label = "PERSONA"
        else:
            label = "ORGANIZZAZIONE"

    # 3) Categorie strutturate (contatti, identificativi, finanziari, temporali)
    else:
        label = _TYPE_PLACEHOLDER.get(
            entity.entity_type,
            _BRACKET_PLACEHOLDER.get(entity.category.value, "ENTITA"),
        )
        # Append the owner role when ownership was resolved by the
        # SemanticRoleService (e.g. EMAIL → EMAIL_CANDIDATO).
        if entity.semantic_role and entity.semantic_role != "documento":
            label = f"{label}_{entity.semantic_role.upper()}"

    counters[label] += 1
    return f"[{label}_{counters[label]}]"


# Caratteri/sequenze che indicano che il valore di un'entità è "sporco":
# l'LLM ha incluso parti del campo successivo (es. newline, " - " bullet,
# ": " label-separator).  Quando una di queste compare, la dedup preferisce
# sempre il valore più corto, anche tra entity_type diversi.
_BUNDLED_VALUE_RE = re.compile(r"\n|\s-\s|:\s")


class AnonymizationService:
    def anonymize(
        self,
        content: str,
        entities: List[Entity],
        document_id: str,
    ) -> AnonymizationResult:
        start = time.monotonic()

        # Sort *shortest-first*: when an LLM produces a "bundled" value that
        # accidentally swallows the next field (e.g. "Marta Bianchi\n- Data di
        # nascita: 14/02/1988" tagged as nome_azienda), processing the clean
        # short value first lets us reject the longer bundled one as soon as
        # we detect the substring relationship — even when entity_types differ.
        seen: set = set()
        unique: List[Entity] = []
        for e in sorted(entities, key=lambda x: len(x.value)):
            if e.value in seen:
                continue
            dominated = False
            for prev in unique:
                a_low = e.value.lower()
                b_low = prev.value.lower()
                # Substring relation in either direction
                if a_low == b_low or a_low in b_low or b_low in a_low:
                    # Same entity_type → standard dedup (keep shorter, already
                    # in `unique` since we sort shortest-first).
                    if prev.entity_type == e.entity_type:
                        dominated = True
                        break
                    # Different entity_type → only collapse when the *longer*
                    # value contains bundling markers (newline / " - " / ": ").
                    # That's the symptom of an LLM that grabbed an adjacent
                    # field; the cleaner short value wins.
                    longer = e.value if len(e.value) >= len(prev.value) else prev.value
                    if _BUNDLED_VALUE_RE.search(longer):
                        dominated = True
                        break
            if not dominated:
                seen.add(e.value)
                unique.append(e)

        # Re-sort longest-first for the actual replacement pass so that
        # longer entities (e.g. full address) are substituted before any
        # shorter substring would consume them.
        unique.sort(key=lambda x: len(x.value), reverse=True)

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
                    semantic_role=entity.semantic_role,
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
