"""Coleta variantes PT empíricas do corpus traduzido (Phase A).

Para cada (es, pt) do glossário original (~95 termos), busca no corpus
PT-br quais variantes morfológicas (singular/plural, masculino/feminino)
de fato apareceram. A saída é insumo direto para `pt_variants_acceptable`
do glossário Atlas (T12 Step 3) — garante retrocompatibilidade
empiricamente, não por chute.
"""

import json
import re
import unicodedata
from pathlib import Path

import pandas as pd


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def morphological_candidates(pt: str) -> set[str]:
    """Gera candidatos morfológicos prováveis a partir do termo PT base.

    Cobre formas singular/plural e masc/fem comuns. Não tenta cobrir
    irregularidades — busca exata no corpus filtra falsos.
    """
    pt = pt.strip()
    cands = {pt, pt.lower()}

    if pt.endswith("o"):
        cands.add(pt[:-1] + "a")  # masc -> fem
        cands.add(pt + "s")        # masc plur
        cands.add(pt[:-1] + "as")  # fem plur
    if pt.endswith("a"):
        cands.add(pt[:-1] + "o")  # fem -> masc
        cands.add(pt + "s")        # fem plur
        cands.add(pt[:-1] + "os")  # masc plur
    if pt.endswith("ção"):
        cands.add(pt[:-3] + "ções")  # singular -> plural
    if pt.endswith("ções"):
        cands.add(pt[:-4] + "ção")
    if pt.endswith("em"):
        cands.add(pt[:-2] + "ens")  # margem -> margens
    if pt.endswith("ens"):
        cands.add(pt[:-3] + "em")

    # Sempre adicionar plural simples se não terminado em -s
    if not pt.endswith("s"):
        cands.add(pt + "s")

    return {c.lower() for c in cands if c}


def main():
    old_glossary = json.loads(
        Path("configs/birads_glossary_es_pt.json").read_text(encoding="utf-8")
    )
    df = pd.read_csv("data/reports_translated_pt.csv")
    pt_corpus = " ".join(df["report_text_raw"].fillna("").astype(str)).lower()

    findings = {}
    n_terms = 0
    for cat, items in old_glossary["terms"].items():
        for entry in items:
            es, pt = entry["es"], entry["pt"]
            n_terms += 1
            cands = morphological_candidates(pt)
            observed = []
            for c in sorted(cands):
                pattern = r"\b" + re.escape(c) + r"\b"
                if re.search(pattern, pt_corpus):
                    observed.append(c)
            findings[es] = {
                "pt_canonical_old": pt,
                "category": cat,
                "observed_variants": observed,
            }

    out_path = Path("results/translation/observed_pt_variants.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Stats
    n_with_observed = sum(1 for v in findings.values() if v["observed_variants"])
    total_variants = sum(len(v["observed_variants"]) for v in findings.values())
    print(f"Termos analisados:          {n_terms}")
    print(f"Termos com variante observada: {n_with_observed}")
    print(f"Total variantes únicas:     {total_variants}")
    print(f"Saida: {out_path}")
    print()
    print("Amostra (10 primeiros termos com >1 variante):")
    multi = {es: v for es, v in findings.items() if len(v["observed_variants"]) > 1}
    for es, v in list(multi.items())[:10]:
        print(f"  {es:<32} -> {v['observed_variants']}")


if __name__ == "__main__":
    main()
