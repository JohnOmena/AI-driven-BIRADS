"""T20 — Consolidação `validation_results.jsonl` (PRE-FLIGHT skeleton).

Schema unificado v1: 6 fontes + abstain semântico (passed/null/in_sample/in_pair).

PRE-FLIGHT scope (T20 fase 1):
  - Funções: assinaturas + lógica de overall_passed/clinical_pass/composite_score/
    failure_reasons/warnings (puras, sem I/O)
  - build_record/main: assinaturas declaradas, NÃO implementam I/O ainda
  - Testes mockados rodam ANTES da implementação completa
  - Pré-registro da fórmula composite_score em
    docs/superpowers/specs/composite_score_formula_v1.md (criado em commit separado)

Implementação completa (build_record I/O + main runner) acontece quando
T13 terminar (só consolida quando todos os artefatos estão prontos).

Princípio governante — três tipos de "valor":
  - passed: True/False  → fonte aplicável
  - passed: None        → abstain (T18 sem cobertura)
  - in_sample/in_pair: False → fonte não aplicável
Abstain e não-aplicável NÃO entram em overall_passed/composite_score.
"""
from __future__ import annotations

SCHEMA_VERSION = "2026-04-28-v1"


def overall_passed(v: dict) -> bool:
    """Aprovação multi-fonte com tratamento de abstain.

    Sempre conta: semantic, structural, lexical_birads, audit_deepseek.
    Conta se aplicável: modifier_agreement (passed != null),
                        back_translation (in_sample = true).
    NUNCA conta: duplicate_stability (priorização, não aprovação).
    """
    sources = [
        v["semantic"]["passed"],
        v["structural"]["all_structural_pass"],
        v["lexical_birads"]["passed"],
        v["audit_deepseek"]["passed"],
    ]
    if v["modifier_agreement"].get("passed") is not None:
        sources.append(v["modifier_agreement"]["passed"])
    if v["back_translation"].get("in_sample"):
        sources.append(v["back_translation"]["passed"])
    return all(sources)


def clinical_pass(v: dict) -> bool:
    """Aprovação CLÍNICA — ignora `modifier-only` failures.

    Hierarquia interpretativa:
      1. has_critical_error  → critério clínico estrito (alimenta H8)
      2. clinical_pass       → aprovação técnica clinicamente relevante
      3. overall_passed      → agregado completo (incluindo modifier)
      4. warnings            → flags para priorização (T22 Tier 4)
    """
    return all([
        v["semantic"]["passed"],
        v["structural"]["all_structural_pass"],
        v["lexical_birads"]["passed"],
        v["audit_deepseek"]["passed"],
        not v["audit_deepseek"]["has_critical_error"],
        (not v["back_translation"].get("in_sample")
         or v["back_translation"]["passed"]),
    ])


def failure_reasons(v: dict) -> list[str]:
    """Diagnóstico granular per-fonte para análise de erros (T23 §10)."""
    reasons = []
    if not v["semantic"]["passed"]:
        reasons.append("semantic")
    if not v["structural"]["all_structural_pass"]:
        reasons.append("structural")
    if not v["lexical_birads"]["passed"]:
        reasons.append("lexical")
    if v["modifier_agreement"].get("passed") is False:
        reasons.append("modifier")
    if not v["audit_deepseek"]["passed"]:
        reasons.append(
            "audit_critical" if v["audit_deepseek"]["has_critical_error"]
            else "audit_nonsuccess"
        )
    if v["back_translation"].get("in_sample") and not v["back_translation"]["passed"]:
        reasons.append("back_translation")
    return reasons


def warnings(v: dict) -> list[str]:
    """Flags que indicam atenção mas NÃO reprovação clínica."""
    w = []
    if v["modifier_agreement"].get("passed") is False:
        w.append("modifier_divergence")
    if v["duplicate_stability"].get("requires_review"):
        w.append("duplicate_structural_instability")
    return w


def composite_score(v: dict) -> float:
    """Fórmula v1 pré-registrada — pesos renormalizam por fontes ativas.

    Q_total = Σ(w_i · Q_i) / Σ(w_i_active)

    | Componente   | Peso | Ativo se          |
    | Q_semantic   | 0.20 | sempre            |
    | Q_structural | 0.25 | sempre            |
    | Q_lexical    | 0.15 | sempre            |
    | Q_audit      | 0.20 | sempre            |
    | Q_modifier   | 0.10 | passed != null    |
    | Q_back_trans | 0.10 | in_sample = true  |
    """
    components = {
        "Q_semantic":   (0.20, 100 * v["semantic"]["bertscore_f1"]),
        "Q_structural": (0.25, 100 if v["structural"]["all_structural_pass"] else 0),
        "Q_lexical":    (0.15, 100 * v["lexical_birads"]["overall_acceptable_rate"]),
        "Q_audit":      (0.20, 0 if v["audit_deepseek"]["has_critical_error"] else 100),
    }
    if v["modifier_agreement"].get("passed") is not None:
        components["Q_modifier"] = (0.10, 100 * v["modifier_agreement"]["preservation_rate"])
    if v["back_translation"].get("in_sample"):
        components["Q_back_trans"] = (0.10, 100 * v["back_translation"]["cosine_es_es_bt"])

    total_w = sum(w for w, _ in components.values())
    return round(sum(w * q for w, q in components.values()) / total_w, 2)


def build_record(rid, data, atlas_hash, prompt_hash) -> dict:
    """PRE-FLIGHT skeleton — implementação completa quando T13 terminar."""
    raise NotImplementedError(
        "build_record full I/O implementation pending T13 completion (consolidate runner)"
    )


def main():
    """PRE-FLIGHT skeleton — implementação completa quando T13 terminar."""
    raise NotImplementedError(
        "consolidate main runner pending T13 completion + all source artifacts"
    )
