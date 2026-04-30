"""
Unit tests for _build_replacement in anonymization_service.
"""

from collections import defaultdict

from app.domain.entities import Entity, EntityCategory
from app.services.anonymization_service import _build_replacement, _translate_label


def _ent(
    value: str,
    entity_type: str,
    category: EntityCategory,
    semantic_role: str | None = None,
) -> Entity:
    return Entity(value=value, entity_type=entity_type, category=category, semantic_role=semantic_role)


class TestRoleBasedLabels:
    """Persone fisiche / giuridiche → bracketed [ROLE_N] / [PERSONA_N] labels."""

    def test_person_with_semantic_role(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE, semantic_role="fornitore")

        result = _build_replacement(ent, counters)

        assert result == "[FORNITORE_1]"

    def test_person_without_role(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE)

        result = _build_replacement(ent, counters)

        assert result == "[PERSONA_1]"

    def test_organization_without_role(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("Acme Srl", "nome_azienda", EntityCategory.PERSONE_GIURIDICHE)

        result = _build_replacement(ent, counters)

        assert result == "[ORGANIZZAZIONE_1]"

    def test_role_with_spaces_normalized(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("Acme Srl", "nome_azienda", EntityCategory.PERSONE_GIURIDICHE, semantic_role="Sede Legale")

        result = _build_replacement(ent, counters)

        assert result == "[SEDE_LEGALE_1]"

    def test_counters_increment(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent1 = _ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE)
        ent2 = _ent("Luigi Bianchi", "nome_cognome", EntityCategory.PERSONE_FISICHE)

        r1 = _build_replacement(ent1, counters)
        r2 = _build_replacement(ent2, counters)

        assert r1 == "[PERSONA_1]"
        assert r2 == "[PERSONA_2]"


class TestAnagraphicSubtypeLabels:
    """persone_fisiche sub-types (data_nascita, luogo_nascita, nazionalita)
    use a dedicated label suffixed with the owner's role when known."""

    def test_data_nascita_with_owner_role(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent(
            "14/02/1988", "data_nascita",
            EntityCategory.PERSONE_FISICHE, semantic_role="candidato",
        )

        result = _build_replacement(ent, counters)

        assert result == "[DATA_NASCITA_CANDIDATO_1]"

    def test_luogo_nascita_with_owner_role(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent(
            "Milano (MI), Italia", "luogo_nascita",
            EntityCategory.PERSONE_FISICHE, semantic_role="paziente",
        )

        result = _build_replacement(ent, counters)

        assert result == "[LUOGO_NASCITA_PAZIENTE_1]"

    def test_anagraphic_subtype_without_role_falls_back(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent(
            "14/02/1988", "data_nascita",
            EntityCategory.PERSONE_FISICHE,
        )

        result = _build_replacement(ent, counters)

        assert result == "[DATA_NASCITA_1]"

    def test_anagraphic_subtype_with_documento_role_falls_back(self):
        """'documento' is the catch-all for unattributed entities and must
        NOT leak into the placeholder."""
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent(
            "14/02/1988", "data_nascita",
            EntityCategory.PERSONE_FISICHE, semantic_role="documento",
        )

        result = _build_replacement(ent, counters)

        assert result == "[DATA_NASCITA_1]"


class TestBracketedLabels:
    """Other categories → [LABEL_N] format."""

    def test_email_type_placeholder(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("test@example.com", "email", EntityCategory.DATI_CONTATTO)

        result = _build_replacement(ent, counters)

        assert result == "[EMAIL_1]"

    def test_iban_type_placeholder(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("IT60X054...", "iban", EntityCategory.DATI_FINANZIARI)

        result = _build_replacement(ent, counters)

        assert result == "[IBAN_1]"

    def test_unknown_type_falls_back_to_category(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("some-value", "tipo_sconosciuto", EntityCategory.DATI_CONTATTO)

        result = _build_replacement(ent, counters)

        assert result == "[CONTATTO_1]"

    def test_counters_increment_bracketed(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent1 = _ent("test@a.com", "email", EntityCategory.DATI_CONTATTO)
        ent2 = _ent("test@b.com", "email", EntityCategory.DATI_CONTATTO)

        r1 = _build_replacement(ent1, counters)
        r2 = _build_replacement(ent2, counters)

        assert r1 == "[EMAIL_1]"
        assert r2 == "[EMAIL_2]"

    def test_data_nascita_type_placeholder(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("01/01/1990", "data_nascita", EntityCategory.DATI_TEMPORALI)

        result = _build_replacement(ent, counters)

        assert result == "[DATA_NASCITA_1]"

    def test_partita_iva_type_placeholder(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("01234567890", "partita_iva", EntityCategory.IDENTIFICATIVI)

        result = _build_replacement(ent, counters)

        assert result == "[PARTITA_IVA_1]"


class TestTranslateLabel:
    """`_translate_label` localises composite labels token-by-token."""

    def test_italian_is_noop(self):
        assert _translate_label("EMAIL_CANDIDATO", "it") == "EMAIL_CANDIDATO"
        assert _translate_label("PERSONA", "it") == "PERSONA"

    def test_unknown_language_is_noop(self):
        assert _translate_label("EMAIL", "es") == "EMAIL"

    def test_simple_token_translation(self):
        assert _translate_label("PERSONA", "en") == "PERSON"
        assert _translate_label("PERSONA", "fr") == "PERSONNE"
        assert _translate_label("PERSONA", "de") == "PERSON"

    def test_role_translation(self):
        assert _translate_label("CANDIDATO", "en") == "CANDIDATE"
        assert _translate_label("CANDIDATO", "fr") == "CANDIDAT"
        assert _translate_label("CANDIDATO", "de") == "BEWERBER"

    def test_composite_label(self):
        assert _translate_label("EMAIL_CANDIDATO", "en") == "EMAIL_CANDIDATE"
        assert _translate_label("INDIRIZZO_AZIENDA_FORNITRICE", "en") == "ADDRESS_SUPPLIER_COMPANY"

    def test_multi_token_key_resolved_greedily(self):
        # DATA_NASCITA must translate as a unit, not "DATE_BIRTH"
        assert _translate_label("DATA_NASCITA", "en") == "BIRTH_DATE"
        assert _translate_label("DATA_NASCITA_CANDIDATO", "en") == "BIRTH_DATE_CANDIDATE"
        assert _translate_label("LUOGO_NASCITA_PAZIENTE", "fr") == "LIEU_NAISSANCE_PATIENT"

    def test_unknown_token_kept_verbatim(self):
        # Tokens with no translation entry pass through unchanged
        assert _translate_label("EMAIL_FOOBAR", "en") == "EMAIL_FOOBAR"


class TestLanguageAwareBuildReplacement:
    """End-to-end check that `_build_replacement` honours the language arg."""

    def test_english_candidate(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE, semantic_role="candidato")

        assert _build_replacement(ent, counters, "en") == "[CANDIDATE_1]"

    def test_french_email_with_role(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("a@b.com", "email", EntityCategory.DATI_CONTATTO, semantic_role="candidato")

        assert _build_replacement(ent, counters, "fr") == "[EMAIL_CANDIDAT_1]"

    def test_german_birth_date_with_role(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("01/01/1990", "data_nascita", EntityCategory.PERSONE_FISICHE, semantic_role="paziente")

        assert _build_replacement(ent, counters, "de") == "[GEBURTSDATUM_PATIENT_1]"

    def test_italian_default_unchanged(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE, semantic_role="candidato")

        # Default arg must keep prior italian behaviour
        assert _build_replacement(ent, counters) == "[CANDIDATO_1]"
