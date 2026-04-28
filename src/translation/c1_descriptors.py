"""Gera o bloco C1 do prompt do auditor a partir do glossário Atlas.

Substitui as listas hardcoded em prompt.py:130-134 que continham:
- Espanhol cru (lineal fino, pleomorfico)
- PT-pt sem til (heterogeneo, homogeneo)
- Apenas formas masculinas (obscurecido, isodenso)
- Categorias inteiras ausentes (calcificações, composição mamária)

Resultado de Phase A: 81.4% dos falsos positivos do auditor vinham de C1
(70 de 86 keeps refutados pela meta-validação na sample 517).

T12.5 deriva C1 dinamicamente do Atlas (T12), incluindo TODAS as variantes
de pt_variants_acceptable — não apenas pt_canonical. Auditor aceita qualquer
forma que o tradutor recebeu via glossário recebido.
"""

import json
from pathlib import Path


# Categorias do Atlas que entram em C1 (descritores BI-RADS).
# Decisão registrada em decision_log.md:
# - Inclui: descritores que modificam massas, calcificações, achados associados
# - Exclui: anatomia (âncoras), findings_mass (substantivos), categories_birads (C2),
#   assessment_terms (juízo), procedures, asymmetry_distortion, breast_composition
C1_CATEGORIES = [
    "mass_shape",
    "mass_margin",
    "mass_density",
    "calcifications_morphology",
    "calcifications_distribution",
    "associated_features",
]

C1_LABELS = {
    "mass_shape":                  "Forma",
    "mass_margin":                 "Margem",
    "mass_density":                "Densidade",
    "calcifications_morphology":   "Morfologia de calcificacoes",
    "calcifications_distribution": "Distribuicao de calcificacoes",
    "associated_features":         "Achados associados",
}


def build_c1_block(atlas_path: str = "configs/birads_glossary_atlas_es_pt.json") -> str:
    """Build the C1 audit block from Atlas glossary.

    Cada categoria lista TODAS as variantes aceitáveis (canonical ∪ acceptable)
    separadas por `/`. Auditor aceita qualquer forma listada.

    Política T12.5 (registrada em decision_log.md):
    - "Aceite QUALQUER variante listada acima como correta."
    - Concordância de gênero/número é coberta por T18 (modifier preservation),
      não por C1 — C1 só verifica se o termo BI-RADS foi usado.
    """
    atlas = json.loads(Path(atlas_path).read_text(encoding="utf-8"))
    cats = atlas["categories"]

    lines = [
        "C1. DESCRITORES BI-RADS (PRIORIDADE MAXIMA): Os descritores padronizados "
        "BI-RADS foram traduzidos corretamente para o portugues conforme o glossario? "
        "Verifique CADA descritor presente no original:"
    ]

    for cat_key in C1_CATEGORIES:
        if cat_key not in cats:
            continue
        label = C1_LABELS[cat_key]
        # Coletar TODAS variantes aceitáveis (canonical + variants), deduplicadas
        all_terms = []
        for entry in cats[cat_key]:
            variants = set()
            variants.add(entry["pt_canonical"])
            variants.update(entry.get("pt_variants_acceptable", []))
            # Ordenar para output determinístico
            joined = "/".join(sorted(variants))
            all_terms.append(joined)
        terms_str = ", ".join(all_terms)
        lines.append(f"    - {label}: {terms_str}")

    lines.append(
        "    Aceite QUALQUER variante listada acima como correta. "
        "Variacao de genero/numero (ex: 'espiculada' vs 'espiculado') NAO e "
        "erro neste criterio se ambas estao listadas — concordancia "
        "morfossintatica e auditada separadamente. Reporte erro em C1 apenas "
        "se o tradutor usou um termo NAO listado em nenhuma das variantes acima."
    )
    return "\n".join(lines)
