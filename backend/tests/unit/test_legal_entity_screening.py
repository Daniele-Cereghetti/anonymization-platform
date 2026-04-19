"""
Unit tests for legal entity screening signals in identification_service:
- _CORPORATE_SUFFIX_RE regex
- _reclassify_legal_entities() post-processing function
"""

from app.domain.entities import Entity, EntityCategory
from app.services.identification_service import (
    _CORPORATE_SUFFIX_RE,
    _reclassify_legal_entities,
)


def _ent(value, category=EntityCategory.PERSONE_FISICHE, entity_type="nome_cognome"):
    return Entity(value=value, category=category, entity_type=entity_type, source="llm")


# ---- Corporate suffix regex ----


class TestCorporateSuffixRegex:
    def test_srl_dotted(self):
        assert _CORPORATE_SUFFIX_RE.search("Rossi S.r.l.")

    def test_srl_compact(self):
        assert _CORPORATE_SUFFIX_RE.search("Rossi Srl")

    def test_spa(self):
        assert _CORPORATE_SUFFIX_RE.search("Fiat S.p.A.")

    def test_sas(self):
        assert _CORPORATE_SUFFIX_RE.search("Verdi S.a.s.")

    def test_snc(self):
        assert _CORPORATE_SUFFIX_RE.search("Bianchi S.n.c.")

    def test_gmbh(self):
        assert _CORPORATE_SUFFIX_RE.search("Müller GmbH")

    def test_ag(self):
        assert _CORPORATE_SUFFIX_RE.search("Novartis AG")

    def test_sa(self):
        assert _CORPORATE_SUFFIX_RE.search("Banca XYZ SA")

    def test_ltd(self):
        assert _CORPORATE_SUFFIX_RE.search("Acme Ltd.")

    def test_inc(self):
        assert _CORPORATE_SUFFIX_RE.search("Google Inc.")

    def test_sagl(self):
        assert _CORPORATE_SUFFIX_RE.search("Studio Bianchi Sagl")

    def test_llc(self):
        assert _CORPORATE_SUFFIX_RE.search("OpenAI LLC")

    def test_plc(self):
        assert _CORPORATE_SUFFIX_RE.search("Barclays PLC")

    def test_corp(self):
        assert _CORPORATE_SUFFIX_RE.search("Microsoft Corp.")

    def test_no_match_plain_name(self):
        assert _CORPORATE_SUFFIX_RE.search("Mario Rossi") is None

    def test_no_match_location(self):
        assert _CORPORATE_SUFFIX_RE.search("Via Roma 15") is None


# ---- Reclassification function ----


class TestReclassifyLegalEntities:
    def test_suffix_reclassified(self):
        entities = [_ent("Rossi S.r.l.")]
        result = _reclassify_legal_entities(entities, "Contratto con Rossi S.r.l.")
        assert result[0].category == EntityCategory.PERSONE_GIURIDICHE
        assert result[0].entity_type == "nome_azienda"

    def test_plain_person_not_reclassified(self):
        entities = [_ent("Mario Rossi")]
        result = _reclassify_legal_entities(entities, "Il signor Mario Rossi")
        assert result[0].category == EntityCategory.PERSONE_FISICHE

    def test_already_giuridica_unchanged(self):
        entities = [_ent("Acme Srl", EntityCategory.PERSONE_GIURIDICHE, "nome_azienda")]
        result = _reclassify_legal_entities(entities, "Acme Srl con sede a Milano")
        assert result[0].category == EntityCategory.PERSONE_GIURIDICHE
        assert result[0].entity_type == "nome_azienda"

    def test_contextual_sede_legale(self):
        entities = [_ent("Bianchi & Partners")]
        text = "La sede legale di Bianchi & Partners si trova in Via Roma 1."
        result = _reclassify_legal_entities(entities, text)
        assert result[0].category == EntityCategory.PERSONE_GIURIDICHE

    def test_contextual_ragione_sociale(self):
        entities = [_ent("Studio Verdi")]
        text = "Ragione sociale: Studio Verdi, con sede a Lugano."
        result = _reclassify_legal_entities(entities, text)
        assert result[0].category == EntityCategory.PERSONE_GIURIDICHE

    def test_contextual_registro_imprese(self):
        entities = [_ent("Alfa Consulting")]
        text = "Alfa Consulting iscritta al registro imprese di Milano."
        result = _reclassify_legal_entities(entities, text)
        assert result[0].category == EntityCategory.PERSONE_GIURIDICHE

    def test_no_context_no_reclassification(self):
        entities = [_ent("Bianchi & Partners")]
        text = "Bianchi & Partners ha firmato il documento."
        result = _reclassify_legal_entities(entities, text)
        assert result[0].category == EntityCategory.PERSONE_FISICHE

    def test_multiple_entities_selective(self):
        entities = [
            _ent("Rossi S.r.l."),
            _ent("Mario Bianchi"),
        ]
        text = "Rossi S.r.l. rappresentata da Mario Bianchi"
        result = _reclassify_legal_entities(entities, text)
        assert result[0].category == EntityCategory.PERSONE_GIURIDICHE  # suffix
        assert result[1].category == EntityCategory.PERSONE_FISICHE     # no signal
