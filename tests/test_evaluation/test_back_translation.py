"""Tests para src/evaluation/back_translation.py — T14.B.

Cobre lógica pura:
  - build_stratified_sample: must_include T22+T19, estratos por categoria, fill
  - calibrate_thresholds: p5 das duplicatas com floor

NÃO testa I/O real do main (depende de Gemini API e T14.A merge).
"""

import json

import numpy as np
import pandas as pd
import pytest


def _setup_fixtures(tmp_path, monkeypatch):
    """Cria fixtures mínimas em tmp_path e chdir para lá."""
    (tmp_path / "data").mkdir()
    (tmp_path / "results" / "translation").mkdir(parents=True)

    # 30 laudos PT, 5 categorias (1-5), 6 por categoria
    rows_pt = []
    for cat in range(1, 6):
        for i in range(6):
            rows_pt.append({
                "report_id":        f"RPT_{cat:02d}{i:02d}",
                "birads_label":     cat,
                "report_text_raw":  f"laudo cat {cat} i {i}",
            })
    pd.DataFrame(rows_pt).to_csv(tmp_path / "data" / "reports_translated_pt.csv",
                                  index=False)

    # translations.csv com 2 review/rejected (must-include T22)
    rows_tr = [
        {"report_id": "RPT_0100", "status": "review"},
        {"report_id": "RPT_0200", "status": "rejected"},
        {"report_id": "RPT_0300", "status": "approved"},
    ]
    pd.DataFrame(rows_tr).to_csv(tmp_path / "results" / "translation" / "translations.csv",
                                  index=False)

    # duplicate_pairs.csv com 1 effective (must-include T19)
    rows_dup = [
        {"report_id": "RPT_0400", "effective": True},
        {"report_id": "RPT_0500", "effective": False},
    ]
    pd.DataFrame(rows_dup).to_csv(tmp_path / "results" / "translation" / "duplicate_pairs.csv",
                                   index=False)

    monkeypatch.chdir(tmp_path)


def test_build_stratified_sample_must_include_t22_t19(tmp_path, monkeypatch):
    """T22 (review/rejected) + T19 (effective) aparecem na amostra."""
    _setup_fixtures(tmp_path, monkeypatch)
    from src.evaluation.back_translation import build_stratified_sample

    out = build_stratified_sample(target_n=20, seed=42)
    ids = set(out["report_ids"])
    assert "RPT_0100" in ids  # T22 review
    assert "RPT_0200" in ids  # T22 rejected
    assert "RPT_0400" in ids  # T19 effective
    # approved e non-effective NÃO são must-include — só entram se random fill pegar
    assert out["metadata"]["must_include_count"] == 3


def test_build_stratified_sample_actual_n_respects_target(tmp_path, monkeypatch):
    """actual_n ≤ target_n e ≤ população disponível."""
    _setup_fixtures(tmp_path, monkeypatch)
    from src.evaluation.back_translation import build_stratified_sample

    out = build_stratified_sample(target_n=20, seed=42)
    assert out["metadata"]["actual_n"] <= 20
    assert out["metadata"]["actual_n"] <= 30  # população total


def test_build_stratified_sample_seed_determinism(tmp_path, monkeypatch):
    """Mesmo seed → mesma amostra."""
    _setup_fixtures(tmp_path, monkeypatch)
    from src.evaluation.back_translation import build_stratified_sample

    out_a = build_stratified_sample(target_n=15, seed=123)
    # Re-run com mesmo seed
    out_b = build_stratified_sample(target_n=15, seed=123)
    assert out_a["report_ids"] == out_b["report_ids"]


def test_build_stratified_sample_writes_json(tmp_path, monkeypatch):
    """bt_sample_ids.json criado em results/translation/."""
    _setup_fixtures(tmp_path, monkeypatch)
    from src.evaluation.back_translation import build_stratified_sample

    build_stratified_sample(target_n=10, seed=42)
    sample_path = tmp_path / "results" / "translation" / "bt_sample_ids.json"
    assert sample_path.exists()
    data = json.loads(sample_path.read_text(encoding="utf-8"))
    assert "report_ids" in data
    assert "metadata" in data


def test_calibrate_thresholds_uses_floor_when_n_small():
    """n<30 duplicatas → fallback floor."""
    from src.evaluation.back_translation import calibrate_thresholds

    df_bt = pd.DataFrame([
        {"report_id": "A", "cosine_es_es_bt": 0.92,
         "bertscore_f1_es_es_bt": 0.91, "chrf_es_es_bt": 70.0},
    ])
    df_tr = pd.DataFrame([
        {"report_id": "A"}, {"report_id": "A"},  # duplicata
    ])
    out = calibrate_thresholds(df_bt, df_tr)
    # n=1 < 30 → floor
    assert out["thresholds"]["cosine_es_es_bt"]["p5"] == 0.85
    assert out["thresholds"]["chrf_es_es_bt"]["p5"] == 50.0
    assert "fallback_floor" in out["thresholds"]["cosine_es_es_bt"]


def test_calibrate_thresholds_uses_max_p5_floor():
    """p5 abaixo do floor → usa floor; p5 acima → usa p5."""
    from src.evaluation.back_translation import calibrate_thresholds

    # 30 duplicatas com cosine alto (todos 0.95) → p5=0.95 > floor 0.85
    n = 30
    rows_bt = []
    rows_tr = []
    for i in range(n):
        rid = f"DUP_{i:03d}"
        rows_bt.append({"report_id": rid, "cosine_es_es_bt": 0.95,
                         "bertscore_f1_es_es_bt": 0.95, "chrf_es_es_bt": 80.0})
        rows_tr.append({"report_id": rid})
        rows_tr.append({"report_id": rid})  # duplicata
    df_bt = pd.DataFrame(rows_bt)
    df_tr = pd.DataFrame(rows_tr)

    out = calibrate_thresholds(df_bt, df_tr)
    cos_t = out["thresholds"]["cosine_es_es_bt"]
    assert cos_t["p5"] >= 0.85
    assert cos_t["p5"] >= cos_t["p5_observed"]  # max(p5, floor)


def test_calibrate_thresholds_metadata_counts_duplicates():
    """metadata.n_duplicates_in_bt = nº de IDs com duplicata em translations."""
    from src.evaluation.back_translation import calibrate_thresholds

    df_bt = pd.DataFrame([
        {"report_id": "DUP_A", "cosine_es_es_bt": 0.9,
         "bertscore_f1_es_es_bt": 0.9, "chrf_es_es_bt": 60.0},
        {"report_id": "SOLO", "cosine_es_es_bt": 0.99,
         "bertscore_f1_es_es_bt": 0.99, "chrf_es_es_bt": 90.0},
    ])
    df_tr = pd.DataFrame([
        {"report_id": "DUP_A"}, {"report_id": "DUP_A"},
        {"report_id": "SOLO"},
    ])
    out = calibrate_thresholds(df_bt, df_tr)
    assert out["metadata"]["n_duplicates_in_bt"] == 1  # só DUP_A
