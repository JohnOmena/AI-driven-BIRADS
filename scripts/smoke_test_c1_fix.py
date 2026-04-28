"""Smoke test do fix C1 (T12.5).

Roda em 2 modos:
  --limit 5  → validação rápida da estrutura (não mede FP)
  --limit 20 → critério de aprovação: redução >=70% em FP C1 vs prompt antigo

Antes (Phase A): 70/86 keeps refutados pela meta-validação eram em C1 (81.4%).
Causas: lineal fino (ES), pleomorfico (sem til), heterogeneo (PT-pt),
formas só masculinas, calcificações ausentes do prompt.

Depois (T12.5): C1 derivado do Atlas com todas pt_variants_acceptable.
Esperamos que a maior parte dos FP desapareça.

Critério de pass do mode 20:
  C1_after / C1_before <= 0.30  (>=70% redução)
Se falhar, abortar T12.5 e investigar.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()

# ensure repo root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.translation.client import create_client
from src.translation.glossary import load_glossary, format_glossary_for_prompt
from src.translation.translate import audit_report


def select_c1_samples(limit: int):
    """Seleciona laudos da Phase A com inconsistência em C1.

    Lê audit_results.json (517 da última sessão) e filtra os que tiveram
    finding em C1 no round 0. Esses são os candidatos a "FP fixed by T12.5".
    """
    path = Path("results/translation/audit_results.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    samples = []
    for rec in data:
        hist = rec.get("correction_history") or []
        if not hist:
            continue
        round0 = hist[0]
        incs = round0.get("inconsistencias") or []
        c1_incs = [i for i in incs if i.get("criterio", "").startswith("C1")]
        if not c1_incs:
            continue
        samples.append({
            "report_id":      rec["report_id"],
            "es_text":        rec["original_text"],
            "pt_text":        rec["translated_text"],
            "c1_before":      len(c1_incs),
        })
        if len(samples) >= limit:
            break
    return samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5,
                        help="5 (mini smoke) ou 20 (full smoke com critério)")
    args = parser.parse_args()

    samples = select_c1_samples(args.limit)
    print(f"Smoke test C1 (T12.5): {len(samples)} laudos")
    print("=" * 60)

    cfg = yaml.safe_load(Path("configs/models.yaml").read_text(encoding="utf-8"))
    auditor = create_client("deepseek-v3", cfg["models"]["deepseek-v3"])
    glossary_text = format_glossary_for_prompt(
        load_glossary("configs/birads_glossary_es_pt.json")
    )

    c1_before_total = sum(s["c1_before"] for s in samples)
    c1_after_total = 0
    parse_failures = 0
    elapsed_total = 0.0
    cost_start = auditor.total_cost_usd

    for i, s in enumerate(samples, 1):
        t0 = time.time()
        try:
            result = audit_report(
                s["es_text"], s["pt_text"], auditor,
                glossary_text, temperature=0,
            )
        except Exception as e:
            print(f"[{i}/{len(samples)}] {s['report_id']} EXCEPTION: {type(e).__name__}: {str(e)[:100]}")
            parse_failures += 1
            continue
        elapsed = time.time() - t0
        elapsed_total += elapsed

        if result is None:
            print(f"[{i}/{len(samples)}] {s['report_id']} FAILED parse")
            parse_failures += 1
            continue

        c1_after = sum(
            1 for inc in result.get("inconsistencias", [])
            if inc.get("criterio", "").startswith("C1")
        )
        c1_after_total += c1_after
        delta = c1_after - s["c1_before"]
        marker = "✓" if delta < 0 else ("=" if delta == 0 else "⚠")
        print(
            f"[{i:>2}/{len(samples)}] {s['report_id']}  "
            f"C1 {s['c1_before']} → {c1_after}  {marker}  "
            f"({elapsed:.1f}s)"
        )

    cost = auditor.total_cost_usd - cost_start
    print()
    print(f"{'='*60}")
    print(f"C1 inconsistências TOTAIS antes (Phase A):  {c1_before_total}")
    print(f"C1 inconsistências TOTAIS depois (T12.5):   {c1_after_total}")
    print(f"Parse failures:                             {parse_failures}")
    print(f"Tempo total:                                {elapsed_total:.1f}s")
    print(f"Custo total:                                ${cost:.6f}")

    if c1_before_total == 0:
        print("Reducao: indeterminada (0 incs antes)")
        return 0

    reduction = (c1_before_total - c1_after_total) / c1_before_total
    print(f"REDUÇÃO em C1: {100*reduction:.1f}%")

    # Critério apenas no modo full (limit >= 20)
    if args.limit >= 20:
        if reduction >= 0.70:
            print(f"\n✅ APROVADO: redução {100*reduction:.1f}% >= 70% threshold")
            return 0
        else:
            print(f"\n❌ REPROVADO: redução {100*reduction:.1f}% < 70% threshold")
            print("   Abortar T12.5 e investigar antes de T13.")
            return 1
    else:
        print(f"\n(modo --limit {args.limit}: sem critério, apenas validação estrutural)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
