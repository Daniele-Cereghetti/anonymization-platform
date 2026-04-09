import re

from app.services.identification_service import _CH_AVS_NUMBER_REGEX

_RE = re.compile(_CH_AVS_NUMBER_REGEX)


def test_valid_avs_matches():
    assert _RE.search("756.1234.5678.97")
    assert _RE.search("Il numero AVS è 756.9999.0000.12 del paziente")


def test_invalid_avs_no_match():
    assert _RE.search("757.1234.5678.97") is None   # non inizia con 756
    assert _RE.search("756.123.5678.97") is None     # gruppo troppo corto
    assert _RE.search("756.1234.5678.123") is None   # ultimo gruppo troppo lungo
    assert _RE.search("7561234567897") is None        # senza punti
