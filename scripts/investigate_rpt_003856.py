"""Investigação do laudo RPT_003856 — único com aumento C1 (1→2) no smoke T12.5."""
import json
import sys
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.translation.client import create_client
from src.translation.glossary import load_glossary, format_glossary_for_prompt
from src.translation.translate import audit_report


def main():
    data = json.loads(
        Path("results/translation/audit_results.json").read_text(encoding="utf-8")
    )
    target = next(r for r in data if r["report_id"] == "RPT_003856")

    print("=" * 60)
    print("RPT_003856 — Phase A (PROMPT ANTIGO)")
    print("=" * 60)
    print(f"Status final: {target.get('status')}")
    print(f"Score: {target.get('audit', {}).get('score_global')}")
    hist = target.get("correction_history", [])
    if hist:
        incs0 = hist[0].get("inconsistencias", [])
        print(f"\nRound 0 — {len(incs0)} inconsistencia(s):")
        for i in incs0:
            print(f"  [{i.get('criterio')}] {i.get('problema', '')[:200]}")
            print(f"     orig: {i.get('original', '')[:100]!r}")
            print(f"     pt:   {i.get('traducao', '')[:100]!r}")
        verdict = hist[0].get("validation", {}).get("verdict")
        confirmed = hist[0].get("validation", {}).get("confirmed", 0)
        rejected = hist[0].get("validation", {}).get("rejected", 0)
        print(f"\nMeta-validation: verdict={verdict} confirmed={confirmed} rejected={rejected}")

    print()
    print("=" * 60)
    print("Re-auditando AGORA com PROMPT NOVO (T12.5)")
    print("=" * 60)

    cfg = yaml.safe_load(Path("configs/models.yaml").read_text(encoding="utf-8"))
    auditor = create_client("deepseek-v3", cfg["models"]["deepseek-v3"])
    glossary = format_glossary_for_prompt(
        load_glossary("configs/birads_glossary_es_pt.json")
    )

    t0 = time.time()
    result = audit_report(
        target["original_text"], target["translated_text"],
        auditor, glossary, temperature=0,
    )
    print(f"Tempo: {time.time()-t0:.1f}s, custo: ${auditor.total_cost_usd:.6f}")

    if result:
        print(f"\nScore: {result.get('score')}, aprovado: {result.get('aprovado')}")
        incs = result.get("inconsistencias", [])
        print(f"Inconsistencias: {len(incs)}")
        for i in incs:
            print(f"\n  [{i.get('criterio')}] {i.get('problema', '')[:300]}")
            print(f"     orig: {i.get('original', '')[:120]!r}")
            print(f"     pt:   {i.get('traducao', '')[:120]!r}")


if __name__ == "__main__":
    main()
