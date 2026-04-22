"""
Modulo Ruoli Semantici
======================
Uses the LLM to assign a contextual role to each person / organisation entity
identified by the Identification Module, and then resolves **ownership** of
every other entity (emails, addresses, IBANs, phones, dates, IDs) so that
the anonymisation module can produce context-aware placeholders like
"[EMAIL_CANDIDATO_1]" instead of generic "[EMAIL_1]".

Two-pass pipeline:
  1. **Role assignment** — persons and organisations receive a role that
     describes their function in the document (candidato, locatore, …).
  2. **Ownership resolution** — every remaining entity is linked to the
     person/org it belongs to, by assigning the owner's role as its
     semantic_role.
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


_OWNERSHIP_SYSTEM_PROMPT = """\
You are a document analysis expert specialised in privacy.
You are given a document, a list of persons/organisations with their assigned roles,
and a list of data entities (emails, addresses, phones, dates, IDs, IBANs, etc.).

For each data entity, determine which person or organisation it belongs to and
return the ROLE of the owner (not the owner's name).

If an entity cannot be clearly attributed to any person/organisation (e.g. a
generic document date), use "documento" as the owner_role.

Return ONLY a valid JSON object (no markdown, no explanation):
{
  "ownership": [
    { "value": "<exact entity value>", "owner_role": "<role of the owner>" }
  ]
}

Rules:
  - Include ONLY entities from the provided data entities list.
  - Use the EXACT value as provided.
  - The owner_role must be one of the roles already assigned to a person/organisation,
    or "documento" for entities not attributable to any specific person/org.
  - Never invent entities not in the list.\
"""


def _parse_ownership(raw: str) -> dict[str, str]:
    """Returns a dict mapping entity value → owner_role."""
    cleaned = re.sub(r"```[a-z]*\n?", "", raw).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return {}

    result: dict[str, str] = {}
    for item in data.get("ownership", []):
        value = item.get("value", "").strip()
        role = item.get("owner_role", "").strip().lower().replace(" ", "_")
        if value and role:
            result[value] = role
    return result


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
        Two-pass enrichment:
          1. Assigns a contextual role to person/organisation entities.
          2. Resolves ownership of all other entities (emails, addresses,
             phones, dates, IDs, IBANs) by linking them to the person/org
             they belong to.
        Returns the same list with semantic_role populated where applicable.
        """
        # --- Pass 1: role assignment for persons / organisations -----------
        role_entities = [e for e in entities if e.category in _ROLE_CATEGORIES]

        if not role_entities:
            return entities

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

        for entity in entities:
            if entity.category in _ROLE_CATEGORIES:
                role = assignments.get(entity.value)
                if role:
                    entity.semantic_role = role

        logger.debug(
            "SemanticRoleService pass 1 (roles): %d/%d entities assigned a role",
            sum(1 for e in entities if e.semantic_role),
            len(role_entities),
        )

        # --- Pass 2: ownership resolution for all other entities ----------
        self._assign_ownership(content, entities)

        return entities

    def _assign_ownership(self, content: str, entities: List[Entity]) -> None:
        """Resolves which person/org each non-person entity belongs to."""
        # Collect assigned roles from pass 1
        role_summary = []
        for e in entities:
            if e.category in _ROLE_CATEGORIES and e.semantic_role:
                role_summary.append(f'  - "{e.value}" → {e.semantic_role}')

        if not role_summary:
            return

        # Collect non-person entities that need ownership
        data_entities = [e for e in entities if e.category not in _ROLE_CATEGORIES]
        if not data_entities:
            return

        roles_block = "\n".join(role_summary)
        entities_block = "\n".join(
            f'  - "{e.value}" ({e.entity_type})' for e in data_entities
        )
        user_message = (
            f"Given these document roles:\n{roles_block}\n\n"
            f"Assign each data entity below to its owner "
            f"(the person/organisation it belongs to).\n"
            f"Return the owner's ROLE, not the name.\n\n"
            f"Data entities:\n{entities_block}\n\n"
            f"Document (first 2000 chars):\n{content[:2000]}"
        )

        try:
            raw = self.client.chat(
                messages=[
                    {"role": "system", "content": _OWNERSHIP_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ]
            )
            ownership = _parse_ownership(raw)
        except Exception as exc:
            logger.warning(
                "SemanticRoleService ownership resolution failed: %s. "
                "Non-person entities will keep generic placeholders.", exc,
            )
            return

        # Apply ownership in-place
        assigned = 0
        for entity in entities:
            if entity.category not in _ROLE_CATEGORIES:
                owner_role = ownership.get(entity.value)
                if owner_role:
                    entity.semantic_role = owner_role
                    assigned += 1

        logger.debug(
            "SemanticRoleService pass 2 (ownership): %d/%d data entities "
            "assigned an owner",
            assigned, len(data_entities),
        )
