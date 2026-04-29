"""Tests para src/evaluation/consolidate.py — T20 PRE-FLIGHT.

Cobre lógica pura de overall_passed, clinical_pass, composite_score,
failure_reasons, warnings com mocks. NÃO testa I/O real (build_record/main
ficam para fase pós-T13).
"""

import pytest

from src.evaluation.consolidate import (
    overall_passed, clinical_pass, composite_score,
    failure_reasons, warnings, SCHEMA_VERSION,
)


def _v(**overrides):
    """Mock validations: tudo passa por default."""
    base = {
        "semantic":            {"bertscore_f1": 0.95, "passed": True},
        "structural":          {"all_structural_pass": True},
        "lexical_birads":      {"overall_acceptable_rate": 1.0, "passed": True},
        "modifier_agreement":  {"preservation_rate": 1.0, "passed": True},
        "audit_deepseek":      {"has_critical_error": False, "passed": True,
                                "audit_final_status": "approved"},
        "back_translation":    {"in_sample": False},
        "duplicate_stability": {"in_pair": False, "requires_review": False},
    }
    base.update(overrides)
    return base


# --- 9 testes core ---

def test_overall_passed_all_pass():
    assert overall_passed(_v()) is True


def test_overall_passed_with_modifier_abstain():
    """passed=null não reprova."""
    v = _v(modifier_agreement={"preservation_rate": None, "passed": None})
    assert overall_passed(v) is True


def test_overall_passed_modifier_fails_count():
    """passed=False reprova."""
    v = _v(modifier_agreement={"preservation_rate": 0.85, "passed": False})
    assert overall_passed(v) is False


def test_overall_passed_bt_not_in_sample_ignored():
    """in_sample=False não conta."""
    v = _v(back_translation={"in_sample": False})
    assert overall_passed(v) is True


def test_overall_passed_bt_in_sample_fails():
    """in_sample=True com False reprova."""
    v = _v(back_translation={"in_sample": True, "cosine_es_es_bt": 0.7, "passed": False})
    assert overall_passed(v) is False


def test_duplicate_stability_never_affects_overall_passed():
    """Mesmo com requires_review=True, não reprova (priorização, não aprovação)."""
    v = _v(duplicate_stability={"in_pair": True, "pair_type": "effective_duplicate",
                                  "cosine_pt_pt": 0.7, "structural_instability": True,
                                  "requires_review": True})
    assert overall_passed(v) is True


def test_composite_score_weights_renormalize_on_abstain():
    """Sem modifier (passed=null) e sem BT, pesos = 0.20+0.25+0.15+0.20 = 0.80."""
    v = _v(modifier_agreement={"preservation_rate": None, "passed": None})
    score = composite_score(v)
    expected = (95*0.20 + 100*0.25 + 100*0.15 + 100*0.20) / 0.80
    assert abs(score - round(expected, 2)) < 0.01


def test_failure_reasons_distinguishes_critical_vs_nonsuccess():
    v_crit = _v(audit_deepseek={"has_critical_error": True, "passed": False,
                                  "audit_final_status": "rejected"})
    assert "audit_critical" in failure_reasons(v_crit)

    v_nons = _v(audit_deepseek={"has_critical_error": False, "passed": False,
                                  "audit_final_status": "review"})
    assert "audit_nonsuccess" in failure_reasons(v_nons)


def test_schema_version_recorded():
    assert SCHEMA_VERSION == "2026-04-28-v1"


# --- Adicionais (alinhados ao Ajuste #5: clinical_pass + warnings) ---

def test_modifier_only_failure_is_clinical_pass():
    """Modifier reprovando mas resto OK:
      - overall_passed=False (agregado completo)
      - clinical_pass=True (modifier-only não é erro clínico)
      - warnings=['modifier_divergence']
    """
    v = _v(modifier_agreement={"preservation_rate": 0.85, "passed": False})
    assert overall_passed(v) is False
    assert clinical_pass(v) is True
    assert "modifier_divergence" in warnings(v)
    assert "modifier" in failure_reasons(v)


def test_clinical_pass_zero_with_critical_error():
    """has_critical_error=True → clinical_pass também False."""
    v = _v(audit_deepseek={"has_critical_error": True, "passed": False,
                            "audit_final_status": "rejected"})
    assert clinical_pass(v) is False
