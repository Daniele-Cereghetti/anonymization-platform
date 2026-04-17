"""
Unit tests for _overlaps and _merge in identification_service.
"""

from app.domain.entities import Entity, EntityCategory
from app.services.identification_service import _merge, _overlaps


def _ent(value: str, entity_type: str, category: EntityCategory, source: str = "ner") -> Entity:
    return Entity(value=value, entity_type=entity_type, category=category, source=source)


# ---- _overlaps ----


class TestOverlaps:
    def test_identical_strings(self):
        assert _overlaps("Mario Rossi", "Mario Rossi") is True

    def test_case_insensitive(self):
        assert _overlaps("Mario Rossi", "mario rossi") is True

    def test_substring_forward(self):
        assert _overlaps("Mario", "Mario Rossi") is True

    def test_substring_reverse(self):
        assert _overlaps("Mario Rossi", "Mario") is True

    def test_no_overlap(self):
        assert _overlaps("Mario", "Giovanni") is False

    def test_empty_string(self):
        assert _overlaps("", "qualsiasi") is True


# ---- _merge ----


class TestMerge:
    def test_semantic_confirmed_by_llm(self):
        ner = [_ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE)]
        llm = [_ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE, source="llm")]

        result = _merge(ner, llm)

        merged_ner = [e for e in result if e.source == "merged"]
        assert len(merged_ner) == 1
        assert merged_ner[0].value == "Mario Rossi"

    def test_semantic_not_confirmed(self):
        ner = [_ent("Formazione", "nome_cognome", EntityCategory.PERSONE_FISICHE)]
        llm = [_ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE, source="llm")]

        result = _merge(ner, llm)

        assert all(e.value != "Formazione" for e in result)

    def test_structural_not_covered(self):
        ner = [_ent("test@example.com", "email", EntityCategory.DATI_CONTATTO)]
        llm = [_ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE, source="llm")]

        result = _merge(ner, llm)

        added = [e for e in result if e.value == "test@example.com"]
        assert len(added) == 1
        assert added[0].source == "merged"

    def test_structural_already_covered(self):
        ner = [_ent("test@example.com", "email", EntityCategory.DATI_CONTATTO)]
        llm = [_ent("test@example.com", "email", EntityCategory.DATI_CONTATTO, source="llm")]

        result = _merge(ner, llm)

        assert sum(e.value == "test@example.com" for e in result) == 1

    def test_empty_inputs(self):
        assert _merge([], []) == []

    def test_only_llm(self):
        llm = [
            _ent("Mario Rossi", "nome_cognome", EntityCategory.PERSONE_FISICHE, source="llm"),
            _ent("test@example.com", "email", EntityCategory.DATI_CONTATTO, source="llm"),
        ]

        result = _merge([], llm)

        assert len(result) == 2
        assert all(e.source == "llm" for e in result)

    def test_only_ner_structural(self):
        ner = [
            _ent("test@example.com", "email", EntityCategory.DATI_CONTATTO),
            _ent("IT60X0542811101000000123456", "iban", EntityCategory.DATI_FINANZIARI),
        ]

        result = _merge(ner, [])

        assert len(result) == 2
        assert all(e.source == "merged" for e in result)
