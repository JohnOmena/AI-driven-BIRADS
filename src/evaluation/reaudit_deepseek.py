"""T13 — Reaudit DeepSeek sobre 4357 laudos com prompt corrigido (T12.5+T12.6).

Restart-safe via JSONL append + load_done_ids. Schema separa audit_raw
(o que LLM disse) de meta_validation (o que sobreviveu ao filtro).
Severity layer (T12.6) aplicada inline via parse_audit_response.

Checkpoints automáticos a cada CHECKPOINT_INTERVAL=500 laudos:
  - git add audit_deepseek.jsonl
  - git commit -m "chore(t13): WIP X/4357 audited"
  - git push (best-effort, não falha se offline)

Modos:
  --limit N       processa apenas N laudos (smoke / debug)
  --no-checkpoint desliga commits durante execução
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.evaluation.io import append_jsonl, load_done_ids
from src.evaluation.severity import (
    apply_severity_override,
    count_by_severity,
    has_critical,
)
from src.translation.client import create_client
from src.translation.glossary import load_glossary, format_glossary_for_prompt
from src.translation.prompt import build_audit_prompt
from src.translation.translate import audit_report
from src.translation.validate import validate_audit_findings


CHECKPOINT_INTERVAL = 500
OUT_PATH = "results/translation/audit_deepseek.jsonl"
COST_LEDGER = "results/translation/cost_ledger.json"


def _prompt_hash() -> str:
    """Hash do prompt do auditor (varia se prompt.py for editado)."""
    sample = build_audit_prompt("ES_DUMMY", "PT_DUMMY", "GLOSSARY_DUMMY")
    return "sha256:" + hashlib.sha256(sample.encode("utf-8")).hexdigest()[:16]


def derive_audit_final_status(audit_raw: dict, validated_findings: list[dict]) -> str:
    """Regra: rejected se has_critical_error; review se findings validadas
    sem critical; approved caso contrário."""
    if has_critical(validated_findings):
        return "rejected"
    if len(validated_findings) > 0:
        return "review"
    return "approved" if audit_raw.get("aprovado", True) else "review"


def build_record(rid: str, es_text: str, pt_text: str,
                 auditor, glossary_text: str, glossary_pairs: list,
                 prompt_hash: str) -> dict | None:
    """Audit + meta-validate + severity. Retorna record completo ou None se falha."""
    audit_result = audit_report(es_text, pt_text, auditor,
                                 glossary_text, temperature=0)
    if audit_result is None:
        return None

    raw_incs = audit_result.get("inconsistencias", [])  # já com severity (T12.6)

    # Meta-validação programática (regex-based, não LLM)
    meta = validate_audit_findings(es_text, pt_text, audit_result, glossary_pairs)
    validated_findings = meta.get("confirmed", [])
    refuted_findings = meta.get("rejected", [])

    # Severity layer também aplicada nos validated/refuted (caso meta tenha alterado fields)
    validated_findings = apply_severity_override(validated_findings)
    refuted_findings = apply_severity_override(refuted_findings)

    # Severity counters sobre validated_findings
    counts = count_by_severity(validated_findings)
    has_crit = has_critical(validated_findings)
    final_status = derive_audit_final_status(audit_result, validated_findings)

    record = {
        "report_id":   rid,
        "auditor":     "deepseek-v3",
        "audited_at":  pd.Timestamp.utcnow().isoformat(),
        "prompt_hash": prompt_hash,

        "audit_raw": {
            "approved":         audit_result.get("aprovado"),
            "score":            audit_result.get("score"),
            "criteria":         audit_result.get("criterios", {}),
            "inconsistencies":  raw_incs,
        },

        "meta_validation": {
            "validator_model":     "deepseek-v3",
            "validated_findings":  validated_findings,
            "refuted_findings":    refuted_findings,
            "kept_count":          len(validated_findings),
            "refuted_count":       len(refuted_findings),
        },

        "audit_final_status":   final_status,
        "audit_final_score":    audit_result.get("score"),

        # Top-level severity counters (consumidos por T20)
        "critical_error_count": counts["critical"],
        "major_error_count":    counts["major"],
        "minor_error_count":    counts["minor"],
        "has_critical_error":   has_crit,
    }
    return record


def checkpoint_commit(progress: int, total: int, push: bool = True) -> None:
    """git add + commit + (best-effort) push do JSONL parcial."""
    try:
        subprocess.run(
            ["git", "add", OUT_PATH],
            check=True, capture_output=True, text=True,
        )
        result = subprocess.run(
            ["git", "commit", "-m", f"chore(t13): WIP {progress}/{total} audited"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"  [checkpoint commit] {progress}/{total}")
            if push:
                push_res = subprocess.run(["git", "push"], capture_output=True, text=True, timeout=30)
                if push_res.returncode == 0:
                    print(f"  [checkpoint push] OK")
                else:
                    print(f"  [checkpoint push] failed (continuing): {push_res.stderr[:100]}")
        else:
            # Sem mudanças desde último commit — silencioso
            pass
    except Exception as e:
        print(f"  [checkpoint] WARN: {type(e).__name__}: {str(e)[:100]}")


def update_cost_ledger(task_key: str, cost_usd: float, n_records: int,
                       tokens_in: int, tokens_out: int) -> None:
    """Atualiza results/translation/cost_ledger.json (G3 governance)."""
    p = Path(COST_LEDGER)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        ledger = json.loads(p.read_text(encoding="utf-8"))
    else:
        ledger = {}

    ledger[task_key] = {
        "task":         task_key.upper(),
        "cost_usd":     round(cost_usd, 4),
        "n_records":    n_records,
        "tokens_in":    tokens_in,
        "tokens_out":   tokens_out,
        "updated_at":   pd.Timestamp.utcnow().isoformat(),
    }
    ledger["total_phase_b_usd"] = round(
        sum(v["cost_usd"] for k, v in ledger.items()
            if k != "total_phase_b_usd" and isinstance(v, dict) and "cost_usd" in v),
        4,
    )
    p.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Processar apenas N laudos (smoke/debug)")
    parser.add_argument("--no-checkpoint", action="store_true",
                        help="Desliga commits automaticos durante execucao")
    args = parser.parse_args()

    # Inputs
    df_pt = pd.read_csv("data/reports_translated_pt.csv")
    df_pt = df_pt.drop_duplicates("report_id", keep="last")
    df_es = pd.read_csv("data/reports_raw_canonical.csv")

    # Cliente DeepSeek
    cfg = yaml.safe_load(Path("configs/models.yaml").read_text(encoding="utf-8"))
    auditor = create_client("deepseek-v3", cfg["models"]["deepseek-v3"])
    glossary_pairs = load_glossary("configs/birads_glossary_es_pt.json")
    glossary_text = format_glossary_for_prompt(glossary_pairs)
    p_hash = _prompt_hash()
    print(f"Prompt hash: {p_hash}")

    # Resume — quem já foi processado pula
    done_ids = load_done_ids(OUT_PATH)
    all_ids = sorted(set(df_pt["report_id"]).intersection(set(df_es["report_id"])))
    pending = [rid for rid in all_ids if rid not in done_ids]
    if args.limit:
        pending = pending[: args.limit]

    total_target = len(done_ids) + len(pending)
    print(f"Já processados: {len(done_ids)}")
    print(f"Pendentes:      {len(pending)}")
    print(f"Output:         {OUT_PATH}")
    print(f"Checkpoint cada: {CHECKPOINT_INTERVAL} laudos" if not args.no_checkpoint else "Checkpoints DESATIVADOS")
    print()

    cost_start = auditor.total_cost_usd
    in_tokens_start = auditor.total_input_tokens
    out_tokens_start = auditor.total_output_tokens
    t_start = time.time()

    df_pt_idx = df_pt.set_index("report_id")
    df_es_idx = df_es.set_index("report_id")

    failures = 0
    for i, rid in enumerate(pending):
        try:
            es_text = df_es_idx.loc[rid]["report_text_raw"]
            pt_text = df_pt_idx.loc[rid]["report_text_raw"]
        except KeyError:
            print(f"  [{i+1}/{len(pending)}] {rid} MISSING in df_es or df_pt -- skipping")
            failures += 1
            continue

        try:
            record = build_record(rid, es_text, pt_text,
                                   auditor, glossary_text, glossary_pairs, p_hash)
        except Exception as e:
            print(f"  [{i+1}/{len(pending)}] {rid} EXC: {type(e).__name__}: {str(e)[:120]}")
            failures += 1
            continue

        if record is None:
            print(f"  [{i+1}/{len(pending)}] {rid} build_record returned None")
            failures += 1
            continue

        append_jsonl(OUT_PATH, record)

        progress = len(done_ids) + i + 1
        if (i + 1) % 25 == 0 or (i + 1) == len(pending):
            elapsed = time.time() - t_start
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(pending) - i - 1) / rate if rate > 0 else 0
            print(
                f"  [{progress}/{total_target}] "
                f"cost=${auditor.total_cost_usd:.4f} "
                f"rate={rate:.2f}/s eta={eta/60:.1f}min"
            )

        # Checkpoint commit
        if not args.no_checkpoint and (i + 1) % CHECKPOINT_INTERVAL == 0:
            checkpoint_commit(progress, total_target, push=True)

    # Final stats
    cost = auditor.total_cost_usd - cost_start
    tokens_in = auditor.total_input_tokens - in_tokens_start
    tokens_out = auditor.total_output_tokens - out_tokens_start
    elapsed = time.time() - t_start

    print()
    print("=" * 60)
    print(f"Total processados:  {len(pending) - failures}")
    print(f"Falhas:             {failures}")
    print(f"Tempo total:        {elapsed/60:.2f} min")
    print(f"Custo:              ${cost:.6f}")
    print(f"Tokens in/out:      {tokens_in:,}/{tokens_out:,}")

    # Atualiza cost_ledger
    if not args.limit:  # só registra ledger no full run
        update_cost_ledger("t13", cost, len(pending) - failures, tokens_in, tokens_out)

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
