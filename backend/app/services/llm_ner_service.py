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
extract all sensitive entities.

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

Available categories and entity_types:
  persone_fisiche   → nome_cognome | data_nascita | luogo_nascita | nazionalita
  persone_giuridiche → nome_azienda | nome_organizzazione
                       (entities with suffixes like S.r.l., S.p.A., GmbH, SA, AG, Ltd, Inc.)
  dati_contatto     → email | telefono | indirizzo | cap_citta | url | profilo_social
  identificativi    → codice_fiscale | passaporto | patente | carta_identita |
                      tessera_sanitaria | targa | numero_avs | numero_assicurazione |
                      partita_iva
  dati_finanziari   → iban | numero_carta | conto_bancario | bic_swift
  dati_temporali    → data_nascita | data_contratto | data_evento | scadenza

Rules:
  - Copy values EXACTLY as they appear (preserve formatting, spaces, punctuation).
  - Do NOT invent or paraphrase values.
  - Do NOT include generic words that are not PII.
  - If the same value appears multiple times, include it only once.
  - Entities containing corporate suffixes (S.r.l., S.p.A., GmbH, SA, AG, Ltd, Inc., etc.)
    are ALWAYS persone_giuridiche/nome_azienda, never persone_fisiche.
  - "P.IVA" or "Partita IVA" followed by 11 digits is identificativi/partita_iva.\
"""


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
            entities.append(
                Entity(
                    value=item["value"],
                    category=cat,
                    entity_type=item.get("entity_type", "unknown"),
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
