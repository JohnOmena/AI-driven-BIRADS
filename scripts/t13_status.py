"""Mini relatório de progresso do T13.

Lê audit_deepseek.jsonl e produz snapshot:
  - Cobertura (X / 4357)
  - Distribuicao de audit_final_status
  - Severity counts (critical/major/minor)
  - has_critical_error rate
  - Custo extrapolado
  - Tempo decorrido + ETA

Uso: python scripts/t13_status.py
"""
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path


JSONL = "results/translation/audit_deepseek.jsonl"
LOG = "results/translation/reaudit_deepseek.log"
PID_FILE = "results/translation/reaudit_deepseek.pid"
TARGET = 4357


def main():
    p = Path(JSONL)
    if not p.exists():
        print("Sem audit_deepseek.jsonl ainda")
        return

    n = 0
    status_counter = Counter()
    crit_total = major_total = minor_total = 0
    has_crit_count = 0
    score_sum = 0
    score_count = 0

    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            n += 1
            status_counter[rec.get("audit_final_status", "?")] += 1
            crit_total += rec.get("critical_error_count", 0)
            major_total += rec.get("major_error_count", 0)
            minor_total += rec.get("minor_error_count", 0)
            if rec.get("has_critical_error"):
                has_crit_count += 1
            score = rec.get("audit_final_score")
            if score is not None:
                score_sum += score
                score_count += 1

    pct = 100 * n / TARGET if TARGET else 0
    print("=" * 60)
    print(f"T13 — mini relatório @ {n}/{TARGET} ({pct:.1f}%)")
    print("=" * 60)
    print()
    print("Status:")
    for st, c in status_counter.most_common():
        pct_st = 100 * c / n if n else 0
        print(f"  {st:<10} {c:>4} ({pct_st:>5.1f}%)")

    print()
    print(f"Severity (sobre validated findings):")
    print(f"  critical {crit_total:>4}")
    print(f"  major    {major_total:>4}")
    print(f"  minor    {minor_total:>4}")
    print()
    print(f"Laudos com >=1 erro crítico: {has_crit_count}/{n} ({100*has_crit_count/n if n else 0:.2f}%)")

    if score_count > 0:
        print(f"Score audit médio: {score_sum/score_count:.2f}")

    # Health do processo
    if Path(PID_FILE).exists():
        pid = Path(PID_FILE).read_text().strip()
        # Tenta verificar (Windows: tasklist; mas em git bash, ps -p)
        try:
            result = os.popen(f"ps -p {pid}").read()
            if pid in result:
                print(f"\nProcesso PID {pid}: RODANDO")
            else:
                print(f"\nProcesso PID {pid}: MORTO ou finalizado")
        except Exception:
            print(f"\nProcesso PID {pid}: status desconhecido")

    # Última linha do log
    if Path(LOG).exists():
        lines = Path(LOG).read_text(encoding="utf-8", errors="replace").strip().split("\n")
        last = [l for l in lines[-5:] if l.strip()]
        if last:
            print(f"\nÚltimas mensagens do log:")
            for l in last[-3:]:
                print(f"  {l[:120]}")


if __name__ == "__main__":
    main()
