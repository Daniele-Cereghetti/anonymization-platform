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


# ---------------------------------------------------------------------------
# Localisation of placeholder labels
# ---------------------------------------------------------------------------
# Internal role taxonomy and structured-data labels are kept in Italian (the
# canonical form used by the LLM prompt and validation logic). Just before a
# placeholder is rendered into the anonymised document we translate each token
# of the label into the document language so that the user sees coherent
# placeholders (e.g. an English CV gets [CANDIDATE_1], not [CANDIDATO_1]).
#
# The dict is keyed by the lowercase Italian token. Each inner dict provides
# UPPERCASE translations for every supported language ("en", "fr", "de").
# Italian is the no-op default and not represented here. Tokens not present in
# this table fall through unchanged — a safe fallback for ad-hoc roles the LLM
# may occasionally emit.
_LABEL_TRANSLATIONS: dict[str, dict[str, str]] = {
    # Structured-data category labels (from _BRACKET_PLACEHOLDER values)
    "contatto":          {"en": "CONTACT",         "fr": "CONTACT",         "de": "KONTAKT"},
    "id":                {"en": "ID",              "fr": "ID",              "de": "ID"},
    "dato_fin":          {"en": "FIN_DATA",        "fr": "DONNEE_FIN",      "de": "FIN_DATEN"},
    "data":              {"en": "DATE",            "fr": "DATE",            "de": "DATUM"},
    # Type-specific labels (from _TYPE_PLACEHOLDER values)
    "email":             {"en": "EMAIL",           "fr": "EMAIL",           "de": "EMAIL"},
    "telefono":          {"en": "PHONE",           "fr": "TELEPHONE",       "de": "TELEFON"},
    "indirizzo":         {"en": "ADDRESS",         "fr": "ADRESSE",         "de": "ADRESSE"},
    "cap":               {"en": "ZIP",             "fr": "CP",              "de": "PLZ"},
    "url":               {"en": "URL",             "fr": "URL",             "de": "URL"},
    "iban":              {"en": "IBAN",            "fr": "IBAN",            "de": "IBAN"},
    "carta":             {"en": "CARD",            "fr": "CARTE",           "de": "KARTE"},
    "conto":             {"en": "ACCOUNT",         "fr": "COMPTE",          "de": "KONTO"},
    "bic":               {"en": "BIC",             "fr": "BIC",             "de": "BIC"},
    "codice_fiscale":    {"en": "TAX_ID",          "fr": "CODE_FISCAL",     "de": "STEUER_ID"},
    "passaporto":        {"en": "PASSPORT",        "fr": "PASSEPORT",       "de": "REISEPASS"},
    "patente":           {"en": "LICENSE",         "fr": "PERMIS",          "de": "FUEHRERSCHEIN"},
    "carta_identita":    {"en": "ID_CARD",         "fr": "CARTE_IDENTITE",  "de": "PERSONALAUSWEIS"},
    "tessera_sanitaria": {"en": "HEALTH_CARD",     "fr": "CARTE_SANTE",     "de": "GESUNDHEITSKARTE"},
    "targa":             {"en": "PLATE",           "fr": "PLAQUE",          "de": "KENNZEICHEN"},
    "avs":               {"en": "AVS",             "fr": "AVS",             "de": "AHV"},
    "partita_iva":       {"en": "VAT",             "fr": "TVA",             "de": "USTID"},
    "licenza":           {"en": "LICENSE_NO",      "fr": "LICENCE",         "de": "LIZENZ"},
    "data_nascita":      {"en": "BIRTH_DATE",      "fr": "DATE_NAISSANCE",  "de": "GEBURTSDATUM"},
    "data_contratto":    {"en": "CONTRACT_DATE",   "fr": "DATE_CONTRAT",    "de": "VERTRAGSDATUM"},
    "scadenza":          {"en": "EXPIRY",          "fr": "ECHEANCE",        "de": "ABLAUF"},
    # Person-subtype labels
    "luogo_nascita":     {"en": "BIRTH_PLACE",     "fr": "LIEU_NAISSANCE",  "de": "GEBURTSORT"},
    "nazionalita":       {"en": "NATIONALITY",     "fr": "NATIONALITE",     "de": "STAATSANGEH"},
    # Generic fallbacks
    "persona":           {"en": "PERSON",          "fr": "PERSONNE",        "de": "PERSON"},
    "organizzazione":    {"en": "ORGANIZATION",    "fr": "ORGANISATION",    "de": "ORGANISATION"},
    "entita":            {"en": "ENTITY",          "fr": "ENTITE",          "de": "ENTITAET"},
    # Person roles (semantic_role vocabulary)
    "candidato":              {"en": "CANDIDATE",        "fr": "CANDIDAT",         "de": "BEWERBER"},
    "paziente":               {"en": "PATIENT",          "fr": "PATIENT",          "de": "PATIENT"},
    "medico":                 {"en": "DOCTOR",           "fr": "MEDECIN",          "de": "ARZT"},
    "dottore":                {"en": "DOCTOR",           "fr": "DOCTEUR",          "de": "DOKTOR"},
    "infermiere":             {"en": "NURSE",            "fr": "INFIRMIER",        "de": "PFLEGER"},
    "avvocato":               {"en": "LAWYER",           "fr": "AVOCAT",           "de": "ANWALT"},
    "giudice":                {"en": "JUDGE",            "fr": "JUGE",             "de": "RICHTER"},
    "notaio":                 {"en": "NOTARY",           "fr": "NOTAIRE",          "de": "NOTAR"},
    "fornitore":              {"en": "SUPPLIER",         "fr": "FOURNISSEUR",      "de": "LIEFERANT"},
    "compratore":             {"en": "BUYER",            "fr": "ACHETEUR",         "de": "KAEUFER"},
    "venditore":              {"en": "SELLER",           "fr": "VENDEUR",          "de": "VERKAEUFER"},
    "locatore":               {"en": "LANDLORD",         "fr": "BAILLEUR",         "de": "VERMIETER"},
    "conduttore":             {"en": "TENANT",           "fr": "LOCATAIRE",        "de": "MIETER"},
    "datore_lavoro":          {"en": "EMPLOYER",         "fr": "EMPLOYEUR",        "de": "ARBEITGEBER"},
    "dipendente":             {"en": "EMPLOYEE",         "fr": "EMPLOYE",          "de": "ARBEITNEHMER"},
    "recruiter":              {"en": "RECRUITER",        "fr": "RECRUTEUR",        "de": "RECRUITER"},
    "testimone":              {"en": "WITNESS",          "fr": "TEMOIN",           "de": "ZEUGE"},
    "richiedente":            {"en": "APPLICANT",        "fr": "DEMANDEUR",        "de": "ANTRAGSTELLER"},
    "beneficiario":           {"en": "BENEFICIARY",      "fr": "BENEFICIAIRE",     "de": "BEGUENSTIGTER"},
    "consulente":             {"en": "CONSULTANT",       "fr": "CONSULTANT",       "de": "BERATER"},
    "dirigente":              {"en": "MANAGER",          "fr": "DIRIGEANT",        "de": "FUEHRUNGSKRAFT"},
    "amministratore":         {"en": "ADMINISTRATOR",    "fr": "ADMINISTRATEUR",   "de": "VERWALTER"},
    "rappresentante_legale":  {"en": "LEGAL_REP",        "fr": "REPRESENTANT_LEGAL","de": "GESETZL_VERTRETER"},
    "controparte":            {"en": "COUNTERPARTY",     "fr": "PARTIE_ADVERSE",   "de": "GEGENPARTEI"},
    "cliente":                {"en": "CLIENT",           "fr": "CLIENT",           "de": "KUNDE"},
    "ricorrente":             {"en": "CLAIMANT",         "fr": "REQUERANT",        "de": "KLAEGER"},
    # Organisation roles
    "azienda_fornitrice":     {"en": "SUPPLIER_COMPANY", "fr": "ENTREPRISE_FOURNISSEUR", "de": "LIEFERFIRMA"},
    "azienda_cliente":        {"en": "CLIENT_COMPANY",   "fr": "ENTREPRISE_CLIENTE",     "de": "KUNDENFIRMA"},
    "banca":                  {"en": "BANK",             "fr": "BANQUE",           "de": "BANK"},
    "ente_pubblico":          {"en": "PUBLIC_BODY",      "fr": "ORGANISME_PUBLIC", "de": "BEHOERDE"},
    "ospedale":               {"en": "HOSPITAL",         "fr": "HOPITAL",          "de": "KRANKENHAUS"},
    "clinica":                {"en": "CLINIC",           "fr": "CLINIQUE",         "de": "KLINIK"},
    "studio_legale":          {"en": "LAW_FIRM",         "fr": "CABINET_AVOCATS",  "de": "ANWALTSKANZLEI"},
    "studio_notarile":        {"en": "NOTARY_FIRM",      "fr": "ETUDE_NOTARIALE",  "de": "NOTARIAT"},
    "assicurazione":          {"en": "INSURER",          "fr": "ASSURANCE",        "de": "VERSICHERUNG"},
    "agenzia_immobiliare":    {"en": "REAL_ESTATE_AG",   "fr": "AGENCE_IMMO",      "de": "IMMOBILIENMAKLER"},
    "societa_datrice_lavoro": {"en": "EMPLOYER_COMPANY", "fr": "SOCIETE_EMPLOYEUR","de": "ARBEITGEBERFIRMA"},
    "societa_appaltatrice":   {"en": "CONTRACTOR",       "fr": "SOCIETE_PRESTATAIRE","de": "AUFTRAGNEHMERFIRMA"},
    "fondo_pensione":         {"en": "PENSION_FUND",     "fr": "FONDS_PENSION",    "de": "PENSIONSKASSE"},
    "ente_formazione":        {"en": "EDUCATION_BODY",   "fr": "ETABLISSEMENT_FORMATION", "de": "BILDUNGSEINRICHTUNG"},
    # Catch-all owner used by ownership resolution; never leaks into the
    # placeholder today (filtered out upstream), but mapped for completeness.
    "documento":              {"en": "DOCUMENT",         "fr": "DOCUMENT",         "de": "DOKUMENT"},
}

# Pre-computed list of multi-token (underscore-containing) keys, sorted by
# token count descending. Used for greedy longest-match translation so that
# composite labels like "DATA_NASCITA_CANDIDATO" translate "data_nascita" as a
# unit before falling back to single-token translation.
_MULTI_TOKEN_KEYS: list[tuple[str, int]] = sorted(
    [(k, k.count("_") + 1) for k in _LABEL_TRANSLATIONS if "_" in k],
    key=lambda x: x[1],
    reverse=True,
)


def _translate_label(label: str, language: str) -> str:
    """Translate a UPPERCASE composite label into ``language``.

    Italian is a no-op. For other languages we split the label on ``_`` and
    walk the tokens left-to-right, applying greedy longest-match against the
    multi-token keys first (so ``DATA_NASCITA`` resolves as one unit even when
    surrounded by other tokens). Tokens with no translation entry are kept
    verbatim — a safe fallback for ad-hoc roles outside the canonical set.
    """
    if language == "it" or language not in {"en", "fr", "de"}:
        return label

    tokens = label.split("_")
    out: list[str] = []
    i = 0
    while i < len(tokens):
        matched = False
        for key, n_tokens in _MULTI_TOKEN_KEYS:
            if i + n_tokens > len(tokens):
                continue
            window = "_".join(tokens[i:i + n_tokens]).lower()
            if window == key:
                out.append(_LABEL_TRANSLATIONS[key][language])
                i += n_tokens
                matched = True
                break
        if matched:
            continue
        single = tokens[i].lower()
        translation = _LABEL_TRANSLATIONS.get(single, {}).get(language)
        out.append(translation if translation else tokens[i])
        i += 1
    return "_".join(out)


def build_replacement(entity: Entity, counters: defaultdict, language: str = "it") -> str:
    """Public placeholder builder shared with the extraction preview.

    Mutates ``counters`` in-place (same defaultdict semantics as before).
    """
    return _build_replacement(entity, counters, language)


def _build_replacement(entity: Entity, counters: defaultdict, language: str = "it") -> str:
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

    label = _translate_label(label, language)
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
        language: str = "it",
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
            replacement = _build_replacement(entity, counters, language)
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
            language=language,
        )
