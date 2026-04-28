"""Gate de retrocompatibilidade do glossário Atlas.

Princípio: o tradutor (Phase A) recebeu o glossário antigo (95 termos).
O Atlas pode ter `pt_canonical` diferente, mas TODA escolha PT do antigo
deve aparecer em `pt_variants_acceptable` da entrada Atlas correspondente.

Sem isso, T13 (reaudit DeepSeek) e T17 (léxico) gerariam falso-positivo
retroativo — punir o tradutor por algo que ele não foi instruído a fazer.

Falha em CI bloqueia commit de T12.
"""

import json
import sys
from pathlib import Path


def main() -> int:
    old = json.loads(
        Path("configs/birads_glossary_es_pt.json").read_text(encoding="utf-8")
    )
    new = json.loads(
        Path("configs/birads_glossary_atlas_es_pt.json").read_text(encoding="utf-8")
    )

    # Flatten old PT terms (lowercased)
    old_pt = set()
    for cat, items in old["terms"].items():
        for entry in items:
            old_pt.add(entry["pt"].strip().lower())

    # Flatten Atlas acceptable variants
    new_acceptable = set()
    for cat, items in new["categories"].items():
        for entry in items:
            new_acceptable.add(entry["pt_canonical"].strip().lower())
            for v in entry.get("pt_variants_acceptable", []):
                new_acceptable.add(v.strip().lower())

    missing = old_pt - new_acceptable
    if missing:
        print("FAIL: termos PT do glossário original NÃO cobertos pelo Atlas:")
        for t in sorted(missing):
            print(f"  - {t}")
        return 1

    print(f"OK: 100% dos {len(old_pt)} termos PT do glossário original aparecem em pt_variants_acceptable do Atlas")
    print(f"Atlas total de variantes aceitáveis (canonical + variants): {len(new_acceptable)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
