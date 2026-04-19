"""
Unit tests for _build_replacement in anonymization_service.
"""

from collections import defaultdict

from app.domain.entities import Entity, EntityCategory
from app.services.anonymization_service import _build_replacement


def _ent(
    value: str,
    entity_type: str,
    category: EntityCategory,
    semantic_role: str | None = None,
) -> Entity:
    return Entity(value=value, entity_type=entity_type, category=category, semantic_role=semantic_role)


class TestRoleBasedLabels:
    """Persone fisiche / giuridiche → readable labels without brackets."""

    def test_person_with_semantic_role(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE, semantic_role="fornitore")

        result = _build_replacement(ent, counters)

        assert result == "fornitore1"

    def test_person_without_role(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE)

        result = _build_replacement(ent, counters)

        assert result == "persona1"

    def test_organization_without_role(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("Acme Srl", "nome_azienda", EntityCategory.PERSONE_GIURIDICHE)

        result = _build_replacement(ent, counters)

        assert result == "organizzazione1"

    def test_role_with_spaces_normalized(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent = _ent("Acme Srl", "nome_azienda", EntityCategory.PERSONE_GIURIDICHE, semantic_role="Sede Legale")

        result = _build_replacement(ent, counters)

        assert result == "sede_legale1"

    def test_counters_increment(self):
        counters: defaultdict[str, int] = defaultdict(int)
        ent1 = _ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE)
        ent2 = _ent("Luigi Bianchi", "nome_cognome", EntityCategory.PERSONE_FISICHE)

        r1 = _build_replacement(ent1, counters)
        r2 = _build_replacement(ent2, counters)

        assert r1 == "persona1"
        assert r2 == "persona2"


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
