"""Gate de morfologia do Atlas.

Para entradas com `forms_pt` ou `forms_es` (adjetivos canônicos T18):
- 4 tags obrigatórias: M-SING, F-SING, M-PLUR, F-PLUR
- toda forma_pt listada deve estar em pt_variants_acceptable
- toda forma_es listada deve ser válida (não checamos lista — sem es_variants_acceptable)

Falha bloqueia commit de T12 (pré-requisito de T18).
"""

import json
import sys
from pathlib import Path


REQUIRED_TAGS = {"M-SING", "F-SING", "M-PLUR", "F-PLUR"}


def main() -> int:
    atlas = json.loads(
        Path("configs/birads_glossary_atlas_es_pt.json").read_text(encoding="utf-8")
    )

    errors: list[str] = []
    n_with_forms = 0

    for cat_key, entries in atlas["categories"].items():
        for entry in entries:
            has_forms_pt = "forms_pt" in entry
            has_forms_es = "forms_es" in entry
            if not (has_forms_pt or has_forms_es):
                continue
            n_with_forms += 1

            # Forms devem vir em par
            if has_forms_pt != has_forms_es:
                errors.append(
                    f"{entry['es']} ({cat_key}): forms_pt e forms_es devem coexistir"
                )

            # 4 tags obrigatórias
            for field in ("forms_pt", "forms_es"):
                forms = entry.get(field, {})
                missing = REQUIRED_TAGS - set(forms.keys())
                if missing:
                    errors.append(
                        f"{entry['es']} ({cat_key}): {field} faltam tags {sorted(missing)}"
                    )

            # forms_pt -> deve estar em pt_variants_acceptable (consistência interna)
            acceptable = {v.lower() for v in entry.get("pt_variants_acceptable", [])}
            acceptable.add(entry["pt_canonical"].lower())
            for tag, form in entry.get("forms_pt", {}).items():
                if form.lower() not in acceptable:
                    errors.append(
                        f"{entry['es']} ({cat_key}): forms_pt[{tag}]={form!r} "
                        f"não está em pt_variants_acceptable"
                    )

    if errors:
        print(f"FAIL: morfologia inconsistente em {len(errors)} item(ns):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: morfologia validada para {n_with_forms} entradas com forms_pt/forms_es")
    return 0


if __name__ == "__main__":
    sys.exit(main())
