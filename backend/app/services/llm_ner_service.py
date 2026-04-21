"""
LLM NER Service
===============
Uses the LLM to perform Named Entity Recognition on a document in any language.
This is the semantic, multilingual NER component of the Identification Module.
"""

import json
import re
from typing import List, Optional

from ..domain.entities import Entity, EntityCategory
from ..infrastructure.llm.ollama_client import OllamaClient


_SYSTEM_PROMPT = """\
You are a privacy expert specialised in identifying personally identifiable information (PII).
Analyse the provided document — which may be in Italian, English, French, or German — and
extract ALL sensitive entities.  Be thorough: scan every section of the document.

Return ONLY a valid JSON object with this exact structure (no markdown, no explanation):
{
  "entities": [
    {
      "value": "<exact text as it appears in the document>",
      "category": "<category>",
      "entity_type": "<type>"
    }
  ]
}

Available categories and their EXACT entity_type values (use only these names):
  persone_fisiche    → nome_cognome | data_nascita | luogo_nascita | nazionalita
  persone_giuridiche → nome_azienda | nome_organizzazione
  dati_contatto      → email | telefono | indirizzo | cap_citta | url | profilo_social
  identificativi     → codice_fiscale | passaporto | patente | carta_identita |
                       tessera_sanitaria | targa | numero_avs | numero_assicurazione |
                       partita_iva | numero_licenza
  dati_finanziari    → iban | numero_carta | conto_bancario | bic_swift
  dati_temporali     → data_nascita | data_contratto | data_evento | scadenza

Rules:
  - Copy values EXACTLY as they appear (preserve formatting, spaces, punctuation).
  - The value must contain ONLY the entity text itself.  Never include surrounding
    markdown syntax (* _ # -), list markers, newlines, or adjacent labels.
  - Do NOT invent or paraphrase values.
  - Do NOT include generic words that are not PII.
  - Each entity must contain exactly ONE piece of PII.  Never combine multiple
    data points (e.g. address + email + phone) into a single entity value —
    extract each one as a separate entity.
  - Do NOT extract standalone city or country names (e.g. "Milano", "Italia") when they
    are already part of a full address you have extracted.
  - If the same value appears multiple times, include it only once.
  - Extract ALL person names, ALL company/organisation names, and ALL addresses in the
    document, not only the primary/main ones.
  - Pay special attention to employment/experience sections: extract the employer name
    and address for EVERY job listed, including past positions — not just the current one.
  - Universities, hospitals, law firms, courts, and public institutions are
    persone_giuridiche/nome_organizzazione.
  - Entities containing corporate suffixes (S.r.l., S.p.A., GmbH, SA, AG, Ltd, Inc., etc.)
    are ALWAYS persone_giuridiche/nome_azienda, never persone_fisiche.
  - License IDs, certificate numbers, and registration numbers are
    identificativi/numero_licenza.
  - "P.IVA" or "Partita IVA" followed by 11 digits is identificativi/partita_iva.
  - Use ONLY the entity_type names listed above.  Do not use synonyms or variations
    (e.g. use "targa" not "targa_auto", use "carta_identita" not "documento_identità").\
"""


# Map non-canonical entity_type names the LLM may produce to canonical values.
_TYPE_ALIASES: dict[str, str] = {
    "targa_auto": "targa",
    "documento_identità": "carta_identita",
    "documento_identita": "carta_identita",
    "carta_di_identita": "carta_identita",
    "carta_di_identità": "carta_identita",
    "numero_telefono": "telefono",
    "indirizzo_email": "email",
}


def _clean_value(raw_value: str) -> str:
    """Strip markdown artifacts, newlines, and surrounding punctuation from an
    entity value extracted by the LLM."""
    # Collapse newlines and everything after them (the LLM sometimes grabs the
    # next list-item marker, e.g. "Marta Bianchi\n-").
    value = re.sub(r"[\n\r]+.*", "", raw_value)
    # Strip leading/trailing whitespace, markdown markers, and list bullets.
    value = value.strip().strip("-*_#").strip()
    return value


def _parse(raw: str, allowed_categories: List[str]) -> List[Entity]:
    cleaned = re.sub(r"```[a-z]*\n?", "", raw).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return []
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return []

    entities: List[Entity] = []
    for item in data.get("entities", []):
        try:
            cat = EntityCategory(item.get("category", ""))
            if allowed_categories and cat.value not in allowed_categories:
                continue
            value = _clean_value(item["value"])
            if not value:
                continue
            etype = item.get("entity_type", "unknown")
            etype = _TYPE_ALIASES.get(etype, etype)
            entities.append(
                Entity(
                    value=value,
                    category=cat,
                    entity_type=etype,
                )
            )
        except (ValueError, KeyError):
            continue
    return entities


class LLMNerService:
    def __init__(self, client: OllamaClient):
        self.client = client

    def extract(
        self,
        content: str,
        categories: Optional[List[str]] = None,
    ) -> List[Entity]:
        if categories is None:
            categories = [c.value for c in EntityCategory]

        categories_list = "\n".join(f"  - {c}" for c in categories)
        user_message = (
            f"Extract all PII entities from the document below.\n"
            f"Focus only on these categories:\n{categories_list}\n\n"
            f"Document:\n{content}"
        )

        raw = self.client.chat(
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ]
        )
        return _parse(raw, categories)
