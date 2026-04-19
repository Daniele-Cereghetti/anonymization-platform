"""
Unit tests for all custom Presidio regex patterns defined in identification_service.
"""

import re

from app.services.identification_service import (
    _CH_AVS_NUMBER_REGEX,
    _IT_FISCAL_CODE_RE,
    _IT_IDENTITY_CARD_ELECTRONIC_REGEX,
    _IT_IDENTITY_CARD_REGEX,
    _IT_LICENSE_PLATE_REGEX,
    _IT_PARTITA_IVA_REGEX,
)


# ---- Swiss AVS / AHV number: 756.XXXX.XXXX.XX ----

_AVS_RE = re.compile(_CH_AVS_NUMBER_REGEX)


class TestAvsNumber:
    def test_valid_standalone(self):
        assert _AVS_RE.search("756.1234.5678.97")

    def test_valid_in_sentence(self):
        assert _AVS_RE.search("Il numero AVS è 756.9999.0000.12 del paziente")

    def test_invalid_wrong_prefix(self):
        assert _AVS_RE.search("757.1234.5678.97") is None

    def test_invalid_short_group(self):
        assert _AVS_RE.search("756.123.5678.97") is None

    def test_invalid_long_last_group(self):
        assert _AVS_RE.search("756.1234.5678.123") is None

    def test_invalid_no_dots(self):
        assert _AVS_RE.search("7561234567897") is None


# ---- Italian license plate: AA123BB (post-1994) ----

_PLATE_RE = re.compile(_IT_LICENSE_PLATE_REGEX)


class TestLicensePlate:
    def test_valid_standard(self):
        assert _PLATE_RE.search("FP123XY")

    def test_valid_in_sentence(self):
        assert _PLATE_RE.search("Targa del veicolo: AB456CD registrata")

    def test_invalid_too_few_digits(self):
        assert _PLATE_RE.search("AB12CD") is None

    def test_invalid_too_many_digits(self):
        assert _PLATE_RE.search("AB1234CD") is None

    def test_invalid_lowercase(self):
        assert _PLATE_RE.search("ab123cd") is None

    def test_invalid_wrong_structure(self):
        assert _PLATE_RE.search("123ABCD") is None


# ---- Italian identity card: AA1234567 (2 letters + 7 digits) ----

_ID_CARD_RE = re.compile(_IT_IDENTITY_CARD_REGEX)


class TestIdentityCard:
    def test_valid_standard(self):
        assert _ID_CARD_RE.search("AA1234567")

    def test_valid_in_sentence(self):
        assert _ID_CARD_RE.search("Carta d'identità: CA9876543 rilasciata il")

    def test_invalid_too_few_digits(self):
        assert _ID_CARD_RE.search("AA123456") is None

    def test_invalid_too_many_digits(self):
        assert _ID_CARD_RE.search("AA12345678") is None

    def test_invalid_three_letters(self):
        assert _ID_CARD_RE.search("AAA123456") is None

    def test_invalid_lowercase(self):
        assert _ID_CARD_RE.search("aa1234567") is None


# ---- Italian electronic identity card (CIE): CA12345AB (2 letters + 5 digits + 2 letters) ----

_ID_CARD_ELECTRONIC_RE = re.compile(_IT_IDENTITY_CARD_ELECTRONIC_REGEX)


class TestIdentityCardElectronic:
    def test_valid_standard(self):
        assert _ID_CARD_ELECTRONIC_RE.search("CA12345AB")

    def test_valid_in_sentence(self):
        assert _ID_CARD_ELECTRONIC_RE.search("CIE numero CA12345AB rilasciata il")

    def test_invalid_too_few_digits(self):
        assert _ID_CARD_ELECTRONIC_RE.search("CA1234AB") is None

    def test_invalid_too_many_digits(self):
        assert _ID_CARD_ELECTRONIC_RE.search("CA123456AB") is None

    def test_invalid_lowercase(self):
        assert _ID_CARD_ELECTRONIC_RE.search("ca12345ab") is None

    def test_no_collision_with_plate(self):
        # License plate has 3 digits (AB123CD), CIE has 5 — no overlap
        assert _ID_CARD_ELECTRONIC_RE.search("AB123CD") is None


# ---- Italian fiscal code: ABCDEF12G34H567I (6 letters + 2 digits + letter + ...) ----


class TestFiscalCode:
    def test_valid_standard(self):
        assert _IT_FISCAL_CODE_RE.match("RSSMRA85M01H501Z")

    def test_valid_lowercase(self):
        # regex has re.IGNORECASE
        assert _IT_FISCAL_CODE_RE.match("rssmra85m01h501z")

    def test_invalid_too_short(self):
        assert _IT_FISCAL_CODE_RE.match("RSSMRA85M01H501") is None

    def test_invalid_too_long(self):
        assert _IT_FISCAL_CODE_RE.match("RSSMRA85M01H501ZZ") is None

    def test_invalid_wrong_month_letter(self):
        # month letter must be in [A-EHLMPR-T], 'X' is not valid
        assert _IT_FISCAL_CODE_RE.match("RSSMRA85X01H501Z") is None

    def test_invalid_all_digits(self):
        assert _IT_FISCAL_CODE_RE.match("1234567890123456") is None


# ---- Italian Partita IVA: 11 digits ----

_PIVA_RE = re.compile(_IT_PARTITA_IVA_REGEX)


class TestPartitaIva:
    def test_valid_11_digits(self):
        assert _PIVA_RE.search("01234567890")

    def test_valid_in_sentence(self):
        assert _PIVA_RE.search("P.IVA 01234567890 della società")

    def test_invalid_10_digits(self):
        assert _PIVA_RE.search("0123456789") is None

    def test_invalid_12_digits_no_boundary(self):
        # 12 consecutive digits — no word boundary at position 11
        assert _PIVA_RE.search("012345678901") is None
