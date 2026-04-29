"""T13 Step 5 — Calibração inter-auditor DeepSeek V3 ↔ GPT-4o-mini.

Pré-registrado em decision_log.md (tag t13-step5-criteria-pre-registered):
  κ ≥ 0,80 → PRIMARY_STABLE  | κ 0,60-0,79 → MODERATE
  κ 0,40-0,59 → INVESTIGATE  | κ < 0,40    → DOWNGRADE

Estratificação amostra (n=250):
  - 6 críticos (100% — Tier 1)
  - 13 major (100%)
  - 50 minor (C1=20, C5=20, C7=10)
  - 181 random estratificado por birads_label

Output:
  - results/translation/calibration_audit_gpt4o.jsonl (per-laudo audit GPT)
  - results/translation/calibration_kappa.json (κ + decisão)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.evaluation.severity import apply_severity_override
from src.translation.client import create_client
from src.translation.glossary import load_glossary, format_glossary_for_prompt
from src.translation.translate import audit_report

OUT_JSONL_DEFAULT = "results/translation/calibration_audit_gpt4o.jsonl"
OUT_KAPPA_DEFAULT = "results/translation/calibration_kappa.json"

AUDITOR_PRESETS = {
    "gpt-4o-mini": {
        "model_key": "gpt-4o-mini",
        "out_jsonl": "results/translation/calibration_audit_gpt4o.jsonl",
        "out_kappa": "results/translation/calibration_kappa.json",
        "auditor_name": "gpt-4o-mini-2024-07-18",
    },
    "claude-haiku": {
        "model_key": "claude-haiku",
        "out_jsonl": "results/translation/calibration_audit_haiku.jsonl",
        "out_kappa": "results/translation/calibration_kappa_haiku.json",
        "auditor_name": "claude-haiku-4-5-20251001",
    },
}


CRITERIA = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]


def _criterion_short(c: str) -> str:
    if not c:
        return ""
    return c.strip().split("_")[0].upper()


def build_stratified_sample(records: list[dict], df_pt: pd.DataFrame,
                              target_n: int = 250, seed: int = 42) -> list[str]:
    """Composição: 6 critical + 13 major + 50 minor (estratificado por C1/C5/C7)
    + 181 random estratificado por birads_label.
    """
    rng = np.random.default_rng(seed)
    by_id = {r["report_id"]: r for r in records}

    crit_ids  = [r["report_id"] for r in records if r.get("has_critical_error")]
    major_ids = [
        r["report_id"] for r in records
        if r.get("major_error_count", 0) > 0 and not r.get("has_critical_error")
    ]

    selected: set[str] = set(crit_ids) | set(major_ids)

    # Minor estratificado por critério (C1=20, C5=20, C7=10)
    minor_by_crit: dict[str, list[str]] = {"C1": [], "C5": [], "C7": []}
    for r in records:
        if r["report_id"] in selected:
            continue
        if r.get("minor_error_count", 0) == 0:
            continue
        # Pegar critérios com ok=False
        crits = r.get("audit_raw", {}).get("criteria", {})
        for k, v in crits.items():
            if isinstance(v, dict) and v.get("ok") is False:
                cn = _criterion_short(k)
                if cn in minor_by_crit:
                    minor_by_crit[cn].append(r["report_id"])
                    break  # 1 entrada por laudo

    quotas = {"C1": 20, "C5": 20, "C7": 10}
    for c, q in quotas.items():
        pool = list(set(minor_by_crit[c]) - selected)
        if len(pool) > 0:
            take = min(q, len(pool))
            idx = rng.choice(len(pool), take, replace=False)
            selected.update(pool[i] for i in idx)

    # Random fill estratificado por birads_label
    df_idx = df_pt.set_index("report_id")
    remaining = [rid for rid in df_idx.index if rid not in selected]
    rem_df = df_idx.loc[remaining]
    fill_n = target_n - len(selected)
    if fill_n > 0 and len(rem_df) > 0:
        # Distribuição proporcional por categoria
        dist = df_pt["birads_label"].value_counts(normalize=True)
        for cat, frac in dist.items():
            cat_pool = rem_df[rem_df["birads_label"] == cat].index.tolist()
            cat_n = max(1, int(round(fill_n * frac)))
            cat_n = min(cat_n, len(cat_pool))
            if cat_n > 0:
                idx = rng.choice(len(cat_pool), cat_n, replace=False)
                selected.update(cat_pool[i] for i in idx)
        # Top-up se faltou (arredondamento)
        if len(selected) < target_n:
            still_remaining = [r for r in remaining if r not in selected]
            extra = target_n - len(selected)
            if len(still_remaining) > 0:
                idx = rng.choice(len(still_remaining), min(extra, len(still_remaining)), replace=False)
                selected.update(still_remaining[i] for i in idx)

    return sorted(selected)[:target_n]


def cohen_kappa(y1: list[bool], y2: list[bool]) -> float:
    """κ Cohen para 2 raters binários."""
    n = len(y1)
    if n == 0:
        return float("nan")
    a = sum(1 for i in range(n) if y1[i] == y2[i])
    po = a / n
    p1 = sum(y1) / n
    p2 = sum(y2) / n
    pe = p1*p2 + (1-p1)*(1-p2)
    if pe == 1:
        return 1.0 if po == 1 else 0.0
    return (po - pe) / (1 - pe)


def kappa_with_bca_ci(y1: list[bool], y2: list[bool],
                       n_resamples: int = 10000, seed: int = 42) -> dict:
    """κ + IC 95% via bootstrap BCa."""
    from scipy.stats import bootstrap
    arr = np.array(list(zip(y1, y2)), dtype=bool)
    if len(arr) < 5:
        return {"kappa": float("nan"), "ci_low": None, "ci_high": None, "n": len(arr)}

    def stat(idx_arr):
        sample = arr[idx_arr]
        return cohen_kappa(sample[:, 0].tolist(), sample[:, 1].tolist())

    rng = np.random.default_rng(seed)
    samples = []
    n = len(arr)
    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        samples.append(stat(idx))
    samples = np.array(samples)
    samples = samples[~np.isnan(samples)]

    point = cohen_kappa(y1, y2)
    if len(samples) < 100:
        return {"kappa": float(point), "ci_low": None, "ci_high": None, "n": n}
    return {
        "kappa":   round(float(point), 4),
        "ci_low":  round(float(np.percentile(samples, 2.5)), 4),
        "ci_high": round(float(np.percentile(samples, 97.5)), 4),
        "n": n,
    }


def derive_decision(kappa_global: float) -> str:
    if kappa_global >= 0.80:
        return "PRIMARY_STABLE"
    if kappa_global >= 0.60:
        return "MODERATE"
    if kappa_global >= 0.40:
        return "INVESTIGATE"
    return "DOWNGRADE"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Smoke test (N laudos)")
    parser.add_argument("--target-n", type=int, default=250)
    parser.add_argument("--auditor", default="gpt-4o-mini",
                        choices=list(AUDITOR_PRESETS.keys()),
                        help="Calibrator model: gpt-4o-mini (Step 5) | claude-haiku (Step 5b)")
    args = parser.parse_args()
    preset = AUDITOR_PRESETS[args.auditor]

    # Inputs: T13 records + base PT + glossário
    print("Carregando T13 audit records...")
    records = []
    with open("results/translation/audit_deepseek.jsonl", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    print(f"  {len(records)} laudos auditados (DeepSeek)")

    df_pt = pd.read_csv("data/reports_translated_pt.csv").drop_duplicates("report_id", keep="last")
    df_es = pd.read_csv("data/reports_raw_canonical.csv")

    # Build sample
    sample_ids = build_stratified_sample(records, df_pt, target_n=args.target_n)
    if args.limit:
        sample_ids = sample_ids[:args.limit]
    print(f"  amostra: {len(sample_ids)}")

    # Calibrator client (Step 5: gpt-4o-mini | Step 5b: claude-haiku)
    cfg = yaml.safe_load(Path("configs/models.yaml").read_text(encoding="utf-8"))
    if preset["model_key"] not in cfg["models"]:
        print(f"ERRO: {preset['model_key']} não em models.yaml")
        return 1
    auditor = create_client(preset["model_key"], cfg["models"][preset["model_key"]])
    print(f"  calibrator: {preset['auditor_name']}")

    # Glossário
    glossary_pairs = load_glossary("configs/birads_glossary_es_pt.json")
    glossary_text = format_glossary_for_prompt(glossary_pairs)

    # Resume
    out_path = Path(preset["out_jsonl"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    done.add(json.loads(line)["report_id"])
    pending = [r for r in sample_ids if r not in done]
    print(f"  resume: {len(done)} já feitos, {len(pending)} pendentes")

    df_es_idx = df_es.set_index("report_id")
    df_pt_idx = df_pt.set_index("report_id")

    print(f"\nAuditando {len(pending)} laudos com GPT-4o-mini...")
    t0 = time.time()
    for i, rid in enumerate(pending, 1):
        try:
            es_text = df_es_idx.loc[rid]["report_text_raw"]
            pt_text = df_pt_idx.loc[rid]["report_text_raw"]
        except KeyError:
            continue

        try:
            audit = audit_report(es_text, pt_text, auditor, glossary_text, temperature=0)
        except Exception as e:
            print(f"  [{i}/{len(pending)}] {rid} EXC: {type(e).__name__}: {str(e)[:80]}")
            continue

        if audit is None:
            print(f"  [{i}/{len(pending)}] {rid} ABORTED (None)")
            continue

        raw_incs = audit.get("inconsistencias", [])
        # Severity override (mesma lógica T13)
        graded = apply_severity_override(raw_incs)

        rec = {
            "report_id":   rid,
            "auditor":     preset["auditor_name"],
            "audited_at":  pd.Timestamp.utcnow().isoformat(),
            "audit_raw": {
                "approved":  audit.get("aprovado"),
                "score":     audit.get("score"),
                "criteria":  audit.get("criterios", {}),
                "inconsistencies": graded,
            },
        }

        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        if i % 10 == 0:
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(pending) - i) / rate / 60 if rate > 0 else 0
            print(f"  [{i}/{len(pending)}] cost=${auditor.total_cost_usd:.4f} rate={rate:.2f}/s eta={eta:.1f}min")

    elapsed = time.time() - t0
    print(f"\n{preset['auditor_name']} concluído em {elapsed/60:.1f} min, ${auditor.total_cost_usd:.4f}")

    # =========================================================================
    # Compute κ Cohen pareada
    # =========================================================================
    print(f"\nComputando κ Cohen DeepSeek↔{preset['auditor_name']}...")

    by_id_ds = {r["report_id"]: r for r in records}
    gpt_records: dict[str, dict] = {}
    with open(out_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                gpt_records[r["report_id"]] = r

    common = [rid for rid in sample_ids if rid in gpt_records and rid in by_id_ds]

    # Per-criterion: ok=False (problema flagado)
    results = {}
    for c in CRITERIA:
        ds_y, gpt_y = [], []
        for rid in common:
            ds_crits  = by_id_ds[rid].get("audit_raw", {}).get("criteria", {})
            gpt_crits = gpt_records[rid].get("audit_raw", {}).get("criteria", {})
            ds_ok  = next((v.get("ok") for k, v in ds_crits.items()  if _criterion_short(k) == c), True)
            gpt_ok = next((v.get("ok") for k, v in gpt_crits.items() if _criterion_short(k) == c), True)
            ds_y.append(ds_ok is False)
            gpt_y.append(gpt_ok is False)
        results[c] = kappa_with_bca_ci(ds_y, gpt_y)

    # Severity per laudo: has_critical_error
    ds_crit  = [bool(by_id_ds[rid].get("has_critical_error"))    for rid in common]
    gpt_crit = []
    for rid in common:
        graded = gpt_records[rid].get("audit_raw", {}).get("inconsistencies", [])
        gpt_crit.append(any(g.get("severity") == "critical" for g in graded))
    results["has_critical_error"] = kappa_with_bca_ci(ds_crit, gpt_crit)

    # κ médio (média não-ponderada das 7 categorias C1-C7)
    valid_kappas = [results[c]["kappa"] for c in CRITERIA if not np.isnan(results[c]["kappa"])]
    kappa_global_unweighted = float(np.mean(valid_kappas)) if valid_kappas else float("nan")

    # Decisão
    decision = derive_decision(kappa_global_unweighted)

    out = {
        "metadata": {
            "n_sample":   len(common),
            "auditor_primary":   "deepseek-v3",
            "auditor_calibrator":preset["auditor_name"],
            "computed_at": pd.Timestamp.utcnow().isoformat(),
            "cost_usd": round(auditor.total_cost_usd, 4),
            "elapsed_min":  round(elapsed/60, 2),
        },
        "kappa_per_criterion": {c: results[c] for c in CRITERIA},
        "kappa_has_critical_error": results["has_critical_error"],
        "kappa_global_unweighted": round(kappa_global_unweighted, 4),
        "decision": decision,
        "criteria_definitions": {
            "C1": "descritores BI-RADS",
            "C2": "categoria BI-RADS",
            "C3": "medidas/números",
            "C4": "lateralidade/localização",
            "C5": "omissões/adições",
            "C6": "inversões/negação",
            "C7": "temporais/achados",
        },
    }
    Path(preset["out_kappa"]).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{'='*60}")
    print(f"κ_global_unweighted: {kappa_global_unweighted:.4f}")
    print(f"DECISÃO: {decision}")
    print(f"\nκ por critério:")
    for c in CRITERIA:
        r = results[c]
        ci = f"[{r['ci_low']}, {r['ci_high']}]" if r['ci_low'] is not None else "(IC NA)"
        print(f"  {c}: {r['kappa']:.4f} {ci}")
    print(f"  has_critical_error: {results['has_critical_error']['kappa']:.4f}")
    print(f"\nOutput: {preset['out_kappa']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
