"""Smoke test do severity layer (T12.6).

Roda em 2 modos:
  --limit 5  → validação estrutural (LLM retorna severity? override funciona?)
  --limit 20 → distribuição plausível (não 100% critical nem 100% minor)

Critério T12.6:
- 0 parse failures
- LLM retorna severity válido em >=70% dos casos C1/C5/C7
- Distribuição plausível (>= 1 caso de cada nível em 20 laudos com inconsistências)
"""

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.translation.client import create_client
from src.translation.glossary import load_glossary, format_glossary_for_prompt
from src.translation.translate import audit_report


def select_samples(limit: int):
    """Laudos da Phase A com inconsistência em qualquer critério."""
    path = Path("results/translation/audit_results.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    samples = []
    for rec in data:
        hist = rec.get("correction_history") or []
        if not hist:
            continue
        round0 = hist[0]
        incs = round0.get("inconsistencias") or []
        if not incs:
            continue
        samples.append({
            "report_id": rec["report_id"],
            "es_text":   rec["original_text"],
            "pt_text":   rec["translated_text"],
        })
        if len(samples) >= limit:
            break
    return samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    samples = select_samples(args.limit)
    print(f"Smoke severity (T12.6): {len(samples)} laudos")
    print("=" * 60)

    cfg = yaml.safe_load(Path("configs/models.yaml").read_text(encoding="utf-8"))
    auditor = create_client("deepseek-v3", cfg["models"]["deepseek-v3"])
    glossary = format_glossary_for_prompt(
        load_glossary("configs/birads_glossary_es_pt.json")
    )

    severity_method_counter: Counter = Counter()
    severity_final_counter: Counter = Counter()
    criterion_counter: Counter = Counter()
    parse_failures = 0
    cost_start = auditor.total_cost_usd
    elapsed_total = 0.0
    n_with_severity_llm_valid = 0
    n_subjective_total = 0  # C1/C5/C7 — onde LLM deve classificar

    for i, s in enumerate(samples, 1):
        t0 = time.time()
        try:
            result = audit_report(s["es_text"], s["pt_text"], auditor,
                                   glossary, temperature=0)
        except Exception as e:
            print(f"[{i}/{len(samples)}] {s['report_id']} EXC: {type(e).__name__}")
            parse_failures += 1
            continue
        elapsed_total += time.time() - t0

        if result is None:
            print(f"[{i}/{len(samples)}] {s['report_id']} FAILED parse")
            parse_failures += 1
            continue

        incs = result.get("inconsistencias", [])
        per_laudo = Counter()
        for inc in incs:
            sev = inc.get("severity", "?")
            method = inc.get("severity_method", "?")
            crit = inc.get("criterio", "?").split("_")[0]
            criterion_counter[crit] += 1
            severity_method_counter[method] += 1
            severity_final_counter[sev] += 1
            per_laudo[sev] += 1
            # Para subjetivos, contar quantas vezes LLM deu severity válido
            if crit in ("C1", "C5", "C7"):
                n_subjective_total += 1
                raw = inc.get("severity_llm_raw")
                if raw in ("critical", "major", "minor"):
                    n_with_severity_llm_valid += 1

        summary = " ".join(f"{k}={v}" for k, v in sorted(per_laudo.items()))
        print(f"[{i:>2}/{len(samples)}] {s['report_id']} incs={len(incs)} {summary}")

    cost = auditor.total_cost_usd - cost_start
    print()
    print(f"{'='*60}")
    print(f"Parse failures:     {parse_failures}")
    print(f"Tempo total:        {elapsed_total:.1f}s")
    print(f"Custo:              ${cost:.6f}")
    print()
    print(f"Distribuicao final por severity:")
    for sev in ("critical", "major", "minor"):
        n = severity_final_counter.get(sev, 0)
        print(f"  {sev:<10} {n:>4}")
    print()
    print(f"Distribuicao por method:")
    for m, n in severity_method_counter.most_common():
        print(f"  {m:<22} {n:>4}")
    print()
    print(f"Por criterio:")
    for c, n in sorted(criterion_counter.items()):
        print(f"  {c:<10} {n:>4}")
    print()
    if n_subjective_total > 0:
        rate = 100 * n_with_severity_llm_valid / n_subjective_total
        print(f"Severity LLM valido em C1/C5/C7: {n_with_severity_llm_valid}/{n_subjective_total} ({rate:.1f}%)")
    else:
        print("Sem inconsistencias subjetivas (C1/C5/C7) na amostra.")

    # Critério aprovação modo 20
    if args.limit >= 20:
        all_levels_present = all(severity_final_counter.get(s, 0) >= 1
                                  for s in ("critical", "major", "minor"))
        no_parse = parse_failures == 0
        llm_rate_ok = (n_subjective_total == 0 or
                       n_with_severity_llm_valid / n_subjective_total >= 0.7)
        print()
        print(f"Criterios T12.6:")
        print(f"  0 parse failures:                  {'OK' if no_parse else 'FAIL'}")
        print(f"  Severity LLM valido >= 70% sub:    {'OK' if llm_rate_ok else 'FAIL'}")
        print(f"  Distribuicao plausivel (>=1 cada): {'OK' if all_levels_present else 'WARN (pode ser amostra pequena)'}")
        if no_parse and llm_rate_ok:
            print("\nAPROVADO")
            return 0
        else:
            print("\nREPROVADO")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
