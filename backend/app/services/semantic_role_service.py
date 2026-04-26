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

# ---------------------------------------------------------------------------
# Document-type detection and role validation
# ---------------------------------------------------------------------------

# Patterns that identify a CV / resume (checked against the first chars).
_CV_PATTERNS = re.compile(
    r"curriculum\s+vitae|(?:^|\s)CV(?:\s|$|\b)|resume|lebenslauf|"
    r"données\s+personnelles|personal\s+data|dati\s+personali|persönliche\s+daten",
    re.IGNORECASE,
)

# Patterns that identify a medical record.
_MEDICAL_PATTERNS = re.compile(
    r"cartella\s+clinica|medical\s+record|dossier\s+m[ée]dical|krankenakte|"
    r"anamnesi|diagnosi|ricovero|paziente\s*:",
    re.IGNORECASE,
)

# Patterns that identify a legal act / court document.
_LEGAL_PATTERNS = re.compile(
    r"tribunale|sentenza|ricorso|ricorrente|convenuto|"
    r"n\.\s*r\.?g\.?|p\.?q\.?m\.?|udienza|ill\.?mo|"
    r"corte\s+d[i']\s+appello|procura\s+della\s+repubblica",
    re.IGNORECASE,
)

# Patterns that identify a contract (rental / employment / commercial).
_CONTRACT_PATTERNS = re.compile(
    r"contratto\s+di\s+(?:locazione|lavoro|affitto|fornitura|prestazione)|"
    r"locatore|conduttore|datore\s+di\s+lavoro|tra\s+le\s+parti|"
    r"\bart(?:icolo)?\.?\s*1\b|le\s+parti\s+convengono",
    re.IGNORECASE,
)

# Patterns that identify an invoice / commercial document.
_INVOICE_PATTERNS = re.compile(
    r"\bfattura\b|\binvoice\b|p\.?\s*iva|partita\s+iva|"
    r"imponibile|aliquota\s+iva|spett\.?le|nr?\.?\s*fattura|"
    r"causale|importo\s+totale",
    re.IGNORECASE,
)

# Patterns that identify a generic letter / written communication.
# Kept as a last-resort fallback because these markers are very generic.
_LETTER_PATTERNS = re.compile(
    r"egregio|gentile|in\s+fede|cordiali\s+saluti|distinti\s+saluti|"
    r"oggetto\s*:",
    re.IGNORECASE,
)

# Roles that are ONLY valid for specific document types.
# If a role appears outside its allowed context, it is remapped.
_ROLE_CONSTRAINTS: dict[str, dict] = {
    "cv": {
        # In a CV, "paziente" is never correct — remap to "candidato"
        "paziente": "candidato",
        "medico": "candidato",
        "infermiere": "candidato",
    },
    "medical": {
        # In a medical record, "candidato" is never correct
        "candidato": "paziente",
    },
    "contract": {
        # A contract has no candidato/paziente
        "candidato": "dipendente",
        "paziente": "controparte",
    },
    "invoice": {
        # An invoice has no candidato/paziente
        "candidato": "cliente",
        "paziente": "cliente",
        "locatore": "fornitore",
        "conduttore": "cliente",
    },
    "legal": {
        # In a legal act, the main person is ricorrente, not candidato/paziente
        "candidato": "ricorrente",
        "paziente": "ricorrente",
    },
    # "letter" intentionally left without strict remaps — generic context
    "letter": {},
}


# Allowed override values from the API (frontend dropdown).
ALLOWED_DOC_TYPES = {"cv", "medical", "contract", "invoice", "legal", "letter"}


def _detect_doc_type(content: str) -> str | None:
    """Heuristic document-type detection from the first 800 characters.

    Order matters: more specific markers (CV, medical, legal) are checked
    before more ambiguous ones (contract → invoice → letter).
    """
    head = content[:800]
    if _CV_PATTERNS.search(head):
        return "cv"
    if _MEDICAL_PATTERNS.search(head):
        return "medical"
    if _LEGAL_PATTERNS.search(head):
        return "legal"
    if _CONTRACT_PATTERNS.search(head):
        return "contract"
    if _INVOICE_PATTERNS.search(head):
        return "invoice"
    if _LETTER_PATTERNS.search(head):
        return "letter"
    return None


def _validate_roles(
    entities: list[Entity],
    doc_type: str | None,
) -> None:
    """Correct roles that are invalid for the detected document type."""
    if doc_type is None:
        return
    constraints = _ROLE_CONSTRAINTS.get(doc_type)
    if not constraints:
        return
    for entity in entities:
        if entity.category not in _ROLE_CATEGORIES:
            continue
        if entity.semantic_role and entity.semantic_role in constraints:
            old_role = entity.semantic_role
            entity.semantic_role = constraints[old_role]
            logger.debug(
                "Role validation: corrected '%s' role from '%s' to '%s' "
                "(doc_type=%s).",
                entity.value, old_role, entity.semantic_role, doc_type,
            )


def _propagate_roles(entities: list[Entity]) -> None:
    """Propagate semantic_role from resolved entities to unresolved ones that
    share the same entity_type and whose value is a substring match.

    Handles cases where NER produces a slightly different surface form than the
    LLM (e.g. "Delta S.r.l" vs "Delta S.r.l.") and the ownership lookup
    misses the match.
    """
    resolved = [e for e in entities if e.semantic_role]
    for entity in entities:
        if entity.semantic_role:
            continue
        e_low = entity.value.strip().lower().rstrip(".")
        for donor in resolved:
            if donor.entity_type != entity.entity_type:
                continue
            d_low = donor.value.strip().lower().rstrip(".")
            if e_low in d_low or d_low in e_low:
                entity.semantic_role = donor.semantic_role
                logger.debug(
                    "Role propagation: '%s' inherited role '%s' from '%s'.",
                    entity.value, donor.semantic_role, donor.value,
                )
                break


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

    def assign_roles(
        self,
        content: str,
        entities: List[Entity],
        doc_type_override: str | None = None,
    ) -> tuple[List[Entity], str | None]:
        """
        Two-pass enrichment:
          1. Assigns a contextual role to person/organisation entities.
          2. Resolves ownership of all other entities (emails, addresses,
             phones, dates, IDs, IBANs) by linking them to the person/org
             they belong to.

        ``doc_type_override`` lets the caller force the detected document
        type (e.g. coming from the user via the frontend dropdown). When
        ``None`` the heuristic ``_detect_doc_type`` is used.

        Returns a tuple ``(entities, doc_type)`` so the caller can surface
        the detected/used document type to the frontend.
        """
        # Resolve doc_type up-front so we always return a value even on
        # the early-exit path (no person/org entities).
        if doc_type_override and doc_type_override in ALLOWED_DOC_TYPES:
            doc_type: str | None = doc_type_override
        else:
            doc_type = _detect_doc_type(content)

        # --- Pass 1: role assignment for persons / organisations -----------
        role_entities = [e for e in entities if e.category in _ROLE_CATEGORIES]

        if not role_entities:
            return entities, doc_type

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
            if not assignments:
                logger.warning(
                    "SemanticRoleService pass 1: LLM returned no parseable "
                    "assignments. doc_type=%s. Raw output (first 500 chars): %s",
                    doc_type, (raw or "")[:500],
                )
        except Exception as exc:
            logger.warning("SemanticRoleService failed: %s. Roles will be empty.", exc)
            assignments = {}

        for entity in entities:
            if entity.category in _ROLE_CATEGORIES:
                role = assignments.get(entity.value)
                if role:
                    entity.semantic_role = role

        logger.info(
            "SemanticRoleService pass 1 (roles): doc_type=%s, %d/%d "
            "person/org entities assigned a role",
            doc_type,
            sum(1 for e in entities if e.semantic_role and e.category in _ROLE_CATEGORIES),
            len(role_entities),
        )

        # --- Pass 1.5: validate roles against document type ---------------
        _validate_roles(entities, doc_type)

        # --- Pass 2: ownership resolution for all other entities ----------
        self._assign_ownership(content, entities)

        # --- Pass 3: propagate roles to unresolved entities ---------------
        _propagate_roles(entities)

        return entities, doc_type

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
            if not ownership:
                logger.warning(
                    "SemanticRoleService pass 2: LLM returned no parseable "
                    "ownership. Raw output (first 500 chars): %s",
                    (raw or "")[:500],
                )
        except Exception as exc:
            logger.warning(
                "SemanticRoleService ownership resolution failed: %s. "
                "Non-person entities will keep generic placeholders.", exc,
            )
            return

        # Build the set of valid owner roles from pass 1
        valid_roles: set[str] = {
            e.semantic_role
            for e in entities
            if e.category in _ROLE_CATEGORIES and e.semantic_role
        }
        valid_roles.add("documento")

        # If there is exactly one person role, use it as the default for
        # unrecognised ownership roles (the LLM sometimes returns generic
        # labels like "persona" that don't match any assigned role).
        person_roles = [
            e.semantic_role
            for e in entities
            if e.category == EntityCategory.PERSONE_FISICHE and e.semantic_role
        ]
        unique_person_roles = set(person_roles)
        default_person_role = (
            unique_person_roles.pop() if len(unique_person_roles) == 1 else None
        )

        # Apply ownership in-place, validating against the known role set.
        assigned = 0
        for entity in entities:
            if entity.category not in _ROLE_CATEGORIES:
                owner_role = ownership.get(entity.value)
                if owner_role:
                    if owner_role not in valid_roles and default_person_role:
                        logger.debug(
                            "Ownership normalisation: remapped '%s' owner "
                            "from '%s' to '%s' (not in valid roles).",
                            entity.value, owner_role, default_person_role,
                        )
                        owner_role = default_person_role
                    entity.semantic_role = owner_role
                    assigned += 1

        logger.info(
            "SemanticRoleService pass 2 (ownership): %d/%d data entities "
            "assigned an owner",
            assigned, len(data_entities),
        )
