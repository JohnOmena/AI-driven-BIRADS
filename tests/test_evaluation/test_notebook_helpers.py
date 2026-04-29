"""Tests para src/evaluation/notebook_helpers.py — T23 PRE-FLIGHT."""

import pandas as pd
import pytest

from src.evaluation.notebook_helpers import (
    median_with_ci,
    proportion_with_ci,
    rate_with_ci,
    build_executive_summary,
)


def test_median_with_ci_returns_tuple():
    """Helper retorna (mediana, ci_low, ci_high)."""
    m, lo, hi = median_with_ci([1, 2, 3, 4, 5], n_resamples=200)
    assert lo <= m <= hi


def test_proportion_with_ci_extreme_zero():
    """Wilson lida com 0/N (caso comum em H8: 0 erros críticos)."""
    p, lo, hi = proportion_with_ci(0, 100)
    assert p == 0.0
    assert lo == 0.0
    assert hi > 0  # CI superior > 0 mesmo com 0/N


def test_proportion_with_ci_extreme_full():
    """Wilson lida com N/N."""
    p, lo, hi = proportion_with_ci(100, 100)
    assert p == 1.0
    assert lo < 1.0  # CI inferior estrito menor que 1
    assert hi >= 0.999  # CI superior próximo de 1 (não 1.0 exato por floating-point)


def test_holm_correction_8_hypotheses():
    """Holm corrige 8 p-values mantendo FWER ≤ α."""
    from statsmodels.stats.multitest import multipletests
    p_raw = [0.04] * 8  # todos significativos sem correção
    reject, p_corr, _, _ = multipletests(p_raw, alpha=0.05, method="holm")
    # Holm: o pior caso = 0.04 * 8 = 0.32 → não rejeita nenhum
    assert not any(reject)


def test_executive_summary_required_dimensions():
    """Tabela executiva contém as dimensões essenciais."""
    mock_records = [
        {"overall_passed": True, "clinical_pass": True, "composite_score": 95,
         "validations": {"audit_deepseek": {"has_critical_error": False}}}
    ] * 100
    mock_summaries = {
        "intrinsic": {"bertscore_f1_median": 0.95},
        "lexical":   {"overall_acceptable_rate": 0.998},
        "duplicate": {"median_cosine_pt_pt": 0.99},
    }
    summary = build_executive_summary(mock_records, mock_summaries)
    dims = set(summary["Dimensão"])
    expected = {
        "Volume", "Aprovação", "Erro crítico (H8)",
        "Semântica (H1)", "Léxico (H2)", "Estabilidade (H5)",
    }
    assert expected.issubset(dims)


def test_executive_summary_three_approval_rates():
    """Três taxas de aprovação separadas (Ajuste #5: clinical/overall/critical)."""
    mock_records = [
        {"overall_passed": True, "clinical_pass": True, "composite_score": 95,
         "validations": {"audit_deepseek": {"has_critical_error": False}}}
    ] * 50 + [
        {"overall_passed": False, "clinical_pass": True, "composite_score": 88,
         "validations": {"audit_deepseek": {"has_critical_error": False}}}
    ] * 30
    summary = build_executive_summary(mock_records, {})
    aprovacao_rows = summary[summary["Dimensão"] == "Aprovação"]
    metricas = aprovacao_rows["Métrica"].tolist()
    assert any("clinical_pass" in m for m in metricas)
    assert any("overall_passed" in m for m in metricas)


def test_proportion_with_ci_zero_total():
    """total=0 → None safe."""
    p, lo, hi = proportion_with_ci(0, 0)
    assert p is None and lo is None and hi is None
