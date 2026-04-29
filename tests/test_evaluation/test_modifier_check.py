"""Tests para src/evaluation/modifier_check.py — T18."""

import pytest

from src.evaluation.modifier_check import detect_form, diff_modifier_agreement


@pytest.fixture
def atlas_minimal():
    return {
        "categories": {
            "mass_margin": [{
                "pt_canonical": "espiculado",
                "bi_rads_code": "MASS_MARGIN_SPICULATED",
                "forms_pt": {"M-SING": "espiculado", "F-SING": "espiculada",
                             "M-PLUR": "espiculados", "F-PLUR": "espiculadas"},
                "forms_es": {"M-SING": "espiculado", "F-SING": "espiculada",
                             "M-PLUR": "espiculados", "F-PLUR": "espiculadas"},
            }]
        }
    }


def test_detect_form_singular_feminine(atlas_minimal):
    forms = atlas_minimal["categories"]["mass_margin"][0]["forms_pt"]
    assert detect_form("lesão espiculada na mama", forms) == "F-SING"


def test_detect_form_plural_feminine(atlas_minimal):
    forms = atlas_minimal["categories"]["mass_margin"][0]["forms_pt"]
    # 'espiculadas' deve ser detectado antes de 'espiculada' (ordem plural-first)
    assert detect_form("margens espiculadas e irregulares", forms) == "F-PLUR"


def test_detect_form_absent_returns_none(atlas_minimal):
    forms = atlas_minimal["categories"]["mass_margin"][0]["forms_pt"]
    assert detect_form("lesão circunscrita", forms) is None


def test_diff_preserved_no_divergence(atlas_minimal):
    es = "lesión espiculada en mama derecha"
    pt = "lesão espiculada em mama direita"
    out = diff_modifier_agreement(es, pt, atlas_minimal)
    assert out["n_divergences"] == 0
    assert out["preservation_rate"] == 1.0


def test_diff_gender_divergence_detected(atlas_minimal):
    es = "lesión espiculada"        # F-SING
    pt = "lesão espiculado"         # M-SING — divergência de gênero introduzida
    out = diff_modifier_agreement(es, pt, atlas_minimal)
    assert out["n_divergences"] == 1
    assert out["divergences"][0]["divergence_type"] == "gender"
    assert out["divergences"][0]["es_form"] == "F-SING"
    assert out["divergences"][0]["pt_form"] == "M-SING"


def test_diff_number_divergence_detected(atlas_minimal):
    es = "margen espiculada"        # F-SING
    pt = "margens espiculadas"      # F-PLUR — divergência de número
    out = diff_modifier_agreement(es, pt, atlas_minimal)
    assert out["n_divergences"] == 1
    assert out["divergences"][0]["divergence_type"] == "number"


def test_diff_adjective_only_in_es_ignored(atlas_minimal):
    es = "lesión espiculada"
    pt = "lesão sem características descritas"
    out = diff_modifier_agreement(es, pt, atlas_minimal)
    assert out["n_modifiers_compared"] == 0
    # Adjetivo só em ES não conta como divergência (T17 cobre ausência)
    assert out["modifier_coverage_pass"] is False  # n_compared=0


def test_coverage_pass_when_modifier_compared(atlas_minimal):
    es = "lesión espiculada"
    pt = "lesão espiculada"
    out = diff_modifier_agreement(es, pt, atlas_minimal)
    assert out["modifier_coverage_pass"] is True
    assert out["preservation_rate"] == 1.0


def test_preservation_rate_none_without_coverage(atlas_minimal):
    """Sem cobertura, preservation_rate = None (abstain), não 1.0."""
    out = diff_modifier_agreement("xxx", "yyy", atlas_minimal)
    assert out["modifier_coverage_pass"] is False
    assert out["preservation_rate"] is None
