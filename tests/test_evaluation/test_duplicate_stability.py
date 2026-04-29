"""Tests para src/evaluation/duplicate_stability.py — T19."""

import pandas as pd
import pytest

from src.evaluation.duplicate_stability import classify_pairs, compute_pair_metrics


def test_classify_4_layers(tmp_path):
    """4 camadas distinguidas corretamente."""
    df = pd.DataFrame([
        {"report_id": "RPT_001", "report_text_translated": "texto a"},
        {"report_id": "RPT_001", "report_text_translated": "texto a'"},
        {"report_id": "RPT_002", "report_text_translated": "texto b"},
        {"report_id": "RPT_002", "report_text_translated": ""},  # invalid
        {"report_id": "RPT_003", "report_text_translated": "x"},  # singleton — não candidate
    ])
    audit = tmp_path / "audit.jsonl"
    audit.write_text(
        '{"report_id":"RPT_001","prompt_hash":"abc"}\n', encoding="utf-8"
    )
    out = classify_pairs(df, str(audit))

    rpt001 = out[out["report_id"] == "RPT_001"].iloc[0]
    assert rpt001["valid"] and rpt001["effective"]
    assert rpt001["pair_type"] == "effective_duplicate"

    rpt002 = out[out["report_id"] == "RPT_002"].iloc[0]
    assert not rpt002["valid"]
    assert rpt002["exclusion_reason"] == "empty_translation"


def test_singleton_not_in_pairs():
    """Report_id sem duplicata não aparece no DataFrame de pairs."""
    df = pd.DataFrame([
        {"report_id": "RPT_X", "report_text_translated": "single"},
        {"report_id": "RPT_Y", "report_text_translated": "tem dois"},
        {"report_id": "RPT_Y", "report_text_translated": "tem dois bis"},
    ])
    out = classify_pairs(df, None)
    # Só RPT_Y é candidate (tem >1 linha)
    assert "RPT_X" not in out["report_id"].values
    assert "RPT_Y" in out["report_id"].values


def test_metrics_identical_pair():
    """Par idêntico: cosine=1, structural sempre match."""
    pt = "BI-RADS 4 mama esquerda 15mm sem calcificacoes"
    out = compute_pair_metrics(pt, pt, embedder=None, bert_scorer=None)
    assert out["exact_match_normalized"] is True
    assert out["chrf_pt_pt"] >= 99
    assert out["category_match"] is True
    assert out["measures_match"] is True
    assert out["laterality_match"] is True
    assert out["negation_match"] is True
    assert out["duplicate_structural_instability"] is False
    assert out["requires_mqm_review"] is False


def test_metrics_measure_swap():
    """Troca de medida (mm→cm): measures_match=False, structural_instability=True."""
    pt1 = "nódulo BI-RADS 4 de 15mm em mama direita"
    pt2 = "nódulo BI-RADS 4 de 15cm em mama direita"  # mm → cm
    out = compute_pair_metrics(pt1, pt2, embedder=None, bert_scorer=None)
    assert out["measures_match"] is False
    assert out["duplicate_structural_instability"] is True
    assert out["requires_mqm_review"] is True


def test_metrics_laterality_inversion():
    """Inversão de lateralidade: laterality_match=False."""
    pt1 = "lesão na mama esquerda"
    pt2 = "lesão na mama direita"
    out = compute_pair_metrics(pt1, pt2, embedder=None, bert_scorer=None)
    assert out["laterality_match"] is False
    assert out["duplicate_structural_instability"] is True
