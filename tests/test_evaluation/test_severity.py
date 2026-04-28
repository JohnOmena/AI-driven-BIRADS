"""Tests para src/evaluation/severity.py — T12.6 severity layer."""

from src.evaluation.severity import (
    apply_severity_override,
    count_by_severity,
    has_critical,
    MECHANICAL_CRITICAL_CRITERIA,
    LLM_JUDGED_CRITERIA,
    VALID_SEVERITIES,
)


# --- Override mecânico (C2/C3/C4/C6) ---

def test_c2_c3_c4_c6_forced_critical_regardless_of_llm():
    """Critérios mecânicos sempre viram critical, ignoram severity do LLM."""
    incs = [
        {"criterio": "C2", "severity": "minor"},     # LLM errou
        {"criterio": "C3", "severity": "major"},
        {"criterio": "C4"},                          # sem severity do LLM
        {"criterio": "C6", "severity": "critical"},
    ]
    out = apply_severity_override(incs)
    for o in out:
        assert o["severity"] == "critical"
        assert o["severity_method"] == "mechanical"


def test_mechanical_preserves_llm_raw():
    """severity_llm_raw guarda o que o LLM disse (auditoria)."""
    incs = [{"criterio": "C2", "severity": "minor"}]
    out = apply_severity_override(incs)
    assert out[0]["severity_llm_raw"] == "minor"
    assert out[0]["severity"] == "critical"  # override venceu


def test_mechanical_with_full_criterion_name():
    """Funciona mesmo quando auditor retorna 'C2_categoria_birads'."""
    incs = [{"criterio": "C2_categoria_birads", "severity": "minor"}]
    out = apply_severity_override(incs)
    assert out[0]["severity"] == "critical"
    assert out[0]["severity_method"] == "mechanical"


# --- LLM judgment (C1/C5/C7) ---

def test_c1_c5_c7_use_llm_classification():
    """LLM classifica em critérios subjetivos."""
    incs = [
        {"criterio": "C1", "severity": "minor"},
        {"criterio": "C5", "severity": "major"},
        {"criterio": "C7", "severity": "critical"},
    ]
    out = apply_severity_override(incs)
    assert out[0]["severity"] == "minor"  and out[0]["severity_method"] == "llm"
    assert out[1]["severity"] == "major"  and out[1]["severity_method"] == "llm"
    assert out[2]["severity"] == "critical" and out[2]["severity_method"] == "llm"


def test_c1_invalid_severity_falls_back_minor():
    """severity inválido em C1/C5/C7 -> minor (conservador)."""
    incs = [{"criterio": "C1", "severity": "extreme"}]
    out = apply_severity_override(incs)
    assert out[0]["severity"] == "minor"
    assert out[0]["severity_method"] == "fallback_minor"
    assert out[0]["severity_llm_raw"] == "extreme"  # preservado


def test_c1_missing_severity_falls_back_minor():
    """severity ausente em C1/C5/C7 -> minor."""
    incs = [{"criterio": "C5"}]
    out = apply_severity_override(incs)
    assert out[0]["severity"] == "minor"
    assert out[0]["severity_method"] == "fallback_minor"
    assert out[0]["severity_llm_raw"] is None


# --- Critério desconhecido ---

def test_unknown_criterion_defaults_minor():
    """Critério fora de C1-C7 -> minor + flag unknown_criterion."""
    incs = [{"criterio": "C99", "severity": "critical"}]
    out = apply_severity_override(incs)
    assert out[0]["severity"] == "minor"
    assert out[0]["severity_method"] == "unknown_criterion"


# --- Agregadores ---

def test_count_by_severity():
    incs = [
        {"severity": "critical"}, {"severity": "critical"},
        {"severity": "minor"},    {"severity": "major"},
    ]
    assert count_by_severity(incs) == {"critical": 2, "major": 1, "minor": 1}


def test_count_by_severity_empty():
    assert count_by_severity([]) == {"critical": 0, "major": 0, "minor": 0}


def test_has_critical():
    assert has_critical([{"severity": "critical"}, {"severity": "minor"}]) is True
    assert has_critical([{"severity": "minor"}, {"severity": "major"}]) is False
    assert has_critical([]) is False


# --- Imutabilidade do input ---

def test_apply_does_not_mutate_input():
    """apply_severity_override não modifica a lista original."""
    incs = [{"criterio": "C2", "severity": "minor"}]
    apply_severity_override(incs)
    assert incs[0]["severity"] == "minor"  # input intacto


# --- Constantes ---

def test_constants_match_decision():
    """As constantes refletem a decisão registrada no decision_log."""
    assert MECHANICAL_CRITICAL_CRITERIA == {"C2", "C3", "C4", "C6"}
    assert LLM_JUDGED_CRITERIA == {"C1", "C5", "C7"}
    assert VALID_SEVERITIES == {"critical", "major", "minor"}
