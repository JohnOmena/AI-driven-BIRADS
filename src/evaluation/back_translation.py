"""T14.B — Back-translation PT→ES via Gemini 2.5 Flash thinking OFF (amostral ~250).

⚠ DEPENDE de T14.A merged em main (LLMClient com thinking_budget). Smoke
e full run aguardam autorização explícita do usuário.

Princípios:
  - Amostra estratificada (~250) cobrindo T22 humanos + T19 duplicatas + Phase A
    review/rejected + estratos por categoria BI-RADS
  - Prompt minimalista (sem glossário) — mitiga family bias Gemini↔Gemini
  - thinking_budget=0 — força tradução determinística
  - Métricas em (ES_orig, ES_bt): cosine, BERTScore-F1, chrF, BLEU
  - Calibração empírica de thresholds via duplicatas (Step 2.6)
  - Resume idempotente

Outputs:
  - bt_sample_ids.json (composição da amostra)
  - back_translation.csv (resultados)
  - bt_thresholds_empirical.json (thresholds calibrados)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


# Prompt minimalista (decisão T14.B)
PROMPT = """Traduza o seguinte laudo do português ao espanhol fielmente, preservando terminologia médica BI-RADS.

LAUDO PT:
{pt_text}

TRADUÇÃO ES:"""


def build_stratified_sample(target_n: int = 250, seed: int = 42) -> dict:
    """Composição:
      - 100% IDs T22 (review + rejected da Phase A)
      - 100% IDs T19 (duplicatas effective)
      - estratos por categoria BI-RADS (≥7 por categoria onde possível)
      - random fill até target_n
    """
    rng = np.random.default_rng(seed)

    df_pt = pd.read_csv("data/reports_translated_pt.csv").drop_duplicates("report_id", keep="last")
    df_translations = pd.read_csv("results/translation/translations.csv")

    must_include: set[str] = set()

    # T22: review + rejected
    if "status" in df_translations.columns:
        rr = df_translations[df_translations["status"].isin(["review", "rejected"])]
        must_include.update(rr["report_id"].dropna().astype(str))

    # T19: duplicatas effective
    dup_path = Path("results/translation/duplicate_pairs.csv")
    if dup_path.exists():
        df_dup = pd.read_csv(dup_path)
        eff_ids = df_dup[df_dup["effective"]]["report_id"].astype(str).tolist()
        must_include.update(eff_ids)

    # Estratos por categoria BI-RADS
    categories = sorted(df_pt["birads_label"].dropna().unique())
    target_per_cat = 7

    selected = set(must_include)
    for cat in categories:
        pool = df_pt[df_pt["birads_label"] == cat]
        already_in = pool[pool["report_id"].isin(selected)]
        needed = max(0, target_per_cat - len(already_in))
        if needed > 0:
            available = pool[~pool["report_id"].isin(selected)]["report_id"].tolist()
            if len(available) > 0:
                take = min(needed, len(available))
                idx = rng.choice(len(available), take, replace=False)
                selected.update([available[i] for i in idx])

    # Random fill até target_n
    if len(selected) < target_n:
        remaining = df_pt[~df_pt["report_id"].isin(selected)]["report_id"].tolist()
        fill = target_n - len(selected)
        if len(remaining) > 0:
            take = min(fill, len(remaining))
            idx = rng.choice(len(remaining), take, replace=False)
            selected.update([remaining[i] for i in idx])

    sample_ids = sorted(selected)[:target_n]

    # Stats por categoria
    df_idx = df_pt.set_index("report_id")
    cat_dist = {}
    for rid in sample_ids:
        if rid in df_idx.index:
            cat = df_idx.loc[rid]["birads_label"]
            if pd.notna(cat):
                cat_dist[int(cat)] = cat_dist.get(int(cat), 0) + 1

    out = {
        "metadata": {
            "seed": seed,
            "target_n": target_n,
            "actual_n": len(sample_ids),
            "must_include_count": len(must_include),
            "categories_distribution": cat_dist,
        },
        "report_ids": sample_ids,
    }

    sample_path = Path("results/translation/bt_sample_ids.json")
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    sample_path.write_text(json.dumps(out, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    return out


def calibrate_thresholds(df_bt: pd.DataFrame, df_translations: pd.DataFrame) -> dict:
    """p5 das duplicatas, piso 0.85 (cosine/bertscore) ou 50 (chrf)."""
    counts = df_translations["report_id"].value_counts()
    dup_ids = set(counts[counts > 1].index)
    dup_bt = df_bt[df_bt["report_id"].isin(dup_ids)]

    out = {"metadata": {
        "method": "p5 of BT metrics on duplicate pairs",
        "n_duplicates_in_bt": len(dup_bt),
    }, "thresholds": {}}

    for col, floor in [("cosine_es_es_bt", 0.85),
                        ("bertscore_f1_es_es_bt", 0.85),
                        ("chrf_es_es_bt", 50.0)]:
        if col in dup_bt.columns and len(dup_bt) >= 30:
            p5 = float(np.percentile(dup_bt[col].dropna(), 5))
            out["thresholds"][col] = {"p5": max(p5, floor), "p5_observed": p5}
        else:
            out["thresholds"][col] = {"p5": floor, "fallback_floor": floor}

    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Smoke test")
    parser.add_argument("--target-n", type=int, default=250)
    parser.add_argument("--out-csv", default="results/translation/back_translation.csv")
    parser.add_argument("--out-thresholds",
                        default="results/translation/bt_thresholds_empirical.json")
    args = parser.parse_args()

    # Build/load sample
    sample_path = Path("results/translation/bt_sample_ids.json")
    if sample_path.exists():
        sample = json.loads(sample_path.read_text(encoding="utf-8"))
    else:
        sample = build_stratified_sample(args.target_n)

    sample_ids = sample["report_ids"]
    if args.limit:
        sample_ids = sample_ids[:args.limit]

    # Resume — skip já feitos
    out_path = Path(args.out_csv)
    if out_path.exists():
        done = set(pd.read_csv(out_path)["report_id"])
        sample_ids = [r for r in sample_ids if r not in done]

    if not sample_ids:
        print("Nada a processar.")
        return 0

    # Carregar dados
    df_pt = pd.read_csv("data/reports_translated_pt.csv").drop_duplicates("report_id", keep="last").set_index("report_id")
    df_es = pd.read_csv("data/reports_raw_canonical.csv").set_index("report_id")

    # Cliente Gemini 2.5 Flash thinking OFF — usa T14.A
    from src.translation.client import create_client
    cfg = yaml.safe_load(Path("configs/models.yaml").read_text(encoding="utf-8"))

    if "gemini-2.5-flash-no-thinking" not in cfg["models"]:
        print("ERRO: gemini-2.5-flash-no-thinking não configurado em models.yaml")
        return 1

    client = create_client("gemini-2.5-flash-no-thinking",
                           cfg["models"]["gemini-2.5-flash-no-thinking"])

    # Modelos para métricas
    print("Carregando modelos...")
    from sentence_transformers import SentenceTransformer, util
    from bert_score import BERTScorer
    import sacrebleu

    embedder = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
    bs = BERTScorer(model_type="xlm-roberta-large", lang="es", rescale_with_baseline=False)

    print(f"T14.B: processando {len(sample_ids)} laudos")
    t_start = time.time()
    rows = []

    for i, rid in enumerate(sample_ids, 1):
        try:
            pt_text = df_pt.loc[rid]["report_text_raw"]
            es_orig = df_es.loc[rid]["report_text_raw"]
        except KeyError:
            continue

        try:
            es_bt = client.generate(PROMPT.format(pt_text=pt_text), temperature=0)
        except Exception as e:
            print(f"  [{i}/{len(sample_ids)}] {rid} EXC: {type(e).__name__}: {str(e)[:80]}")
            continue

        # Métricas (ES_orig, ES_bt)
        emb_o = embedder.encode([str(es_orig)], convert_to_tensor=True, show_progress_bar=False)
        emb_b = embedder.encode([str(es_bt)], convert_to_tensor=True, show_progress_bar=False)
        cos = float(util.cos_sim(emb_o, emb_b)[0][0].item())

        chrf = float(sacrebleu.corpus_chrf([str(es_bt)], [[str(es_orig)]],
                                              word_order=2, char_order=6).score)
        bleu = float(sacrebleu.corpus_bleu([str(es_bt)], [[str(es_orig)]]).score)

        p, r, f1 = bs.score([str(es_bt)], [str(es_orig)])
        bf1 = float(f1[0])

        # Estrutural cross-check (reusa T16)
        from src.evaluation.structural_checks import (
            extract_birads_category, extract_measures, extract_laterality
        )
        cat_orig = extract_birads_category(es_orig)
        cat_bt = extract_birads_category(es_bt)
        meas_orig = set(extract_measures(es_orig))
        meas_bt = set(extract_measures(es_bt))
        lat_orig = extract_laterality(es_orig, "es")
        lat_bt = extract_laterality(es_bt, "es")

        rec = {
            "report_id":              rid,
            "es_back_translated":     es_bt,
            "cosine_es_es_bt":        round(cos, 4),
            "bertscore_f1_es_es_bt":  round(bf1, 4),
            "chrf_es_es_bt":          round(chrf, 3),
            "bleu_es_es_bt":          round(bleu, 3),
            "category_match":         (cat_orig == cat_bt),
            "measures_match":         (meas_orig == meas_bt),
            "laterality_match":       (lat_orig == lat_bt),
        }
        rows.append(rec)

        if i % 10 == 0:
            elapsed = time.time() - t_start
            print(f"  [{i}/{len(sample_ids)}] cost=${client.total_cost_usd:.4f} rate={i/elapsed:.2f}/s")

        # Flush a cada 25
        if i % 25 == 0:
            mode = "a" if out_path.exists() else "w"
            header = not out_path.exists()
            pd.DataFrame(rows).to_csv(out_path, mode=mode, header=header, index=False)
            rows = []

    # Final flush
    if rows:
        mode = "a" if out_path.exists() else "w"
        header = not out_path.exists()
        pd.DataFrame(rows).to_csv(out_path, mode=mode, header=header, index=False)

    # Calibrar thresholds
    print("\nCalibrando thresholds via duplicatas...")
    df_bt = pd.read_csv(out_path)
    df_translations = pd.read_csv("results/translation/translations.csv")
    threshold_data = calibrate_thresholds(df_bt, df_translations)
    Path(args.out_thresholds).write_text(
        json.dumps(threshold_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    elapsed = time.time() - t_start
    print(f"\nT14.B completo em {elapsed/60:.1f} min")
    print(f"  CSV:        {out_path}")
    print(f"  Thresholds: {args.out_thresholds}")
    print(f"  Custo:      ${client.total_cost_usd:.6f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
