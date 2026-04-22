"""
Modulo Ruoli Semantici
======================
Uses the LLM to assign a contextual role to each person / organisation entity
identified by the Identification Module.

Instead of opaque labels like "[PERSONA_1]", the anonymisation module will use
human-readable role-based replacements like "fornitore1", "paziente1", "locatore1"
(as required by section 2.1.4 of the project documentation).

Only entities of category persone_fisiche and persone_giuridiche receive a
semantic role; structured-data entities (emails, IBANs, etc.) keep category
placeholders like "[IBAN_1]".
"""

import json
import logging
import re
from typing import List

from ..domain.entities import Entity, EntityCategory
from ..infrastructure.llm.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

_ROLE_CATEGORIES = {EntityCategory.PERSONE_FISICHE, EntityCategory.PERSONE_GIURIDICHE}

_SYSTEM_PROMPT = """\
You are a document analysis expert specialised in privacy and anonymisation.
Given a document and a list of person / organisation entities, assign a single
contextual role to each entity based on the role they play in the document.

Step 1 — Identify the document type (e.g. CV/resume, rental contract, medical
record, employment contract, invoice, legal complaint, letter, etc.).
Step 2 — Assign a role to each entity that reflects its function in this
specific document type.

Use lowercase Italian role names (underscores allowed, no spaces):

For persons (persone_fisiche):
  candidato, paziente, medico, dottore, infermiere, avvocato, giudice, notaio,
  fornitore, compratore, venditore, locatore, conduttore, datore_lavoro,
  dipendente, recruiter, testimone, richiedente, beneficiario,
  consulente, dirigente, amministratore, rappresentante_legale, controparte

  Common document-type mappings:
    - CV / resume → the subject person is "candidato"
    - Medical record → the subject person is "paziente"
    - Rental contract → "locatore" and "conduttore"
    - Employment contract → "dipendente" and "datore_lavoro"

For organisations (persone_giuridiche):
  azienda_fornitrice, azienda_cliente, banca, ente_pubblico, ospedale,
  clinica, studio_legale, studio_notarile, assicurazione, agenzia_immobiliare,
  societa_datrice_lavoro, societa_appaltatrice, fondo_pensione, ente_formazione

  Common document-type mappings:
    - CV / resume → the employer is "societa_datrice_lavoro", a university is "ente_formazione"
    - Invoice → "azienda_fornitrice" and "azienda_cliente"

Return ONLY a valid JSON object (no markdown, no explanation):
{
  "assignments": [
    { "value": "<exact entity value>", "role": "<role>" }
  ]
}

Rules:
  - Include ONLY entities from the provided list.
  - Use the EXACT value as provided.
  - Prefer a specific role over a generic one.  Use "persona" or "organizzazione"
    ONLY when the document truly provides no contextual clue.
  - Never invent entities not in the list.
  - The document may be in any language (Italian, English, French, German).
    Always use the ITALIAN role names listed above, regardless of the document language.
  - CRITICAL: follow the document-type mappings strictly.  The main subject of a
    CV / resume is ALWAYS "candidato" — never "dipendente", "paziente", or other roles.
    "dipendente" is only for employment contracts, "paziente" is only for medical records.\
"""


def _parse_assignments(raw: str) -> dict[str, str]:
    """Returns a dict mapping entity value → role."""
    cleaned = re.sub(r"```[a-z]*\n?", "", raw).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return {}

    result: dict[str, str] = {}
    for item in data.get("assignments", []):
        value = item.get("value", "").strip()
        role = item.get("role", "").strip().lower().replace(" ", "_")
        if value and role:
            result[value] = role
    return result


class SemanticRoleService:
    def __init__(self, client: OllamaClient):
        self.client = client

    def assign_roles(self, content: str, entities: List[Entity]) -> List[Entity]:
        """
        Enriches person/organisation entities with a semantic_role.
        Returns the same list with semantic_role populated where applicable.
        """
        role_entities = [e for e in entities if e.category in _ROLE_CATEGORIES]

        if not role_entities:
            return entities

        # Build entity list for the prompt
        entity_lines = "\n".join(
            f'  - "{e.value}" ({e.category.value})' for e in role_entities
        )
        user_message = (
            f"Assign a contextual role to each entity listed below, "
            f"based on how they appear in the document.\n\n"
            f"Entities to classify:\n{entity_lines}\n\n"
            f"Document (first 3000 chars):\n{content[:3000]}"
        )

        try:
            raw = self.client.chat(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ]
            )
            assignments = _parse_assignments(raw)
        except Exception as exc:
            logger.warning("SemanticRoleService failed: %s. Roles will be empty.", exc)
            assignments = {}

        # Apply roles to entities in-place
        for entity in entities:
            if entity.category in _ROLE_CATEGORIES:
                role = assignments.get(entity.value)
                if role:
                    entity.semantic_role = role

        logger.debug(
            "SemanticRoleService: %d/%d entities assigned a role",
            sum(1 for e in entities if e.semantic_role),
            len(role_entities),
        )
        return entities
