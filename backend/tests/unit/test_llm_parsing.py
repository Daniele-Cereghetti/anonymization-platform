"""
Unit tests for LLM output parsing functions.

- _parse() in llm_ner_service — strips code fences, extracts JSON, validates EntityCategory
- _parse_assignments() in semantic_role_service — extracts dict from LLM output

No Ollama needed — these are pure string/JSON parsing functions.
"""

import json

from app.domain.entities import EntityCategory
from app.services.llm_ner_service import _parse
from app.services.semantic_role_service import _parse_assignments


# ---- _parse (llm_ner_service) ----


class TestParse:
    def test_clean_json(self):
        raw = json.dumps({
            "entities": [
                {"value": "Mario Rossi", "category": "persone_fisiche", "entity_type": "nome_cognome"},
            ]
        })

        result = _parse(raw, allowed_categories=[])

        assert len(result) == 1
        assert result[0].value == "Mario Rossi"
        assert result[0].category == EntityCategory.PERSONE_FISICHE

    def test_strips_code_fences(self):
        raw = '```json\n{"entities": [{"value": "test@example.com", "category": "dati_contatto", "entity_type": "email"}]}\n```'

        result = _parse(raw, allowed_categories=[])

        assert len(result) == 1
        assert result[0].value == "test@example.com"

    def test_filters_by_allowed_categories(self):
        raw = json.dumps({
            "entities": [
                {"value": "Mario Rossi", "category": "persone_fisiche", "entity_type": "nome_cognome"},
                {"value": "test@example.com", "category": "dati_contatto", "entity_type": "email"},
            ]
        })

        result = _parse(raw, allowed_categories=["dati_contatto"])

        assert len(result) == 1
        assert result[0].value == "test@example.com"

    def test_invalid_category_skipped(self):
        raw = json.dumps({
            "entities": [
                {"value": "Mario Rossi", "category": "categoria_inventata", "entity_type": "x"},
            ]
        })

        result = _parse(raw, allowed_categories=[])

        assert result == []

    def test_missing_value_key_skipped(self):
        raw = json.dumps({
            "entities": [
                {"category": "persone_fisiche", "entity_type": "nome_cognome"},
            ]
        })

        result = _parse(raw, allowed_categories=[])

        assert result == []

    def test_no_json_returns_empty(self):
        result = _parse("no json here at all", allowed_categories=[])

        assert result == []

    def test_malformed_json_returns_empty(self):
        result = _parse("{broken: json,}", allowed_categories=[])

        assert result == []

    def test_default_entity_type(self):
        raw = json.dumps({
            "entities": [
                {"value": "Mario Rossi", "category": "persone_fisiche"},
            ]
        })

        result = _parse(raw, allowed_categories=[])

        assert result[0].entity_type == "unknown"


# ---- _parse_assignments (semantic_role_service) ----


class TestParseAssignments:
    def test_clean_json(self):
        raw = json.dumps({
            "assignments": [
                {"value": "Mario Rossi", "role": "fornitore"},
            ]
        })

        result = _parse_assignments(raw)

        assert result == {"Mario Rossi": "fornitore"}

    def test_strips_code_fences(self):
        raw = '```json\n{"assignments": [{"value": "Mario Rossi", "role": "locatore"}]}\n```'

        result = _parse_assignments(raw)

        assert result == {"Mario Rossi": "locatore"}

    def test_role_normalized(self):
        raw = json.dumps({
            "assignments": [
                {"value": "Acme Srl", "role": "Sede Legale"},
            ]
        })

        result = _parse_assignments(raw)

        assert result["Acme Srl"] == "sede_legale"

    def test_empty_value_skipped(self):
        raw = json.dumps({
            "assignments": [
                {"value": "", "role": "fornitore"},
            ]
        })

        result = _parse_assignments(raw)

        assert result == {}

    def test_empty_role_skipped(self):
        raw = json.dumps({
            "assignments": [
                {"value": "Mario Rossi", "role": ""},
            ]
        })

        result = _parse_assignments(raw)

        assert result == {}

    def test_no_json_returns_empty(self):
        result = _parse_assignments("no json here")

        assert result == {}

    def test_malformed_json_returns_empty(self):
        result = _parse_assignments("{broken: json,}")

        assert result == {}
