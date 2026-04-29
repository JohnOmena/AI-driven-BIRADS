# MQM Review Protocol v1 — Revisão Humana de Traduções (T22)

> **Status:** STUB pré-T22. Contém apenas a instrução Tier 1 já decidida. Demais
> seções (estrutura da planilha, dimensões MQM, cegamento físico, termo de
> confidencialidade, etc.) serão escritas quando T22 for implementado.

## Tier 1 — Casos com `has_critical_error = True` no audit_deepseek

Os laudos selecionados como Tier 1 são aqueles em que o auditor automatizado
(DeepSeek V3) identificou erro crítico — predominantemente via **mechanical
override** sobre os critérios C2 (categoria BI-RADS), C3 (medidas/números),
C4 (lateralidade/localização) ou C6 (inversões/negação).

**Premissa:** o mechanical override é projetado para ser **conservador**
(anti-bias, sobre-flagar) — alguns flags são previsivelmente false positives
de equivalência semântica (ex.: "às custas de" ≡ "a expensas de"; "informe"
≈ "laudo" no contexto comparativo). Outros são erros clínicos genuínos
(ex.: adição de "acessório" muda anatomia).

### Instrução ao radiologista revisor (Tier 1)

> Para os laudos identificados como Tier 1 (potencial erro crítico), avaliar
> especificamente:
>
> 1. **A inconsistência apontada pelo auditor altera o diagnóstico clínico ou
>    a conduta?**
> 2. **Se altera:** registrar `has_critical_error_human = True`. Classificar a
>    severidade clínica conforme dimensão MQM (Accuracy/Mistranslation, etc.).
> 3. **Se NÃO altera** (sinônimo médico, variação léxica equivalente, idiotismo
>    consagrado em PT-br): registrar `has_critical_error_human = False` e
>    classificar como `minor` (ou abstain se irrelevante).
>
> Esta avaliação permite refutar de forma estruturada os false positives do
> mechanical override.

### Schema do output esperado (planilha MQM)

| Campo | Tipo | Notas |
|---|---|---|
| `report_id` | str | identificador do laudo |
| `tier` | int | 1 = potencial crítico; 2 = divergência estrutural; 3 = aleatório |
| `has_critical_error_human` | bool | True/False decisão do radiologista |
| `severity_human` | enum | `critical`/`major`/`minor`/`abstain` |
| `mqm_dimensions` | list[str] | dimensões MQM aplicáveis (Accuracy, Fluency, etc.) |
| `comments` | str | justificativa livre |

### Cross-validação

- `has_critical_error_human` × `has_critical_error` (DeepSeek) → matriz de
  confusão para reportar **sensibilidade e especificidade do auditor LLM**
- κ Cohen pareada com BCa bootstrap n=10000

---

**Demais seções a serem desenvolvidas em T22:**
- §2 Estrutura da planilha (Excel cegamento físico em 2 arquivos)
- §3 Dimensões MQM essenciais (6 selecionadas — Lommel et al. 2014)
- §4 Critérios de seleção da amostra (~50 laudos: Tier 1 + Tier 2 + Tier 3)
- §5 Termo de confidencialidade + LGPD
- §6 Pré-registro git (tag `mqm-protocol-pre-registered`)
- §7 Procedimento de inter-rater (κ entre revisor humano e LLM)
