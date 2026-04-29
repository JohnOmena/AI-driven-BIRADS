"""T17 — Análise de consistência léxica BI-RADS (F5.B + F5.C).

Princípio metodológico: contagem GLOBAL por laudo, não alinhamento posicional.
Para cada termo ES do glossário Atlas, conta ocorrências no ES e em cada
variante PT (canonical + acceptable + unacceptable) com tolerância ±10%.

Categorização determinística:
  - canonical             → variante == pt_canonical
  - acceptable            → ∈ pt_variants_acceptable
  - gender_variant        → difere do canonical apenas em -o/-a
  - number_variant        → difere apenas em -s/-es
  - unacceptable          → ∈ pt_variants_unacceptable
  - unknown_for_term      → fora de qualquer lista

Métricas:
  - Por termo: term_canonical_ratio, term_acceptable_ratio
  - Globais:   overall_canonical_rate, overall_acceptable_rate (alvo H2 ≥ 0.99)

Outputs:
  - lexical_consistency.csv (1 linha por (laudo × termo))
  - lexical_anomalies.csv   (1 linha por anomalia)
  - lexical_global_summary.json (agregados — alimenta T23)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd


# --- Normalização ---

def _norm(s: str) -> str:
    s = str(s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# --- Categorização determinística ---

def _is_gender_variant(variant: str, canonical: str) -> bool:
    v = _norm(variant)
    c = _norm(canonical)
    if len(v) != len(c) or v == c:
        return False
    if v[:-1] == c[:-1] and {v[-1], c[-1]} == {"o", "a"}:
        return True
    return False


def _is_number_variant(variant: str, canonical: str) -> bool:
    v = _norm(variant)
    c = _norm(canonical)
    if v == c:
        return False
    # Plural simples: cat → cats
    if v == c + "s" or c == v + "s":
        return True
    # Plural -es: nodulo → nodulos / cor → cores
    if v == c + "es" or c == v + "es":
        return True
    # Transformação -em → -ens (margem → margens) e -ão → -ões
    if v.endswith("ens") and c.endswith("em") and v[:-3] == c[:-2]:
        return True
    if c.endswith("ens") and v.endswith("em") and c[:-3] == v[:-2]:
        return True
    if v.endswith("oes") and c.endswith("ao") and v[:-3] == c[:-2]:
        return True
    if c.endswith("oes") and v.endswith("ao") and c[:-3] == v[:-2]:
        return True
    return False


def categorize_pt_variant(variant: str, entry: dict) -> str:
    """Categoriza uma variante PT contra a entrada do glossário Atlas.

    Ordem: canonical → acceptable → unacceptable → gender_variant → number_variant → unknown.
    """
    v = _norm(variant)
    canonical = _norm(entry["pt_canonical"])
    acceptable = {_norm(x) for x in entry.get("pt_variants_acceptable", [])}
    unacceptable = {_norm(x) for x in entry.get("pt_variants_unacceptable", [])}

    if v == canonical:
        return "canonical"
    if v in acceptable:
        return "acceptable"
    if v in unacceptable:
        return "unacceptable"
    if _is_gender_variant(variant, entry["pt_canonical"]):
        return "gender_variant"
    if _is_number_variant(variant, entry["pt_canonical"]):
        return "number_variant"
    return "unknown_for_term"


# --- Contagem ---

def count_term_occurrences(text: str, term: str) -> int:
    """Conta ocorrências do termo (word boundary, case/accent insensitive)."""
    text_n = _norm(text)
    term_n = _norm(term)
    return len(re.findall(r"\b" + re.escape(term_n) + r"\b", text_n))


def analyze_laudo_lexical(es_text: str, pt_text: str, atlas: dict,
                            structural_pass: bool | None = None) -> list[dict]:
    """Para cada termo do Atlas presente no ES, conta variantes PT.

    Retorna lista de dicts (uma entry por termo BI-RADS encontrado no ES).
    structural_pass: se passado, computa flags de cross-reference com T16.
    """
    rows = []
    for cat_key, entries in atlas["categories"].items():
        for entry in entries:
            es_term = entry["es"]
            es_count = count_term_occurrences(es_text, es_term)
            if es_count == 0:
                continue

            # Coletar todas variantes a contar
            all_pt_variants = (
                {entry["pt_canonical"]}
                | set(entry.get("pt_variants_acceptable", []))
                | set(entry.get("pt_variants_unacceptable", []))
            )
            variant_counts = {v: count_term_occurrences(pt_text, v) for v in all_pt_variants}
            pt_total = sum(variant_counts.values())

            # Categorizar contagens
            categorized = {"canonical": 0, "acceptable": 0,
                            "gender_variant": 0, "number_variant": 0,
                            "unacceptable": 0, "unknown_for_term": 0}
            for v, n in variant_counts.items():
                if n == 0:
                    continue
                cat = categorize_pt_variant(v, entry)
                categorized[cat] += n

            # Flags ±10%
            ratio = pt_total / es_count if es_count > 0 else 0
            loss = ratio < 0.9
            hallucination = ratio > 1.1

            # Per-term ratios
            canonical_count = categorized["canonical"]
            acceptable_count = categorized["canonical"] + categorized["acceptable"]
            term_canonical_ratio = canonical_count / pt_total if pt_total > 0 else 0
            term_acceptable_ratio = acceptable_count / pt_total if pt_total > 0 else 0

            # Cross-flag com structural (T16)
            loss_with_struct_pass = (loss and structural_pass is True)
            loss_with_struct_fail = (loss and structural_pass is False)

            rows.append({
                "es_term":                 es_term,
                "es_count":                es_count,
                "pt_total_count":          pt_total,
                "ratio_pt_es":             round(ratio, 3),
                **categorized,
                "term_canonical_ratio":    round(term_canonical_ratio, 3),
                "term_acceptable_ratio":   round(term_acceptable_ratio, 3),
                "lexical_loss_flag":       loss,
                "lexical_hallucination_flag": hallucination,
                "lexical_loss_with_structural_pass": loss_with_struct_pass,
                "lexical_loss_with_structural_fail": loss_with_struct_fail,
                "bi_rads_code":            entry.get("bi_rads_code"),
            })
    return rows


# --- Anomalias ---

def detect_anomalies(es_text: str, pt_text: str, atlas: dict) -> list[dict]:
    """Detecta anomalias léxicas (variantes ≠ canonical e ≠ acceptable)."""
    out = []
    for cat_key, entries in atlas["categories"].items():
        for entry in entries:
            es_term = entry["es"]
            if count_term_occurrences(es_text, es_term) == 0:
                continue
            # Coletar todas variantes que aparecem no PT
            all_pt_variants = (
                {entry["pt_canonical"]}
                | set(entry.get("pt_variants_acceptable", []))
                | set(entry.get("pt_variants_unacceptable", []))
            )
            for v in all_pt_variants:
                n = count_term_occurrences(pt_text, v)
                if n == 0:
                    continue
                cat = categorize_pt_variant(v, entry)
                if cat in ("canonical", "acceptable"):
                    continue
                # Flag como anomalia
                severity = "critical" if entry.get("bi_rads_code", "").startswith(("CATEGORY_", "MASS_DENSITY_")) else "minor"
                out.append({
                    "es_term":             es_term,
                    "pt_variant_observed": v,
                    "pt_canonical":        entry["pt_canonical"],
                    "category":            cat,
                    "occurrences":         n,
                    "severity_inferred":   severity,
                    "bi_rads_code":        entry.get("bi_rads_code"),
                })
    return out


# --- Main ---

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out-consistency", default="results/translation/lexical_consistency.csv")
    parser.add_argument("--out-anomalies", default="results/translation/lexical_anomalies.csv")
    parser.add_argument("--out-summary", default="results/translation/lexical_global_summary.json")
    args = parser.parse_args()

    # Inputs
    df_pt = pd.read_csv("data/reports_translated_pt.csv").drop_duplicates("report_id", keep="last")
    df_es = pd.read_csv("data/reports_raw_canonical.csv")
    df = df_pt.merge(df_es[["report_id", "report_text_raw"]],
                     on="report_id", suffixes=("_pt", "_es"))
    df = df.rename(columns={"report_text_raw_pt": "pt_text",
                              "report_text_raw_es": "es_text"})

    # Cross-flag com T16: se structural_checks.csv existe, usar all_structural_pass
    struct_map: dict = {}
    struct_path = Path("results/translation/structural_checks.csv")
    if struct_path.exists():
        df_struct = pd.read_csv(struct_path)
        struct_map = dict(zip(df_struct["report_id"], df_struct["all_structural_pass"]))
        print(f"Cross-flag com T16: {len(struct_map)} laudos")

    if args.limit:
        df = df.head(args.limit)

    atlas = json.loads(Path("configs/birads_glossary_atlas_es_pt.json").read_text(encoding="utf-8"))
    print(f"T17: processando {len(df)} laudos × {sum(len(c) for c in atlas['categories'].values())} termos")

    consistency_rows: list[dict] = []
    anomaly_rows: list[dict] = []

    for i, row in enumerate(df.itertuples(index=False), 1):
        rid = row.report_id
        struct_pass = struct_map.get(rid)

        per_term = analyze_laudo_lexical(row.es_text, row.pt_text, atlas, struct_pass)
        for r in per_term:
            consistency_rows.append({"report_id": rid, **r})

        anomalies = detect_anomalies(row.es_text, row.pt_text, atlas)
        for a in anomalies:
            anomaly_rows.append({"report_id": rid, **a})

        if i % 500 == 0:
            print(f"  [{i}/{len(df)}]")

    # CSVs
    Path(args.out_consistency).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(consistency_rows).to_csv(args.out_consistency, index=False)
    pd.DataFrame(anomaly_rows).to_csv(args.out_anomalies, index=False)

    # Summary
    summary = build_summary(consistency_rows, anomaly_rows, args.out_summary)
    print(f"\nT17 completo")
    print(f"  Consistency: {args.out_consistency} ({len(consistency_rows)} rows)")
    print(f"  Anomalies:   {args.out_anomalies}   ({len(anomaly_rows)} rows)")
    print(f"  Summary:     {args.out_summary}")
    print()
    print(f"  overall_canonical_rate:   {summary['overall_canonical_rate']:.4f}")
    print(f"  overall_acceptable_rate:  {summary['overall_acceptable_rate']:.4f}  ← H2 metric (alvo ≥ 0.99)")


def build_summary(consistency_rows, anomaly_rows, out_path: str) -> dict:
    if not consistency_rows:
        return {"overall_canonical_rate": 0, "overall_acceptable_rate": 0}

    df = pd.DataFrame(consistency_rows)
    total_pt = int(df["pt_total_count"].sum())
    total_canonical = int(df["canonical"].sum())
    total_acceptable = int((df["canonical"] + df["acceptable"]).sum())
    n_terms = df["es_term"].nunique()

    summary = {
        "n_records":                int(df["report_id"].nunique()),
        "n_terms_analyzed":         int(n_terms),
        "total_es_occurrences":     int(df["es_count"].sum()),
        "total_pt_occurrences":     int(total_pt),
        "overall_canonical_rate":   round(total_canonical / total_pt, 4) if total_pt else 0,
        "overall_acceptable_rate":  round(total_acceptable / total_pt, 4) if total_pt else 0,
        "n_anomalies":              len(anomaly_rows),
        "n_laudos_with_loss_isolated":  int(df["lexical_loss_with_structural_pass"].sum()),
        "n_laudos_with_loss_critical":  int(df["lexical_loss_with_structural_fail"].sum()),
    }

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                encoding="utf-8")
    return summary


if __name__ == "__main__":
    sys.exit(main())
