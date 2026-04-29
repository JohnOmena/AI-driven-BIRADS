"""Tests para src/evaluation/intrinsic_metrics.py — T15."""

import pandas as pd
import pytest

from src.evaluation.intrinsic_metrics import (
    length_ratio,
    compute_chrf,
    compute_ter,
    compute_metrics_for_pair,
    build_summary,
    tokenize_basic,
)


# --- length_ratio ---

def test_length_ratio_identical():
    assert length_ratio("a b c", "x y z") == 1.0


def test_length_ratio_pt_shorter():
    assert length_ratio("a b c d", "x y") == 0.5


def test_length_ratio_pt_longer():
    assert length_ratio("a b", "x y z w") == 2.0


def test_length_ratio_empty_es():
    assert length_ratio("", "x y") == 0.0


# --- chrF++ ---

def test_chrf_identical_strings_high_score():
    score = compute_chrf("calcificación benigna", "calcificación benigna")
    assert score >= 99.0


def test_chrf_completely_different_low_score():
    score = compute_chrf("calcificación benigna", "lorem ipsum")
    assert score < 30.0


def test_chrf_close_morphology_high_score():
    """Línguas próximas com flexão similar — chrF deve detectar."""
    # Espera-se chrF alto mesmo com mudança de gênero/número
    score = compute_chrf("masa espiculada", "massa espiculada")
    assert score > 50.0  # alta semelhança caractere-nível


# --- TER ---

def test_ter_identical_zero():
    assert compute_ter("texto igual", "texto igual") == 0.0


def test_ter_completely_different_high():
    score = compute_ter("texto curto", "totalmente outro conteúdo aqui")
    assert score > 0.5  # > 50% edits


# --- compute_metrics_for_pair (sem modelos pesados) ---

def test_compute_metrics_no_models():
    """Sem embedder/bert_scorer, retorna só length_ratio + chrf + ter."""
    metrics = compute_metrics_for_pair("hola mundo", "olá mundo",
                                         embedder=None, bert_scorer=None)
    assert "length_ratio" in metrics
    assert "chrf" in metrics
    assert "ter" in metrics
    assert "cosine_sim" not in metrics
    assert "bertscore_f1" not in metrics


def test_no_bleu_in_output():
    """BLEU intencionalmente não consta no output (decisão T15)."""
    metrics = compute_metrics_for_pair("hola mundo", "olá mundo",
                                         embedder=None, bert_scorer=None)
    assert "bleu" not in metrics


# --- tokenize_basic ---

def test_tokenize_basic_strips_whitespace():
    assert tokenize_basic("  a  b  c  ") == ["a", "b", "c"]


def test_tokenize_basic_empty():
    assert tokenize_basic("") == []


# --- build_summary ---

def test_build_summary_structure(tmp_path):
    df = pd.DataFrame([
        {"report_id": "RPT_1", "bertscore_f1": 0.95, "chrf": 67.0,
         "cosine_sim": 0.93, "length_ratio": 0.97, "ter": 0.20},
        {"report_id": "RPT_2", "bertscore_f1": 0.92, "chrf": 62.0,
         "cosine_sim": 0.89, "length_ratio": 1.02, "ter": 0.25},
    ])
    out = tmp_path / "summary.json"
    summary = build_summary(df, str(out))

    assert summary["n_records"] == 2
    assert "metrics_main" in summary
    assert "metrics_appendix" in summary
    assert "bleu_excluded" in summary  # explicit note
    assert summary["metrics_main"]["bertscore_f1"]["median"] > 0.9
    assert "bleu" not in summary["metrics_main"]
    assert "bleu" not in summary["metrics_appendix"]


def test_build_summary_headline_bertscore():
    """Headline `bertscore_f1_median` é registrado para T23."""
    df = pd.DataFrame([
        {"report_id": f"RPT_{i}", "bertscore_f1": 0.9 + i * 0.01,
         "chrf": 60, "cosine_sim": 0.9, "length_ratio": 1.0, "ter": 0.2}
        for i in range(10)
    ])
    summary = build_summary(df, "/tmp/_test_t15_summary.json")
    assert summary["bertscore_f1_median"] is not None
    assert summary["bertscore_f1_median"] > 0.9
