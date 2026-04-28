"""Severidade clínica de inconsistências (T12.6).

Substitui o esquema binário aprovado/reprovado da auditoria por taxonomia
ancorada em impacto clínico, com regra determinística para critérios objetivos
(C2 categoria, C3 medidas, C4 lateralidade, C6 negação) — qualquer divergência
nesses é por definição `critical`. Para C1 (descritores), C5 (omissões/adições)
e C7 (temporais/achados associados), o LLM classifica e revisão MQM (T22) valida.

Decisão registrada em docs/superpowers/specs/decision_log.md.
"""

# C2/C3/C4/C6 são objetivos: divergência detectada é por definição critical
MECHANICAL_CRITICAL_CRITERIA = {"C2", "C3", "C4", "C6"}

# Critérios subjetivos onde o LLM classifica e MQM (T22) valida
LLM_JUDGED_CRITERIA = {"C1", "C5", "C7"}

VALID_SEVERITIES = {"critical", "major", "minor"}


def _criterion_short(criterio: str) -> str:
    """Normaliza 'C1_descritores_birads' -> 'C1'.

    O auditor pode retornar com sufixo (`C1_descritores_birads`) ou só `C1`.
    """
    if not criterio:
        return ""
    return criterio.strip().split("_")[0].upper()


def apply_severity_override(inconsistencias: list[dict]) -> list[dict]:
    """Aplica regra mecânica para C2/C3/C4/C6, mantém LLM em C1/C5/C7.

    Cada inconsistência ganha 3 campos:
    - `severity`: critical | major | minor (final, após override)
    - `severity_method`: mechanical | llm | fallback_minor | unknown_criterion
    - `severity_llm_raw`: o que o LLM disse (ou None se não veio)

    Não modifica os campos originais (criterio, problema, original, traducao).
    """
    out = []
    for inc in inconsistencias:
        crit = _criterion_short(inc.get("criterio", ""))
        sev_llm_raw = (inc.get("severity") or "").strip().lower() or None

        if crit in MECHANICAL_CRITICAL_CRITERIA:
            sev_final = "critical"
            sev_method = "mechanical"
        elif crit in LLM_JUDGED_CRITERIA:
            if sev_llm_raw in VALID_SEVERITIES:
                sev_final = sev_llm_raw
                sev_method = "llm"
            else:
                sev_final = "minor"  # fallback conservador
                sev_method = "fallback_minor"
        else:
            sev_final = "minor"
            sev_method = "unknown_criterion"

        new_inc = dict(inc)
        new_inc["severity"] = sev_final
        new_inc["severity_method"] = sev_method
        new_inc["severity_llm_raw"] = sev_llm_raw
        out.append(new_inc)
    return out


def count_by_severity(inconsistencias: list[dict]) -> dict[str, int]:
    """Conta {critical, major, minor} num laudo. Aceita inconsistências
    JÁ processadas por apply_severity_override (campo `severity` presente).
    """
    counts = {"critical": 0, "major": 0, "minor": 0}
    for inc in inconsistencias:
        s = inc.get("severity")
        if s in counts:
            counts[s] += 1
    return counts


def has_critical(inconsistencias: list[dict]) -> bool:
    """Headline metric T23: laudo tem alguma inconsistencia crítica?

    Aceita inconsistências JÁ processadas por apply_severity_override.
    """
    return any(inc.get("severity") == "critical" for inc in inconsistencias)
