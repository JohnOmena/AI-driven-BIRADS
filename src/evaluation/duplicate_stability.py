"""T19 — Estabilidade operacional via duplicatas (Phase A crash/restart).

Princípio metodológico: duplicatas foram geradas por crash/restart na Phase A,
não por experimento controlado. T19 mede estabilidade operacional sob produção
e calibra empiricamente os pisos de variação tolerada em T14.B/T18.

Filtragem em 4 camadas:
  - duplicate_candidate: report_id com >1 linha em translations.csv
  - valid_duplicate:     candidate AND ambas PT não-vazias
  - effective_duplicate: valid AND mesmo prompt_hash
  - strict_reproducibility_pair: effective AND mesma sessão

Métricas em 3 níveis:
  - Textual:    exact_match_normalized, chrf_pt_pt
  - Semântico:  cosine_pt_pt, bertscore_f1_pt_pt
  - Estrutural: category_match, measures_match, laterality_match, negation_match

Outputs:
  - duplicate_pairs.csv (classificação 4 camadas)
  - duplicate_stability.csv (métricas para effective)
  - duplicate_stability_summary.json (com h5_passed)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.evaluation.structural_checks import (
    extract_birads_category,
    extract_measures,
    extract_laterality,
    count_negations,
)


def _norm(s: str) -> str:
    s = str(s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# --- 4 camadas de classificação ---

def classify_pairs(df_translations: pd.DataFrame,
                    audit_jsonl_path: str | None = None) -> pd.DataFrame:
    """Classifica cada report_id repetido em 4 camadas determinísticas."""
    counts = df_translations["report_id"].value_counts()
    candidates = counts[counts > 1].index.tolist()

    # Carrega prompt_hash do audit JSONL se disponível
    prompt_hashes: dict = {}
    if audit_jsonl_path and Path(audit_jsonl_path).exists():
        with open(audit_jsonl_path, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    prompt_hashes[rec["report_id"]] = rec.get("prompt_hash")
                except (json.JSONDecodeError, KeyError):
                    continue

    rows = []
    for rid in candidates:
        pair = df_translations[df_translations["report_id"] == rid]
        # Determinar coluna de texto
        text_col = "report_text_translated" if "report_text_translated" in pair.columns else "report_text_raw"
        valid = (
            pair[text_col].notna().all()
            and (pair[text_col].astype(str) != "").all()
        )
        # prompt_hash: para Phase A não temos por laudo; assumimos effective se valid
        ph = prompt_hashes.get(rid, "phase_a_assumed")
        effective = valid and ph is not None
        strict = False  # heurística temporal não disponível

        rows.append({
            "report_id":    rid,
            "valid":        valid,
            "effective":    effective,
            "strict":       strict,
            "exclusion_reason": (
                None if effective
                else "empty_translation" if not valid
                else "different_prompt_hash" if ph is None
                else None
            ),
            "pair_type": (
                "strict_reproducibility_pair" if strict
                else "effective_duplicate" if effective
                else "valid_duplicate" if valid
                else "duplicate_candidate"
            ),
        })

    return pd.DataFrame(rows)


# --- Métricas em 3 níveis ---

def compute_pair_metrics(pt1: str, pt2: str, embedder=None, bert_scorer=None) -> dict:
    """Retorna 3 níveis: textual, semântico, estrutural."""
    import sacrebleu

    # Textual
    pt1_n = _norm(pt1)
    pt2_n = _norm(pt2)
    exact = (pt1_n == pt2_n)
    chrf = float(sacrebleu.corpus_chrf([str(pt2)], [[str(pt1)]],
                                          word_order=2, char_order=6).score)

    out = {
        "exact_match_normalized": exact,
        "chrf_pt_pt":             round(chrf, 3),
    }

    # Semântico
    if embedder is not None:
        from sentence_transformers import util
        e1 = embedder.encode([str(pt1)], convert_to_tensor=True, show_progress_bar=False)
        e2 = embedder.encode([str(pt2)], convert_to_tensor=True, show_progress_bar=False)
        cos = float(util.cos_sim(e1, e2)[0][0].item())
        out["cosine_pt_pt"] = round(cos, 4)

    if bert_scorer is not None:
        p, r, f1 = bert_scorer([str(pt2)], [str(pt1)])
        out["bertscore_f1_pt_pt"] = round(float(f1[0]), 4)

    # Estrutural (reusa T16)
    cat1, cat2 = extract_birads_category(pt1), extract_birads_category(pt2)
    meas1, meas2 = set(extract_measures(pt1)), set(extract_measures(pt2))
    lat1, lat2 = extract_laterality(pt1, "pt"), extract_laterality(pt2, "pt")
    neg1, neg2 = count_negations(pt1, "pt"), count_negations(pt2, "pt")

    out["category_match"]   = (cat1 == cat2)
    out["measures_match"]   = (meas1 == meas2)
    out["laterality_match"] = (lat1 == lat2)
    out["negation_match"]   = (neg1 == neg2)

    structural_instability = not all([
        out["category_match"], out["measures_match"],
        out["laterality_match"], out["negation_match"],
    ])
    out["duplicate_structural_instability"] = structural_instability
    out["requires_mqm_review"] = structural_instability

    return out


# --- Summary ---

def build_summary(df_pairs, df_metrics, out_path: str) -> dict:
    eff_ids = set(df_pairs[df_pairs["effective"]]["report_id"])
    eff = df_metrics[df_metrics["report_id"].isin(eff_ids)]
    n_eff = len(eff)

    excluded = df_pairs[~df_pairs["effective"]]["exclusion_reason"].value_counts().to_dict()

    cosine_col = eff.get("cosine_pt_pt", pd.Series([], dtype=float))
    bert_col = eff.get("bertscore_f1_pt_pt", pd.Series([], dtype=float))

    if n_eff >= 30:
        median_cos = float(cosine_col.median()) if not cosine_col.empty else None
        p5_cos = float(np.percentile(cosine_col.dropna(), 5)) if not cosine_col.empty else None
    else:
        median_cos = float(cosine_col.median()) if n_eff and not cosine_col.empty else None
        p5_cos = None

    structural_ids = eff[eff["duplicate_structural_instability"]]["report_id"].tolist()
    struct_rate = len(structural_ids) / n_eff if n_eff else 0

    h5_components = {
        "median_cosine_passed":  median_cos is not None and median_cos >= 0.98,
        "p5_cosine_passed":      p5_cos is not None and p5_cos >= 0.95,
        "structural_passed":     struct_rate <= 0.02,
    }
    h5_passed = all(h5_components.values())

    summary = {
        "duplicate_candidate_count":          int(len(df_pairs)),
        "valid_duplicate_count":              int(df_pairs["valid"].sum()),
        "effective_duplicate_count":          int(df_pairs["effective"].sum()),
        "strict_reproducibility_pair_count":  int(df_pairs["strict"].sum()),
        "excluded":                           excluded,

        "median_cosine_pt_pt":      round(median_cos, 4) if median_cos is not None else None,
        "p5_cosine_pt_pt":          round(p5_cos, 4) if p5_cos is not None else None,
        "median_bertscore_f1_pt_pt": round(float(bert_col.median()), 4) if not bert_col.empty else None,
        "median_chrf_pt_pt":        round(float(eff["chrf_pt_pt"].median()), 3) if n_eff else None,
        "exact_match_normalized_rate": round(float(eff["exact_match_normalized"].mean()), 4) if n_eff else None,

        "structural_instability_count": len(structural_ids),
        "structural_instability_rate":  round(struct_rate, 4),
        "structural_instability_ids":   structural_ids,

        "h5_components": h5_components,
        "h5_passed":     h5_passed,
    }

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                encoding="utf-8")
    return summary


# --- Main ---

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-jsonl", default="results/translation/audit_deepseek.jsonl")
    parser.add_argument("--out-pairs", default="results/translation/duplicate_pairs.csv")
    parser.add_argument("--out-metrics", default="results/translation/duplicate_stability.csv")
    parser.add_argument("--out-summary", default="results/translation/duplicate_stability_summary.json")
    parser.add_argument("--no-bertscore", action="store_true",
                        help="Pula BERTScore (mais rápido)")
    args = parser.parse_args()

    df_translations = pd.read_csv("results/translation/translations.csv")
    text_col = "report_text_translated" if "report_text_translated" in df_translations.columns else "report_text_raw"

    print("Classificando pares...")
    df_pairs = classify_pairs(df_translations, args.audit_jsonl)
    Path(args.out_pairs).parent.mkdir(parents=True, exist_ok=True)
    df_pairs.to_csv(args.out_pairs, index=False)

    print(f"  Candidates:   {len(df_pairs)}")
    print(f"  Valid:        {df_pairs['valid'].sum()}")
    print(f"  Effective:    {df_pairs['effective'].sum()}")
    print(f"  Excluded:     {dict(df_pairs[~df_pairs['effective']]['exclusion_reason'].value_counts())}")

    eff_ids = set(df_pairs[df_pairs["effective"]]["report_id"])
    if not eff_ids:
        print("Sem pares effective — abortando.")
        return 0

    # Carregar modelos
    print("\nCarregando modelos...")
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

    bert_scorer = None
    if not args.no_bertscore:
        from bert_score import BERTScorer
        bs = BERTScorer(model_type="xlm-roberta-large", lang="pt", rescale_with_baseline=False)
        def bert_scorer(cands, refs):
            return bs.score(cands, refs)

    print(f"\nComputando métricas para {len(eff_ids)} pares effective...")
    rows = []
    for i, rid in enumerate(sorted(eff_ids), 1):
        pair = df_translations[df_translations["report_id"] == rid].head(2)
        if len(pair) < 2:
            continue
        pt1 = pair.iloc[0][text_col]
        pt2 = pair.iloc[1][text_col]
        metrics = compute_pair_metrics(pt1, pt2, embedder, bert_scorer)
        rec = {"report_id": rid, "pair_type": "effective_duplicate", **metrics}
        rows.append(rec)

    df_metrics = pd.DataFrame(rows)
    df_metrics.to_csv(args.out_metrics, index=False)

    summary = build_summary(df_pairs, df_metrics, args.out_summary)

    print()
    print(f"T19 completo")
    print(f"  Cosine mediano:                {summary['median_cosine_pt_pt']}")
    print(f"  Cosine p5:                      {summary['p5_cosine_pt_pt']}")
    print(f"  exact_match_normalized_rate:    {summary['exact_match_normalized_rate']}")
    print(f"  structural_instability_count:   {summary['structural_instability_count']}")
    print(f"  H5 components: {summary['h5_components']}")
    print(f"  H5 passed: {summary['h5_passed']}")


if __name__ == "__main__":
    sys.exit(main())
