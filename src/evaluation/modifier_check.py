"""T18 — Modifier preservation: divergências morfossintáticas INTRODUZIDAS pela tradução.

Pergunta: a forma flexionada do adjetivo BI-RADS foi preservada (não invertida)?
NÃO: a concordância está correta no PT — isso é T22/MQM.

Apenas adjetivos canônicos com `forms_pt` + `forms_es` no Atlas (~25 entradas).

Outputs:
  - modifier_preservation.csv  (1 linha por laudo)
  - modifier_threshold_empirical.json  (calibrado via T19 duplicatas, p5 com piso 0.90)
  - modifier_summary.json (agregados)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


MORPHOLOGY_TAGS = ["M-SING", "F-SING", "M-PLUR", "F-PLUR"]


def _norm(s: str) -> str:
    s = str(s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def detect_form(text: str, forms_dict: dict) -> str | None:
    """Detecta primeira forma morfológica encontrada. Plurais antes de singulares
    (evita match parcial: 'espiculadas' contém 'espiculada')."""
    text_n = _norm(text)
    for tag in ["M-PLUR", "F-PLUR", "M-SING", "F-SING"]:
        form = forms_dict.get(tag)
        if not form:
            continue
        if re.search(r"\b" + re.escape(_norm(form)) + r"\b", text_n):
            return tag
    return None


def diff_modifier_agreement(es_text: str, pt_text: str, atlas: dict) -> dict:
    """Compara forma do adjetivo em ES vs PT, retorna divergências introduzidas."""
    divergences = []
    n_compared = 0

    for cat_key, entries in atlas["categories"].items():
        for entry in entries:
            forms_pt = entry.get("forms_pt")
            forms_es = entry.get("forms_es")
            if not forms_pt or not forms_es:
                continue

            es_form = detect_form(es_text, forms_es)
            pt_form = detect_form(pt_text, forms_pt)

            if es_form is None or pt_form is None:
                continue

            n_compared += 1
            if es_form != pt_form:
                divergences.append({
                    "adjective_canonical": entry["pt_canonical"],
                    "bi_rads_code": entry.get("bi_rads_code"),
                    "es_form": es_form,
                    "pt_form": pt_form,
                    "divergence_type": (
                        "gender" if es_form[0] != pt_form[0]
                        else "number" if es_form[2:] != pt_form[2:]
                        else "both"
                    ),
                })

    return {
        "n_modifiers_compared": n_compared,
        "n_divergences":        len(divergences),
        "divergence_rate":      len(divergences) / n_compared if n_compared else 0.0,
        "preservation_rate":    (n_compared - len(divergences)) / n_compared if n_compared else None,
        "modifier_coverage_pass": (n_compared >= 1),
        "divergences":          divergences,
    }


# --- Calibração + Summary ---

def calibrate_threshold(df_mod: pd.DataFrame, df_translations: pd.DataFrame) -> dict:
    """Threshold empírico via p5 das duplicatas (T19), piso 0.90."""
    counts = df_translations["report_id"].value_counts()
    dup_ids = set(counts[counts > 1].index)

    dup_mod = df_mod[df_mod["report_id"].isin(dup_ids) & df_mod["modifier_coverage_pass"]]
    n_dups = len(dup_mod)

    if n_dups >= 30:
        p5 = float(np.percentile(dup_mod["preservation_rate"].dropna(), 5))
        threshold = max(p5, 0.90)
        method = "p5 of preservation_rate on duplicate pairs (n>=30)"
    else:
        p5 = None
        threshold = 0.95
        method = f"fallback 0.95 (only {n_dups} duplicates with coverage)"

    return {
        "preservation_rate_threshold": threshold,
        "method":                       method,
        "n_duplicates_with_coverage":   n_dups,
        "p5_observed":                  p5,
        "fallback_floor":               0.90,
    }


def build_summary(df: pd.DataFrame, threshold_data: dict, out_path: str) -> dict:
    covered = df[df["modifier_coverage_pass"]]
    n_total = len(df)
    n_cov = len(covered)
    total_compared = int(df["n_modifiers_compared"].sum())
    n_div = int(df["n_divergences"].sum())

    preservation_global = ((total_compared - n_div) / total_compared) if total_compared else None

    summary = {
        "total_laudos":                            n_total,
        "laudos_com_pelo_menos_1_modifier_comparado": n_cov,
        "coverage_rate":                            round(n_cov / n_total, 4) if n_total else 0,
        "n_modifiers_total_compared":               total_compared,
        "preservation_rate_global":                 round(preservation_global, 4) if preservation_global is not None else None,
        "n_divergences_total":                      n_div,
        "divergence_breakdown": {
            "gender": int(df.get("gender_divergence_count", pd.Series([0])).sum()),
            "number": int(df.get("number_divergence_count", pd.Series([0])).sum()),
            "both":   int(df.get("both_divergence_count", pd.Series([0])).sum()),
        },
        "preservation_rate_p5_duplicates":          threshold_data.get("p5_observed"),
        "threshold_empirical":                      threshold_data["preservation_rate_threshold"],
    }

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                encoding="utf-8")
    return summary


# --- Main ---

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out-csv", default="results/translation/modifier_preservation.csv")
    parser.add_argument("--out-thresholds", default="results/translation/modifier_threshold_empirical.json")
    parser.add_argument("--out-summary", default="results/translation/modifier_summary.json")
    args = parser.parse_args()

    df_pt = pd.read_csv("data/reports_translated_pt.csv").drop_duplicates("report_id", keep="last")
    df_es = pd.read_csv("data/reports_raw_canonical.csv")
    df = df_pt.merge(df_es[["report_id", "report_text_raw"]],
                     on="report_id", suffixes=("_pt", "_es"))
    df = df.rename(columns={"report_text_raw_pt": "pt_text",
                              "report_text_raw_es": "es_text"})

    if args.limit:
        df = df.head(args.limit)

    atlas = json.loads(Path("configs/birads_glossary_atlas_es_pt.json").read_text(encoding="utf-8"))
    print(f"T18: processando {len(df)} laudos")

    rows = []
    for i, row in enumerate(df.itertuples(index=False), 1):
        result = diff_modifier_agreement(row.es_text, row.pt_text, atlas)
        rec = {
            "report_id":                row.report_id,
            "n_modifiers_compared":     result["n_modifiers_compared"],
            "n_divergences":            result["n_divergences"],
            "divergence_rate":          result["divergence_rate"],
            "preservation_rate":        result["preservation_rate"],
            "modifier_coverage_pass":   result["modifier_coverage_pass"],
            "gender_divergence_count":  sum(1 for d in result["divergences"] if d["divergence_type"] == "gender"),
            "number_divergence_count":  sum(1 for d in result["divergences"] if d["divergence_type"] == "number"),
            "both_divergence_count":    sum(1 for d in result["divergences"] if d["divergence_type"] == "both"),
            "divergences_json":         json.dumps(result["divergences"], ensure_ascii=False),
        }
        rows.append(rec)
        if i % 1000 == 0:
            print(f"  [{i}/{len(df)}]")

    df_out = pd.DataFrame(rows)
    Path(args.out_csv).parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(args.out_csv, index=False)

    # Calibração via duplicatas
    df_translations = pd.read_csv("results/translation/translations.csv")
    threshold_data = calibrate_threshold(df_out, df_translations)
    Path(args.out_thresholds).write_text(
        json.dumps(threshold_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Summary
    summary = build_summary(df_out, threshold_data, args.out_summary)

    print()
    print(f"T18 completo")
    print(f"  CSV:        {args.out_csv}")
    print(f"  Thresholds: {args.out_thresholds}")
    print(f"  Summary:    {args.out_summary}")
    print()
    print(f"  Coverage rate:                {summary['coverage_rate']*100:.2f}%")
    print(f"  preservation_rate_global:     {summary['preservation_rate_global']:.4f}" if summary['preservation_rate_global'] else "  preservation_rate_global: N/A")
    print(f"  n_divergences_total:          {summary['n_divergences_total']}")
    print(f"  threshold_empirical:          {summary['threshold_empirical']:.4f}")


if __name__ == "__main__":
    sys.exit(main())
