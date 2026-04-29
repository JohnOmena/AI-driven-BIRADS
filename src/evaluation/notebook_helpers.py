"""T23 — Helpers estatísticos para o notebook consolidado.

Padroniza:
  - median_with_ci (bootstrap BCa)
  - proportion_with_ci (Wilson — robusto em 0/N e N/N)
  - rate_with_ci (wrapper para taxas booleanas)
  - build_executive_summary (tabela 1-página com 3 níveis de aprovação)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import bootstrap


def median_with_ci(values, alpha: float = 0.05, n_resamples: int = 10000):
    """Mediana + IC bootstrap BCa (alinhado com T15/T18/T19/T21)."""
    arr = np.array(values)
    arr = arr[~pd.isna(arr)]
    if len(arr) < 2:
        return None, None, None
    res = bootstrap((arr,), np.median, n_resamples=n_resamples,
                    confidence_level=1 - alpha, method="BCa")
    return (
        float(np.median(arr)),
        float(res.confidence_interval.low),
        float(res.confidence_interval.high),
    )


def proportion_with_ci(successes: int, total: int, alpha: float = 0.05):
    """Wilson score interval — robusto em 0/N e N/N (corner cases comuns em H8)."""
    if total == 0:
        return None, None, None
    p = successes / total
    z = 1.96  # alpha=0.05
    denom = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denom
    half = z * np.sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denom
    return p, max(0.0, center - half), min(1.0, center + half)


def rate_with_ci(values, alpha: float = 0.05, n_resamples: int = 10000):
    """Taxas (booleanos) — usa median_with_ci com cast."""
    return median_with_ci([float(v) for v in values], alpha, n_resamples)


def build_executive_summary(records, summaries) -> pd.DataFrame:
    """Tabela 1-página com 3 taxas separadas (Ajuste #5):
      - clinical_pass:  ignora modifier-only failures
      - overall_passed: agregado completo
      - critical_error_rate: H8
    """
    n = len(records)
    if n == 0:
        return pd.DataFrame(columns=["Dimensão", "Métrica", "Valor", "Critério"])

    n_passed = sum(1 for r in records if r.get("overall_passed"))
    n_clinical = sum(1 for r in records if r.get("clinical_pass"))
    n_critical = sum(
        1 for r in records
        if r.get("validations", {}).get("audit_deepseek", {}).get("has_critical_error")
    )
    composite_median = float(
        pd.Series([r.get("composite_score") for r in records if r.get("composite_score") is not None]).median()
    ) if records else 0

    rows = [
        ("Volume",           "Laudos consolidados",                f"{n:,}",                                 "—"),
        ("Volume",           "Cobertura completa",                  f"{n}/4357",                               "100%"),
        ("Aprovação",        "clinical_pass (sem modifier-only)",   f"{n_clinical/n:.1%}",                    "≥ 95%"),
        ("Aprovação",        "overall_passed (todas as fontes)",    f"{n_passed/n:.1%}",                      "≥ 90%"),
        ("Aprovação",        "composite_score (mediana)",           f"{composite_median:.1f}",                "≥ 90"),
        ("Erro crítico (H8)", "Taxa (has_critical_error)",          f"{n_critical/n:.2%}",                    "≤ 1%"),
        ("Semântica (H1)",   "BERTScore-F1 (mediana)",
         f"{summaries.get('intrinsic', {}).get('bertscore_f1_median', '?')}", "≥ 0.90"),
        ("Léxico (H2)",      "overall_acceptable_rate",
         f"{summaries.get('lexical', {}).get('overall_acceptable_rate', '?')}", "≥ 0.99"),
        ("Estabilidade (H5)", "cosine_pt_pt mediana",
         f"{summaries.get('duplicate', {}).get('median_cosine_pt_pt', '?')}", "≥ 0.98"),
    ]
    return pd.DataFrame(rows, columns=["Dimensão", "Métrica", "Valor", "Critério"])
