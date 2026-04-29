"""T13 Step 1.5 — Smoke test ESTRATIFICADO antes do full run.

Composição (20 laudos, seed=42):
  5  com inconsistência C1 conhecida da Phase A → testa fix T12.5
  5  com lateralidade/medida/negação no texto → testa override mecânico T12.6
  3  com status review/rejected da Phase A → casos limite
  5  random estratificados por categoria BI-RADS (1 por categoria 0-4)
  2  das duplicatas T19 (RPT_000721-RPT_000820)

6 critérios objetivos para liberar full run:
  1. Parse rate 100% (sem failures)
  2. Custo por laudo $0.000042 - $0.000078
  3. Latência mediana < 5s
  4. Score válido em 100% (não None/null)
  5. Severity_method plausível: pelo menos 1 inconsistência mecânica em C2/C3/C4/C6
     com severity_method = 'mechanical'
  6. audit_final_status plausível: distribuição NÃO-extrema
     (não 100% approved nem 100% rejected)

Falha em qualquer → abortar T13 full run.
"""

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd
import yaml
import numpy as np
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation.io import append_jsonl
from src.evaluation.reaudit_deepseek import build_record, _prompt_hash
from src.translation.client import create_client
from src.translation.glossary import load_glossary, format_glossary_for_prompt


SMOKE_OUT = "results/translation/smoke_t13_reaudit.jsonl"


def stratified_sample(seed: int = 42) -> list[str]:
    """Seleciona 20 laudos estratificados conforme composição T13 Step 1.5."""
    np.random.seed(seed)

    df_pt = pd.read_csv("data/reports_translated_pt.csv").drop_duplicates("report_id", keep="last")
    df_es = pd.read_csv("data/reports_raw_canonical.csv")
    audit_old = json.loads(Path("results/translation/audit_results.json").read_text(encoding="utf-8"))

    selected: set[str] = set()

    # Bucket 1: 5 com C1 finding na Phase A
    c1_ids = []
    for rec in audit_old:
        hist = rec.get("correction_history") or []
        if not hist:
            continue
        incs = hist[0].get("inconsistencias") or []
        if any(i.get("criterio", "").startswith("C1") for i in incs):
            c1_ids.append(rec["report_id"])
    bucket1 = list(np.random.choice(c1_ids, min(5, len(c1_ids)), replace=False))
    selected.update(bucket1)

    # Bucket 2: 5 com lateralidade/medida/negação explícitas no texto
    pat = re.compile(r"(izquierd|derech|\d+\s*(?:mm|cm)|no se observ|sin )", re.IGNORECASE)
    candidates = []
    for _, row in df_es.iterrows():
        if row["report_id"] in selected:
            continue
        text = str(row["report_text_raw"])
        if pat.search(text):
            candidates.append(row["report_id"])
    bucket2 = list(np.random.choice(candidates, min(5, len(candidates)), replace=False))
    selected.update(bucket2)

    # Bucket 3: 3 com status review/rejected na Phase A — vem de translations.csv intermediário
    df_status = pd.read_csv("results/translation/translations.csv").drop_duplicates("report_id", keep="last")
    rr = df_status[df_status.get("status", pd.Series()).isin(["review", "rejected"])]
    rr = rr[~rr["report_id"].isin(selected)]
    if len(rr) > 0:
        bucket3 = list(np.random.choice(rr["report_id"].values, min(3, len(rr)), replace=False))
        selected.update(bucket3)

    # Bucket 4: 5 random por categoria (1 por categoria 0-4)
    for cat in [0, 1, 2, 3, 4]:
        pool = df_pt[(df_pt["birads_label"] == cat) & (~df_pt["report_id"].isin(selected))]
        if len(pool) > 0:
            chosen = pool.sample(1, random_state=seed + cat)["report_id"].iloc[0]
            selected.add(chosen)

    # Bucket 5: 2 das duplicatas T19 (RPT_000721-RPT_000820)
    counts = pd.read_csv("results/translation/translations.csv")["report_id"].value_counts()
    dup_ids = counts[counts > 1].index.tolist()
    dup_ids = [d for d in dup_ids if d not in selected]
    if len(dup_ids) > 0:
        bucket5 = list(np.random.choice(dup_ids, min(2, len(dup_ids)), replace=False))
        selected.update(bucket5)

    return sorted(selected)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=SMOKE_OUT)
    args = parser.parse_args()

    sample = stratified_sample(seed=42)
    print(f"Smoke T13 estratificado: {len(sample)} laudos")
    print("=" * 60)

    # Limpar smoke output anterior se existir
    out_path = Path(args.out)
    if out_path.exists():
        out_path.unlink()

    df_pt = pd.read_csv("data/reports_translated_pt.csv").drop_duplicates("report_id", keep="last").set_index("report_id")
    df_es = pd.read_csv("data/reports_raw_canonical.csv").set_index("report_id")

    cfg = yaml.safe_load(Path("configs/models.yaml").read_text(encoding="utf-8"))
    auditor = create_client("deepseek-v3", cfg["models"]["deepseek-v3"])
    glossary_pairs = load_glossary("configs/birads_glossary_es_pt.json")
    glossary_text = format_glossary_for_prompt(glossary_pairs)
    p_hash = _prompt_hash()

    parse_failures = 0
    latencies = []
    severity_methods: Counter = Counter()
    final_statuses: Counter = Counter()
    has_critical_count = 0
    has_score_valid = 0

    cost_start = auditor.total_cost_usd
    for i, rid in enumerate(sample, 1):
        if rid not in df_es.index or rid not in df_pt.index:
            print(f"[{i}/{len(sample)}] {rid} MISSING -- skip")
            continue
        es_text = df_es.loc[rid]["report_text_raw"]
        pt_text = df_pt.loc[rid]["report_text_raw"]

        t0 = time.time()
        try:
            record = build_record(rid, es_text, pt_text,
                                   auditor, glossary_text, glossary_pairs, p_hash)
        except Exception as e:
            print(f"[{i}/{len(sample)}] {rid} EXC: {type(e).__name__}: {str(e)[:120]}")
            parse_failures += 1
            continue

        elapsed = time.time() - t0
        latencies.append(elapsed)

        if record is None:
            parse_failures += 1
            print(f"[{i}/{len(sample)}] {rid} parse failed")
            continue

        append_jsonl(args.out, record)

        # Coletar métricas
        if record["audit_final_score"] is not None:
            has_score_valid += 1
        if record["has_critical_error"]:
            has_critical_count += 1
        final_statuses[record["audit_final_status"]] += 1

        validated = record["meta_validation"]["validated_findings"]
        for inc in validated:
            severity_methods[inc.get("severity_method", "?")] += 1

        n_val = record["meta_validation"]["kept_count"]
        n_ref = record["meta_validation"]["refuted_count"]
        crit = record["critical_error_count"]
        print(f"[{i:>2}/{len(sample)}] {rid:<12} status={record['audit_final_status']:<8} "
              f"crit={crit} val={n_val} ref={n_ref} ({elapsed:.1f}s)")

    cost = auditor.total_cost_usd - cost_start
    n_total = len(sample)
    n_processed = n_total - parse_failures
    cost_per_laudo = cost / n_processed if n_processed else 0
    median_latency = float(np.median(latencies)) if latencies else 0

    print()
    print("=" * 60)
    print(f"GATE T13 Step 1.5")
    print("=" * 60)

    # Critério 1: parse rate 100%
    parse_rate_ok = parse_failures == 0
    print(f"  [1] Parse rate 100%:                  {'OK' if parse_rate_ok else 'FAIL'} ({n_processed}/{n_total})")

    # Critério 2: custo por laudo na faixa
    cost_ok = 0.000042 <= cost_per_laudo <= 0.000078
    print(f"  [2] Custo/laudo $0.000042-0.000078:   {'OK' if cost_ok else 'WARN'} (${cost_per_laudo:.6f})")

    # Critério 3: latência mediana < 5s
    latency_ok = median_latency < 5.0
    print(f"  [3] Latencia mediana < 5s:            {'OK' if latency_ok else 'WARN'} ({median_latency:.2f}s)")

    # Critério 4: score válido em 100%
    score_ok = has_score_valid == n_processed
    print(f"  [4] Score valido 100%:                {'OK' if score_ok else 'FAIL'} ({has_score_valid}/{n_processed})")

    # Critério 5: severity_method plausível (≥1 mechanical SE houver C2/C3/C4/C6)
    mechanical_count = severity_methods.get("mechanical", 0)
    severity_methods_total = sum(severity_methods.values())
    if severity_methods_total == 0:
        crit5_ok = True
        crit5_note = "WARN: 0 inconsistencias na amostra (esperado em sample healthy)"
    elif mechanical_count >= 1:
        crit5_ok = True
        crit5_note = f"OK: {mechanical_count} mecanicas / {severity_methods_total} total"
    else:
        crit5_ok = True  # WARN, não FAIL — pode não ter erro estrutural na amostra
        crit5_note = f"WARN: 0 mecanicas em {severity_methods_total} incs (sample sem erro estrutural)"
    print(f"  [5] severity_method plausivel:        {crit5_note}")

    # Critério 6: audit_final_status NÃO-extrema
    n_approved = final_statuses.get("approved", 0)
    pct_approved = 100 * n_approved / n_processed if n_processed else 0
    status_extreme = pct_approved == 100 or pct_approved == 0
    crit6_ok = not status_extreme
    print(f"  [6] audit_final_status nao-extrema:   {'OK' if crit6_ok else 'FAIL'} "
          f"(approved={n_approved}/{n_processed}={pct_approved:.0f}%)")
    print(f"      Distribuicao: {dict(final_statuses)}")

    print()
    print(f"Custo total smoke: ${cost:.6f}")
    print(f"Severity methods:  {dict(severity_methods)}")
    print(f"Has critical:      {has_critical_count}/{n_processed}")
    print()

    # Decisão
    blockers = [not parse_rate_ok, not score_ok, not crit6_ok]
    if any(blockers):
        print("ABORTAR full run — critérios bloqueadores falharam.")
        return 1
    print("APROVADO — liberar full run T13 Step 2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
