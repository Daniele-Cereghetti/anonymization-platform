"""
Unit tests for _is_semantic_false_positive in identification_service.

Layer 3 (spaCy POS filter) is skipped by passing nlp_obj=None so that
these tests remain purely unit-level with no model loading.
"""

from app.services.identification_service import _is_semantic_false_positive


# ---- Structural types bypass the filter entirely ----


class TestStructuralTypesSkipped:
    def test_email_not_filtered(self):
        assert _is_semantic_false_positive("test@example.com", "EMAIL", nlp_obj=None) is False

    def test_iban_not_filtered(self):
        assert _is_semantic_false_positive("IT60X0542811101000000123456", "IBAN_CODE", nlp_obj=None) is False

    def test_phone_not_filtered(self):
        assert _is_semantic_false_positive("+39 02 1234567", "PHONE_NUMBER", nlp_obj=None) is False


# ---- Layer 1: deny-list ----


class TestDenyList:
    # -- exact match per language --

    def test_italian_exact(self):
        assert _is_semantic_false_positive("Formazione", "PERSON", nlp_obj=None, lang="it") is True

    def test_german_exact(self):
        assert _is_semantic_false_positive("Profil", "PERSON", nlp_obj=None, lang="de") is True

    def test_french_exact(self):
        assert _is_semantic_false_positive("Compétences", "PERSON", nlp_obj=None, lang="fr") is True

    def test_english_exact(self):
        assert _is_semantic_false_positive("Skills", "PERSON", nlp_obj=None, lang="en") is True

    def test_common_entry(self):
        assert _is_semantic_false_positive("Agile", "PERSON", nlp_obj=None, lang="it") is True

    def test_case_insensitive(self):
        assert _is_semantic_false_positive("FORMAZIONE", "PERSON", nlp_obj=None, lang="it") is True

    # -- first-line match --

    def test_first_line_match(self):
        assert _is_semantic_false_positive(
            "Formazione\n- Laurea Magistrale in Informatica", "PERSON", nlp_obj=None, lang="it",
        ) is True

    def test_first_line_with_trailing_colon(self):
        assert _is_semantic_false_positive(
            "Competenze:", "PERSON", nlp_obj=None, lang="it",
        ) is True

    # -- prefix match --

    def test_prefix_match(self):
        assert _is_semantic_false_positive(
            "Profilo Project Manager", "PERSON", nlp_obj=None, lang="it",
        ) is True


# ---- Layer 2: partial IBAN regex ----


class TestPartialIban:
    def test_short_iban_fragment(self):
        assert _is_semantic_false_positive("IT60 X054", "LOCATION", nlp_obj=None) is True

    def test_full_iban_not_filtered(self):
        assert _is_semantic_false_positive(
            "IT60X0542811101000000123456", "LOCATION", nlp_obj=None,
        ) is False


# ---- Real entities pass all layers ----


class TestRealEntitiesPass:
    def test_real_person_name(self):
        assert _is_semantic_false_positive("Mario Rossi", "PERSON", nlp_obj=None) is False

    def test_real_organization(self):
        assert _is_semantic_false_positive("Università di Milano", "ORGANIZATION", nlp_obj=None) is False

    def test_real_location(self):
        assert _is_semantic_false_positive("Via Roma 15", "LOCATION", nlp_obj=None) is False
