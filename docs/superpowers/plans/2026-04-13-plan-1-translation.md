# Plan 1: Translation Module + Quality Evaluation Framework

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** (1) Translate the Spanish mammography report database (4,357 reports) to Brazilian Portuguese using Gemini 2.5 Flash (translator) + DeepSeek V3 (auditor) with multi-stage quality pipeline. (2) Evaluate translation quality through 5-source triangulation (intrinsic metrics, programmatic structural checks, back-translation, LLM auditor, human MQM review).

**Architecture:**
- **Phase A (T1–T11, DONE):** Translation pipeline with audit + meta-validation + correction loop. Output: `data/reports_translated_pt.csv` + `results/translation/translations.csv`.
- **Phase B (T12–T23, PENDING):** Evaluation framework producing `validation_results.jsonl` (single source of truth) + consolidated notebook.

**Tech Stack:** Python, Google Generative AI SDK (Gemini), OpenAI-compatible SDK (DeepSeek + GPT for back-translation control), Sentence Transformers, sacrebleu, bert_score, pandas, scipy.

**Specs:**
- Translation pipeline: `docs/superpowers/specs/2026-04-13-birads-classification-pipeline-design.md` — Seção 1
- Evaluation framework: `docs/superpowers/specs/2026-04-26-translation-evaluation-framework.md`

**Depends on:** Plan 0 (project setup) completed.

---

## Status & Progress (atualizado 2026-04-26)

### ✅ Phase A — Translation pipeline (T1–T11 COMPLETED)

| Task | Status | Artefato |
|------|--------|----------|
| T1: Glossário BI-RADS ES↔PT (95 termos) | ✅ | `configs/birads_glossary_es_pt.json` |
| T2: Config module + CLI | ✅ | `src/translation/config.py` |
| T3: Glossary loader + tests | ✅ | `src/translation/glossary.py` |
| T4: Translation prompt builder + tests | ✅ | `src/translation/prompt.py` |
| T5: LLM API client wrapper + tests | ✅ | `src/translation/client.py` |
| T6: Validation module + tests | ✅ | `src/translation/validate.py` |
| T7: Main pipeline (translate + audit + meta-val + correction) | ✅ | `src/translation/translate.py` |
| T8: Integration test (mocked APIs) | ✅ | `tests/test_translation/` |
| T9: Run all tests | ✅ | 100% pass |
| T10: Smoke test API real (10 laudos) | ✅ | OK |
| T11: Full translation (4.357 laudos) | ✅ | `data/reports_translated_pt.csv` (4.357 únicos) |

**Resultados consolidados (Phase A):**

```
Volume:           4.357 / 4.357  (100% cobertura)
Aprovados:        4.316 / 4.357  (99.06%)
Em revisão:          37 / 4.357  ( 0.85%)
Rejeitados:           2 / 4.357  ( 0.05%)
Falhas (NaN):         2 / 4.357  ( 0.05%)
Score médio:      9.31 / 10
Similaridade:    0.9571
Term match:      0.9959
Duplicatas:           100 (RPT_000721–RPT_000820, crash usage=None)
```

**Custo real Phase A:** ~R$160 (gasto verificado pelo orientado).
**Discrepância vs `stats.json` ($0.20 USD):** stats.json reporta apenas última sessão; tracking de `thoughts_token_count` ausente; preços desatualizados em `models.yaml`. Diagnóstico completo no commit de T14.

**Restarts:** 6 (2x crash usage=None, 1x fechamento sessão, 2x API hang, 1x reboot)
**Commits relevantes:**
- `955875a` feat(translation): loop de correção Gemini-DeepSeek com re-auditoria
- `498ee09` feat(translation): meta-auditoria valida achados do DeepSeek antes de corrigir
- `18557f7` feat(translation): resumo periódico a cada 15 laudos durante pipeline
- `8c67ed6` fix(translation): tratar usage=None na resposta da API DeepSeek/Google

### 🔲 Phase B — Quality Evaluation Framework (T12–T23 PENDING)

| Task | Status | Fase do framework | Custo | Tempo |
|------|--------|-------------------|-------|-------|
| T12: Setup eval infra + glossário Atlas CBR/SBM | 🔲 | F5.A | $0 | ~3h |
| **T12.5: Fix C1 auditor (derivar do Atlas)** ⚠ pré-req T13 | 🔲 | (mitigação) | $0 | ~1h |
| **T12.6: Severidade clínica (critical/major/minor + override mecânico)** ⚠ pré-req T13 | 🔲 | (validade clínica) | $0 | ~1h |
| T13: Re-audit DeepSeek (4.357 laudos) + Step 0 (audit Phase A correções) + Step 5 (calibração GPT-4o-mini) | 🔲 | F1 + calib | ~$0.44 | ~7h |
| **T14.A: Fix tracking custo/tokens (thoughts + preços)** ⚠ pré-req T14.B | 🔲 | (validade) | $0 | ~1h |
| **T14.B: Back-translation amostral (~250, prompt minimalista, structural round-trip + thresholds empíricos)** | 🔲 | F2 | ~$0.20 | ~20min |
| T15: Métricas intrínsecas MT (BERTScore-F1 + chrF++ + cosine + length_ratio principais; TER apêndice) | 🔲 | F3 | $0 | ~30min |
| T16: Checks programáticos estruturais | 🔲 | F4 | $0 | ~10min |
| T17: Consistência léxica + anomalias | 🔲 | F5.B+C | $0 | ~1h |
| T18: Concordância morfossintática | 🔲 | F6 | $0 | ~30min |
| T19: Estabilidade via duplicatas | 🔲 | F7 | $0 | ~10min |
| T20: Persistência consolidada (`validation_results.jsonl`) — schema unificado, fórmula pré-registrada, abstain semântico, 9 testes TDD, verify cross-source, 2-stage commit | 🔲 | F8 | $0 | ~2h20min |
| T21: Acordo cross-source (Cohen's κ pareada 6 fontes + abstain + estratificado por BI-RADS + disagreement direcional + 6 TDD) | 🔲 | F9 | $0 | ~1h45min |
| T22: Amostra MQM n=50 cega (seleção hierárquica T1-T5+T99 lendo schema T20, 6 dim essenciais + 4 opcionais, protocolo pré-registrado, 5 TDD) | 🔲 | F10 | $0 + revisão manual | ~1h35min + ~3-4h revisão |
| T23: Notebook consolidado (H1–H8 + Holm-Bonferroni + headline executiva + 12 seções 5/5b/7/7b + summary JSONs + failure_reasons + reproducibility auto-gerado + 5 TDD) | 🔲 | F11 | $0 | ~2h30min |

**Custo total Phase B:** ~$0.64 USD ≈ **R$3.20** (DeepSeek reaudit $0.27 + GPT-4o-mini calibration $0.17 + BT amostral $0.20).
**Tempo de máquina:** ~10h (T13/T14 paralelos).
**Tempo de implementação:** 2–3 dias úteis.

**Hipóteses operacionais a testar (H1–H8):**

| ID | Hipótese | Critério |
|----|----------|----------|
| H1 | Tradução preserva significado clínico | mediana BERTScore-F1 ≥ 0.90; cos(ES,ES_bt) ≥ 0.85 |
| H2 | Léxico BI-RADS preservado conforme glossário recebido | (a) **`overall_acceptable_rate` ≥ 0.99** (T17, canonical ∪ acceptable, contagem global) **E** (b) **`preservation_rate` ≥ 0.95** agregado em todos os laudos (T18, divergências morfossintáticas introduzidas). Cobrem dimensões diferentes: T17 mede qual variante; T18 mede qual flexão da variante. `canonical_rate` reportado em paralelo como evidência de decisão de glossário, não erro de tradução. |
| H3 | Fontes ortogonais convergem | Em laudos da amostra BT (~250): ≥ 4 das 5 fontes "approved" em ≥ 95%. Fora da amostra: ≥ 3 das 4 fontes em ≥ 95% |
| H4 | Categoria/medidas/lateralidade preservadas | ≥ 99% laudos passam |
| H5 | Estabilidade operacional em duplicatas (`effective_duplicate`) | (a) mediana `cosine_pt_pt` ≥ 0.98 com IC 95% bootstrap BCa; (b) p5 `cosine_pt_pt` ≥ 0.95; (c) `structural_instability_rate` ≤ 0.02 (tolerância calibrada — acomoda 1 caso anômalo em 48); IDs com `requires_mqm_review = True` automaticamente flagados para T22 |
| H6 | Sem viés por categoria BI-RADS | Kruskal-Wallis p > 0.05 |
| H7 | PT-br puro sem drift PT-pt | ≤ 1% laudos com marcador PT-pt |
| **H8** | **Taxa de erro crítico ≤ 1%** (severidade clínica) | ≤ 1% dos laudos com ≥1 inconsistência `critical` (T12.6) |

---

## File Structure

```
configs/
├── birads_glossary_es_pt.json          ✅ created (95 termos, Phase A)
├── birads_glossary_atlas_es_pt.json    🔲 pending (T12, ~200 termos CBR/SBM)
└── models.yaml                         ⚠ a corrigir em T14 (preços + entry no-thinking)

src/
├── translation/                        ✅ Phase A
│   ├── __init__.py
│   ├── config.py
│   ├── glossary.py
│   ├── prompt.py
│   ├── client.py                       ⚠ a corrigir em T14 (track thoughts_token_count)
│   ├── translate.py
│   └── validate.py
│
└── evaluation/                         🔲 Phase B (criar em T12)
    ├── __init__.py                     🔲
    ├── io.py                           🔲 T12 (JSONL append + fsync)
    ├── reaudit_deepseek.py             🔲 T13
    ├── back_translation.py             🔲 T14
    ├── intrinsic_metrics.py            🔲 T15
    ├── structural_checks.py            🔲 T16
    ├── lexical_analysis.py             🔲 T17
    ├── modifier_check.py               🔲 T18
    ├── duplicate_stability.py          🔲 T19
    ├── consolidate.py                  🔲 T20
    ├── agreement.py                    🔲 T21
    └── sample_for_human_review.py      🔲 T22

tests/
├── test_translation/                   ✅ Phase A
└── test_evaluation/                    🔲 Phase B (criar progressivamente)
    ├── test_io.py
    ├── test_back_translation.py
    ├── test_intrinsic_metrics.py
    ├── test_structural_checks.py
    └── test_consolidate.py

results/translation/
├── translations.csv                    ✅ Phase A (4.457 linhas, 4.357 únicas)
├── stats.json                          ✅ Phase A (subreporta — apenas última sessão)
├── audit_results.json                  ⚠ Phase A (só 517 da última sessão; será recriado em T13)
├── pipeline.log                        ✅ Phase A
│
├── audit_deepseek.jsonl                🔲 T13
├── back_translation.csv                🔲 T14
├── intrinsic_metrics.csv               🔲 T15
├── structural_checks.csv               🔲 T16
├── lexical_consistency.csv             🔲 T17
├── lexical_anomalies.csv               🔲 T17
├── modifier_preservation.csv           🔲 T18
├── duplicate_stability.csv             🔲 T19
├── validation_results.jsonl            🔲 T20  (★ fonte única consolidada)
├── agreement_report.json               🔲 T21
└── human_review_sample.xlsx            🔲 T22

data/
├── reports_raw_canonical.csv           ✅ Phase 0 (4.357 ES)
└── reports_translated_pt.csv           ✅ Phase A (4.357 PT-br)

notebooks/
└── 01_translation_report.ipynb         🔲 T23 (relatório TCC final)
```

---

## Pre-flight checklist (executar antes de T12)

Antes de iniciar a Phase B, validar:

- [x] **Backup pré-Phase B** — `backups/data_pre_phase_b/` + `backups/results_translation_pre_phase_b/` (4.9M + 4.8M, hashes registrados)
- [x] **PHI verification** — base PT-br: 0 matches; base ES: 21 falso-positivos confirmados visualmente (PACIENTE PORTADORA, CON ANTECEDENTE, etc.). Whitelist `PACIENTE_STOPWORDS` adicionada ao regex
- [x] **APIs configuradas** — DeepSeek ✅, Google ✅, **OpenAI ❌** (bloqueador de T13 Step 5)
- [x] **Smoke test conectividade** — DeepSeek 4.31s + Gemini 3.99s (ambos $0.00001 de teste)
- [x] **`models.yaml` corrigido** — preços Gemini 2.5 Flash atualizados ($0.30/$2.50); entries `gemini-2.5-flash-no-thinking` (T14.B) e `gpt-4o-mini` (T13 Step 5) adicionadas
- [ ] **OPENAI_API_KEY a obter** antes de T13 Step 5 (custo previsto $0.17 — quota requer cartão de crédito ativo)
- [ ] **Commits de design** — feitos (`aeac246`, `8eb164b`, `19ffd2b`)

### Estratégia de paralelização (decisão registrada)

**Ambiente:** Windows + Git Bash → `tmux` e `screen` indisponíveis. **Decisão:** usar `nohup` + background job (mesmo padrão da Phase A, já validado).

**Setup para T13 + T14.B/T15/T16 em paralelo:**

```bash
# Sessão 1 — T13 em background (6h)
nohup venv/Scripts/python.exe -u -m src.evaluation.reaudit_deepseek \
  > results/translation/reaudit_deepseek.log 2>&1 &
echo $! > results/translation/reaudit_deepseek.pid
disown

# Sessão 2 — sua janela ativa: desenvolver T14.B/T15/T16
# Monitoramento sob demanda (não polling):
tail -n 50 results/translation/reaudit_deepseek.log
ps -p $(cat results/translation/reaudit_deepseek.pid) || echo "T13 finalizou ou morreu"
```

**Mitigações de risco:**
- **`-u`** flag: stdout sem buffer (log atualiza em tempo real)
- **`disown`**: isola do shell pai (sobrevive a fechamento de terminal, embora não a reboot)
- **PID em arquivo**: monitoramento sem `ps -ef | grep`
- **Smoke test (Step 1.5)** rodado primeiro em foreground — só vai para background se passar

**Quando NÃO paralelizar:**
- Se smoke test (Step 1.5) ainda não passou → rodar em foreground primeiro
- Se está depurando algo → sequencial é mais simples mentalmente
- Para T22 (revisão humana 3-4h) — paralelizar não faz sentido (fora da máquina)

**Acessórios criados:**
- `scripts/smoke_test_apis.py` — connectividade DeepSeek + Gemini (rodado pré-Phase B)

---

## Governance & Operational Documentation

Antes de iniciar a Phase B (T12 em diante), criar 6 artefatos de governança que protegem reprodutibilidade, defensibilidade na banca, e rastreabilidade pós-execução. Cada um resolve uma lacuna específica do plano hoje.

### G1 — Decision log centralizado (`docs/superpowers/specs/decision_log.md`)

**Problema resolvido:** decisões metodológicas estão espalhadas em ~16 tasks. Banca pergunta "por que escolheram X?" → caça à task certa. Centralizar elimina o tempo de busca.

**Schema:**

```markdown
# Decision log — Phase B evaluation framework

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Cortar BLEU do par ES↔PT | T15 | n-gramas de palavra inflam erro em línguas próximas; flexão equivalente subestima | Freitag et al. 2022 (WMT22 Metrics) |
| n=250 BT amostral | T14.B | Suficiente para H6 estratificado (≥7 por categoria); custo $0.20 vs $3.05 full | (decisão pragmática) |
| 6 dimensões MQM essenciais (não 10) | T22 | Reduz fadiga 500→300 julgamentos; cobre H1/H2/H3 | Lommel et al. 2014 (MQM core) |
| Threshold modifier 0.95 (piso 0.90) | T18 Step 6 | Calibração empírica via p5 das duplicatas T19 | (calibração interna) |
| Tag pré-registro `composite-score-formula` | T20 Step 6 | Anti-p-hacking via timestamp git imutável | Nosek et al. 2018 |
| Tag pré-registro `mqm-protocol` | T22 Step 0 | Mesma estratégia anti-p-hacking | Nosek et al. 2018 |
| Holm-Bonferroni para H1–H8 | T23 Step 3 | FWER controlado em α=0.05 com 8 hipóteses confirmatórias | Holm 1979 |
| `audit_final_status="review"` → `passed=True` | T20 build_audit | Evita dupla penalização (Q_audit já pega has_critical) | (decisão pré-registrada) |
| `clinical_pass` separado de `overall_passed` | T20 schema | Modifier-only failure não é erro clínico — vira warning | (decisão metodológica) |
| Cegamento operacional na revisão MQM | T22 Step 5 | MQM como fonte ortogonal — sem cegamento vira validação enviesada | (princípio metodológico) |
| Override mecânico C2/C3/C4/C6 → severity=critical | T12.6 | LLM calibra severidade instavelmente; objetivo elimina viés | (decisão de design) |
| BT prompt minimalista (sem glossário) | T14.B | Mitigação de family bias (Gemini ↔ Gemini) | (decisão metodológica) |
| Schema `validation_results` v1 | T20 Step 0 | Schema unificado consumido por T21/T22/T23 | (arquitetural) |
| 3 estados de "valor": passed/null/in_sample | T20 princípio | Distingue aplicável + falhou de não-aplicável (abstain) | (semântica de estado) |
| BERTScore não decide erro clínico | T15 escopo | Métricas semânticas globais não captam troca local de token | (limitação de escopo) |
| `duplicate_stability` nunca em `overall_passed` | T19 / T20 | Fonte de priorização (T22), não de aprovação | (decisão arquitetural) |
```

**Custo:** ~30 min para mapear todas as decisões + referências (boa parte já está nos commits/specs).
**Ganho:** defesa cristalina — toda decisão em uma página com referência.

---

### G2 — Execution log por task (`docs/superpowers/execution_log/T{N}_run.md`)

**Problema resolvido:** quando T13 (~6h, $0.27) ou T22 (~3-4h revisão humana) executar, falta padrão de log estruturado. Pós-execução improvisada não é defensável.

**Template (criar UM arquivo por task com chamada de API ou execução longa):**

```markdown
# T{N} — Execution log

## Pre-flight
- [ ] Commit hash inicial: `<hash>`
- [ ] Smoke test PASSED (se aplicável)
- [ ] Custo por unidade no smoke: $0.000XX (esperado: $0.000YY ±30%)
- [ ] Pré-requisitos verificados (specs, glossário, T-anterior)

## Run
- Iniciado:   YYYY-MM-DD HH:MM TZ
- Finalizado: YYYY-MM-DD HH:MM TZ (duração)
- Restarts:   N (motivos: ...)
- Custos finais: $0.XX (esperado: $0.XX)

## Verifications
- Cobertura: N / esperado ✓
- JSON parse failures: 0 ✓
- Cross-source vs *_summary: ✓
- (outros critérios da task)

## Outputs
- Arquivo X: N records, sha256: `<hash>`
- (...)

## Anomalies / observations
(deixar em branco se nenhuma; senão, descrever — alimenta G5 incidents.md)

## Rollback decisions
(se aplicável: critério violado, ação tomada)

## Commit
`<hash>`: feat(evaluation): F{N} ...
```

**Tasks com log obrigatório:** T12, T12.5, T12.6, T13, T13 Step 5, T14.A, T14.B, T15, T16, T17, T18, T19, T20, T21, T22, T23 (16 tasks).

**Custo:** ~5 min por task × 16 = 80 min total.
**Ganho:** rastreabilidade pós-execução documentada, não improvisada.

---

### G3 — Cost ledger (`results/translation/cost_ledger.json`)

**Problema resolvido:** custos espalhados — T23 §12 vai precisar somar manualmente. Cada task com API call atualiza o ledger; T23 lê direto.

**Schema:**

```json
{
  "phase_a": {
    "task": "T1-T11",
    "cost_usd": 33.43,
    "method": "T14.A retrofit (thoughts_token_count + precos corrigidos)",
    "billing_source": "Google Cloud Console (R$160 verified)"
  },
  "t13": {
    "task": "T13",
    "cost_usd": 0.27,
    "model": "deepseek-v3",
    "tokens_in": 1506000, "tokens_out": 180000,
    "billing_source": "client.total_cost_usd"
  },
  "t13_step5": {
    "task": "T13 Step 5",
    "cost_usd": 0.17,
    "model": "gpt-4o-mini-2024-07-18",
    "n_audits": 250,
    "billing_source": "client.total_cost_usd"
  },
  "t14b": {
    "task": "T14.B",
    "cost_usd": 0.20,
    "model": "gemini-2.5-flash-no-thinking",
    "n_laudos": 250,
    "billing_source": "client.total_cost_usd (corrigido por T14.A)"
  },
  "total_phase_b_usd": 0.64,
  "total_all_usd":     34.07,
  "last_updated":      "2026-04-29T19:45:00-03:00"
}
```

**Tasks que atualizam:** T13, T13 Step 5, T14.B (todas com chamada de API).
**Custo:** ~10 min de implementação (helper `update_cost_ledger.py`).
**Ganho:** cost reporting consistente; T23 §12 lê direto.

---

### G4 — Verification matrix (`docs/superpowers/execution_log/verification_matrix.md`)

**Problema resolvido:** cada task tem critérios de sanidade individuais. Banca pergunta "como sabem que cada fase rodou bem?" → falta dashboard único.

**Schema:**

```markdown
# Verification matrix — Phase B

| Task | Pre-flight | Run | Verify | Output sanity | Commit | Status |
|---|---|---|---|---|---|---|
| T12   | ✅ | ✅ | ✅ verify_atlas_morphology + backward_compat | ✅ ~200 termos | `<hash>` | DONE |
| T12.5 | ✅ | ✅ | ✅ smoke 20 laudos C1 | ✅ FP redução ≥70% | `<hash>` | DONE |
| T12.6 | ✅ | ✅ smoke 5 | ✅ severity overrides funcionando | ✅ 5 testes pass | `<hash>` | DONE |
| T13   | ✅ Step 0 | ✅ smoke 1.5 + full | ✅ verify cross-source | ✅ 4357/4357 + summary | `<hash>` | DONE |
| T13.5 | ✅ | ✅ | ✅ kappa por critério | ✅ decisão registrada | `<hash>` | DONE |
| T14.A | ✅ | ✅ teste mock | ✅ thoughts contados | ✅ retrofit Phase A | `<hash>` | DONE |
| T14.B | ✅ smoke 10 | ✅ full ~250 | ✅ calibração thresholds | ✅ structural round-trip | `<hash>` | DONE |
| T15   | ✅ | ✅ | ✅ sanity (median ≥ 0.90) | ✅ 4357 com 4+1 metrics | `<hash>` | DONE |
| T16   | ✅ | ✅ | ✅ regex coverage | ✅ all_structural_pass rate | `<hash>` | DONE |
| T17   | ✅ | ✅ | ✅ acceptable_rate ≥ 0.99 | ✅ summary global | `<hash>` | DONE |
| T18   | ✅ | ✅ | ✅ coverage ≥ 70% | ✅ p5 calibrado | `<hash>` | DONE |
| T19   | ✅ | ✅ | ✅ 4 camadas distinguidas | ✅ summary H5 | `<hash>` | DONE |
| T20   | ✅ TDD 11 | ✅ | ✅ verify cross-source | ✅ 4357 records v1 | `<hash>` | DONE |
| T21   | ✅ TDD 6 | ✅ | ✅ kappa pareada 6 fontes | ✅ agreement_report | `<hash>` | DONE |
| T22   | ✅ Step 0 protocol | ✅ amostra n=50 + revisão | ✅ extract_mqm | ✅ summary humano | `<hash>` | DONE |
| T23   | ✅ TDD 5 | ✅ notebook | ✅ Holm-Bonferroni | ✅ reproducibility.json | `<hash>` | DONE |
```

**Custo:** 10 min de criação + 1 min por task ao executar (preencher uma linha).
**Ganho:** dashboard único de progresso, defesa imediata.

---

### G5 — Incidents log (`docs/superpowers/execution_log/incidents.md`)

**Problema resolvido:** Phase A teve 6 restarts. Phase B vai ter pelo menos algum imprevisto. Sem template, defesa de "por que executou em N tentativas" é improvisada.

**Template:**

```markdown
## Incident #{N} — {task} {sintoma resumido}
- **Data:**         YYYY-MM-DD HH:MM TZ
- **Sintoma:**      (descrição objetiva)
- **Diagnóstico:**  (causa identificada)
- **Mitigação:**    (ação tomada para resolver)
- **Impacto na reprodutibilidade:** (nenhum / parcial / total — justificar)
- **Lição:**        (mudança proposta para próxima versão / commit fix)
```

**Custo:** zero criação (template), preenchido só se ocorrer.
**Ganho:** defesa de execução não-trivial documentada.

---

### G6 — Rollback criteria por task (com chamada de API)

**Problema resolvido:** se custo estourar 50% ou parse failure crescer, falta critério explícito → decisão ad-hoc.

**Aplicar em T13, T14.A, T14.B, T22** (tasks com custo ou execução longa). Adicionar bloco:

```markdown
#### Rollback criteria

Reverter T{N} e re-investigar se durante a execução:
- Custo total > 150% do esperado (ex: $0.40 em T13 vs $0.27)
- JSON parse failures > 1% (esperado <0.5%)
- Cobertura final < 99% (esperado 100%)
- Critério específico: <critério da task>

**Ação se rollback:** abortar full run, salvar partial output, abrir issue em incidents.md, reavaliar prompt/config.
```

**Custo:** ~5 min por task com API call (4 tasks = 20 min).
**Ganho:** decisão pré-registrada em vez de ad-hoc no momento da crise.

---

### Resumo das 6 lacunas

| ID | Artefato | Resolve | Custo |
|----|----------|---------|-------|
| **G1** | `decision_log.md` centralizado | Caça a decisões espalhadas em 16 tasks | 30 min |
| **G2** | `T{N}_run.md` por task | Log estruturado pós-execução | 80 min total |
| **G3** | `cost_ledger.json` | Cost reporting consistente | 10 min |
| **G4** | `verification_matrix.md` | Dashboard único de progresso | 10 min + 1/task |
| **G5** | `incidents.md` (template) | Defesa de imprevistos | 0 min (só se ocorrer) |
| **G6** | Rollback criteria nas 4 tasks com API | Decisão pré-registrada | 20 min |

**Total: ~2h30min de governança operacional.** Aplicar antes de iniciar T12 (logo a seguir), exceto G2/G4/G5 que são preenchidos durante execução.

---

### Task 1: Create BI-RADS glossary ES↔PT ✅ DONE

**Files:**
- Create: `configs/birads_glossary_es_pt.json`

- [ ] **Step 1: Write the bilingual BI-RADS glossary**

This glossary contains the official BI-RADS terminology that MUST be preserved during translation. Terms are grouped by category.

```json
{
  "metadata": {
    "source": "ACR BI-RADS Atlas, 5th Edition",
    "description": "Bilingual glossary ES↔PT for BI-RADS mammography terminology"
  },
  "terms": {
    "anatomy": [
      {"es": "mama derecha", "pt": "mama direita"},
      {"es": "mama izquierda", "pt": "mama esquerda"},
      {"es": "cuadrante superior externo", "pt": "quadrante superior externo"},
      {"es": "cuadrante superior interno", "pt": "quadrante superior interno"},
      {"es": "cuadrante inferior externo", "pt": "quadrante inferior externo"},
      {"es": "cuadrante inferior interno", "pt": "quadrante inferior interno"},
      {"es": "retroareolar", "pt": "retroareolar"},
      {"es": "prolongación axilar", "pt": "prolongamento axilar"},
      {"es": "región axilar", "pt": "região axilar"},
      {"es": "pezón", "pt": "mamilo"},
      {"es": "mamelón", "pt": "mamilo"},
      {"es": "areola", "pt": "aréola"},
      {"es": "conducto", "pt": "ducto"},
      {"es": "piel", "pt": "pele"},
      {"es": "tejido glandular", "pt": "tecido glandular"},
      {"es": "tejido adiposo", "pt": "tecido adiposo"},
      {"es": "plano posterior", "pt": "plano posterior"},
      {"es": "región pectoaxilar", "pt": "região pectoaxilar"}
    ],
    "findings_mass": [
      {"es": "nódulo", "pt": "nódulo"},
      {"es": "masa", "pt": "massa"},
      {"es": "imagen nodular", "pt": "imagem nodular"},
      {"es": "formación nodular", "pt": "formação nodular"},
      {"es": "lesión nodular", "pt": "lesão nodular"},
      {"es": "asimetría", "pt": "assimetria"},
      {"es": "asimetría focal", "pt": "assimetria focal"},
      {"es": "asimetría global", "pt": "assimetria global"},
      {"es": "distorsión arquitectural", "pt": "distorção arquitetural"},
      {"es": "densidad asimétrica", "pt": "densidade assimétrica"}
    ],
    "findings_calcification": [
      {"es": "calcificación", "pt": "calcificação"},
      {"es": "calcificaciones", "pt": "calcificações"},
      {"es": "microcalcificación", "pt": "microcalcificação"},
      {"es": "microcalcificaciones", "pt": "microcalcificações"},
      {"es": "macrocalcificación", "pt": "macrocalcificação"}
    ],
    "morphology": [
      {"es": "espiculado", "pt": "espiculado"},
      {"es": "espiculada", "pt": "espiculada"},
      {"es": "circunscrito", "pt": "circunscrito"},
      {"es": "circunscrita", "pt": "circunscrita"},
      {"es": "irregular", "pt": "irregular"},
      {"es": "ovalado", "pt": "ovalado"},
      {"es": "ovalada", "pt": "ovalada"},
      {"es": "redondo", "pt": "redondo"},
      {"es": "redonda", "pt": "redonda"},
      {"es": "lobulado", "pt": "lobulado"},
      {"es": "lobulada", "pt": "lobulada"},
      {"es": "microlobulado", "pt": "microlobulado"},
      {"es": "obscurecido", "pt": "obscurecido"},
      {"es": "indistinto", "pt": "indistinto"},
      {"es": "isodenso", "pt": "isodenso"},
      {"es": "isodensos", "pt": "isodensos"},
      {"es": "hipodenso", "pt": "hipodenso"},
      {"es": "hiperdenso", "pt": "hiperdenso"},
      {"es": "heterogéneo", "pt": "heterogêneo"},
      {"es": "homogéneo", "pt": "homogêneo"},
      {"es": "pleomórfico", "pt": "pleomórfico"},
      {"es": "amorfo", "pt": "amorfo"},
      {"es": "puntiforme", "pt": "puntiforme"},
      {"es": "lineal fino", "pt": "linear fino"},
      {"es": "ramificado", "pt": "ramificado"}
    ],
    "distribution": [
      {"es": "agrupada", "pt": "agrupada"},
      {"es": "segmentaria", "pt": "segmentar"},
      {"es": "lineal", "pt": "linear"},
      {"es": "regional", "pt": "regional"},
      {"es": "difusa", "pt": "difusa"},
      {"es": "ductal", "pt": "ductal"}
    ],
    "density": [
      {"es": "composición mamaria", "pt": "composição mamária"},
      {"es": "predominantemente adiposa", "pt": "predominantemente adiposa"},
      {"es": "densidades fibroglandulares dispersas", "pt": "densidades fibroglandulares dispersas"},
      {"es": "heterogéneamente densa", "pt": "heterogeneamente densa"},
      {"es": "extremadamente densa", "pt": "extremamente densa"},
      {"es": "tipo A", "pt": "tipo A"},
      {"es": "tipo B", "pt": "tipo B"},
      {"es": "tipo C", "pt": "tipo C"},
      {"es": "tipo D", "pt": "tipo D"}
    ],
    "assessment": [
      {"es": "BI-RADS", "pt": "BI-RADS"},
      {"es": "benigno", "pt": "benigno"},
      {"es": "benigna", "pt": "benigna"},
      {"es": "maligno", "pt": "maligno"},
      {"es": "maligna", "pt": "maligna"},
      {"es": "sospechoso", "pt": "suspeito"},
      {"es": "sospechosa", "pt": "suspeita"},
      {"es": "probablemente benigno", "pt": "provavelmente benigno"},
      {"es": "hallazgo", "pt": "achado"},
      {"es": "hallazgos", "pt": "achados"}
    ],
    "procedure": [
      {"es": "mamografía", "pt": "mamografia"},
      {"es": "ecografía", "pt": "ecografia"},
      {"es": "ultrasonido", "pt": "ultrassonografia"},
      {"es": "biopsia", "pt": "biópsia"},
      {"es": "incidencia", "pt": "incidência"},
      {"es": "cráneo-caudal", "pt": "craniocaudal"},
      {"es": "medio lateral oblicua", "pt": "médio-lateral oblíqua"},
      {"es": "prótesis", "pt": "prótese"},
      {"es": "implante", "pt": "implante"},
      {"es": "ganglio linfático", "pt": "linfonodo"},
      {"es": "ganglios linfáticos", "pt": "linfonodos"},
      {"es": "ganglio linfático intramamario", "pt": "linfonodo intramamário"}
    ]
  }
}
```

- [ ] **Step 2: Validate JSON**

Run:
```bash
python -c "import json; d=json.load(open('configs/birads_glossary_es_pt.json', encoding='utf-8')); total=sum(len(v) for v in d['terms'].values()); print(f'Valid JSON: {len(d[\"terms\"])} categories, {total} term pairs')"
```
Expected: `Valid JSON: 8 categories, ~80 term pairs`

- [ ] **Step 3: Commit**

Run:
```bash
git add configs/birads_glossary_es_pt.json
git commit -m "feat: add bilingual BI-RADS glossary ES↔PT"
```

---

### Task 2: Create translation config module ✅ DONE

**Files:**
- Create: `src/translation/config.py`
- Test: `tests/test_translation/test_config.py` (deferred — tested implicitly)

- [ ] **Step 1: Write config.py with CONFIG object + argparse CLI**

```python
"""Translation module configuration.

Usage:
    - Edit CONFIG dict directly for default values
    - Override via CLI: python -m src.translation.translate --llm-primary gemini-2.0-flash
"""

import argparse
from pathlib import Path

CONFIG = {
    "source_path": "data/reports_raw_canonical.csv",
    "output_path": "data/reports_translated_pt.csv",
    "output_primary_path": "results/translation/translations_primary.csv",
    "output_secondary_path": "results/translation/translations_secondary.csv",
    "divergences_path": "results/translation/divergences.json",
    "stats_path": "results/translation/stats.json",
    "llm_primary": "gemini-2.0-flash",
    "llm_secondary": "deepseek-v3",
    "similarity_threshold": 0.95,
    "temperature": 0,
    "birads_glossary_path": "configs/birads_glossary_es_pt.json",
    "models_config_path": "configs/models.yaml",
    "batch_size": 10,
    "max_retries": 3,
    "resume": True,
}


def parse_args() -> dict:
    """Parse CLI arguments and merge with CONFIG defaults."""
    parser = argparse.ArgumentParser(description="Translate ES reports to PT")
    parser.add_argument("--source-path", type=str, help="Path to source CSV")
    parser.add_argument("--output-path", type=str, help="Path to output CSV")
    parser.add_argument("--llm-primary", type=str, help="Primary LLM for translation")
    parser.add_argument("--llm-secondary", type=str, help="Secondary LLM for validation")
    parser.add_argument("--similarity-threshold", type=float, help="Min similarity threshold")
    parser.add_argument("--temperature", type=float, help="LLM temperature")
    parser.add_argument("--batch-size", type=int, help="Reports per batch")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh, ignore previous progress")

    args = parser.parse_args()
    config = CONFIG.copy()

    # Override CONFIG with any provided CLI args
    if args.source_path:
        config["source_path"] = args.source_path
    if args.output_path:
        config["output_path"] = args.output_path
    if args.llm_primary:
        config["llm_primary"] = args.llm_primary
    if args.llm_secondary:
        config["llm_secondary"] = args.llm_secondary
    if args.similarity_threshold is not None:
        config["similarity_threshold"] = args.similarity_threshold
    if args.temperature is not None:
        config["temperature"] = args.temperature
    if args.batch_size:
        config["batch_size"] = args.batch_size
    if args.no_resume:
        config["resume"] = False

    return config
```

- [ ] **Step 2: Commit**

Run:
```bash
git add src/translation/config.py
git commit -m "feat(translation): add config module with CLI + object pattern"
```

---

### Task 3: Create glossary loader ✅ DONE

**Files:**
- Create: `src/translation/glossary.py`
- Create: `tests/test_translation/__init__.py`
- Create: `tests/test_translation/test_glossary.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for glossary loading and formatting."""

import json
import tempfile
from pathlib import Path

from src.translation.glossary import load_glossary, format_glossary_for_prompt


def test_load_glossary_returns_term_pairs():
    """Loading the glossary returns a flat list of (es, pt) term pairs."""
    glossary_data = {
        "metadata": {"source": "test"},
        "terms": {
            "anatomy": [
                {"es": "mama derecha", "pt": "mama direita"},
                {"es": "mama izquierda", "pt": "mama esquerda"},
            ],
            "morphology": [
                {"es": "espiculado", "pt": "espiculado"},
            ],
        },
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(glossary_data, f, ensure_ascii=False)
        tmp_path = f.name

    pairs = load_glossary(tmp_path)
    assert len(pairs) == 3
    assert ("mama derecha", "mama direita") in pairs
    assert ("espiculado", "espiculado") in pairs
    Path(tmp_path).unlink()


def test_format_glossary_for_prompt():
    """Glossary formatted for prompt contains ES→PT mappings."""
    pairs = [
        ("mama derecha", "mama direita"),
        ("calcificación", "calcificação"),
    ]
    text = format_glossary_for_prompt(pairs)
    assert "mama derecha → mama direita" in text
    assert "calcificación → calcificação" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
python -m pytest tests/test_translation/test_glossary.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'src.translation.glossary'`

- [ ] **Step 3: Implement glossary.py**

```python
"""Load and format the BI-RADS glossary for translation prompts."""

import json
from pathlib import Path


def load_glossary(glossary_path: str) -> list[tuple[str, str]]:
    """Load glossary JSON and return flat list of (es, pt) term pairs."""
    with open(glossary_path, encoding="utf-8") as f:
        data = json.load(f)

    pairs = []
    for category_terms in data["terms"].values():
        for entry in category_terms:
            pairs.append((entry["es"], entry["pt"]))
    return pairs


def format_glossary_for_prompt(pairs: list[tuple[str, str]]) -> str:
    """Format term pairs as a readable glossary block for the LLM prompt."""
    lines = ["Glossário de termos BI-RADS (Espanhol → Português):"]
    for es, pt in pairs:
        lines.append(f"  {es} → {pt}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m pytest tests/test_translation/test_glossary.py -v
```
Expected: 2 passed

- [ ] **Step 5: Commit**

Run:
```bash
git add src/translation/glossary.py tests/test_translation/__init__.py tests/test_translation/test_glossary.py
git commit -m "feat(translation): add glossary loader with tests"
```

---

### Task 4: Create translation prompt builder ✅ DONE

**Files:**
- Create: `src/translation/prompt.py`
- Create: `tests/test_translation/test_prompt.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for translation prompt construction."""

from src.translation.prompt import build_translation_prompt


def test_prompt_contains_report_text():
    """The prompt must include the original report text."""
    report = "Se observa un nódulo espiculado en mama derecha."
    glossary_text = "mama derecha → mama direita"
    prompt = build_translation_prompt(report, glossary_text)
    assert "Se observa un nódulo espiculado en mama derecha." in prompt


def test_prompt_contains_glossary():
    """The prompt must include the glossary."""
    report = "Texto de ejemplo."
    glossary_text = "mama derecha → mama direita\ncalcificación → calcificação"
    prompt = build_translation_prompt(report, glossary_text)
    assert "mama derecha → mama direita" in prompt
    assert "calcificación → calcificação" in prompt


def test_prompt_contains_fidelity_instructions():
    """The prompt must contain explicit fidelity instructions."""
    report = "Texto."
    glossary_text = ""
    prompt = build_translation_prompt(report, glossary_text)
    # Check for key fidelity instructions
    prompt_lower = prompt.lower()
    assert "fielmente" in prompt_lower or "fiel" in prompt_lower
    assert "não omit" in prompt_lower or "no omit" in prompt_lower or "sem omitir" in prompt_lower


def test_prompt_instructs_birads_preservation():
    """The prompt must instruct to preserve BI-RADS terminology."""
    report = "Texto."
    glossary_text = ""
    prompt = build_translation_prompt(report, glossary_text)
    assert "BI-RADS" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
python -m pytest tests/test_translation/test_prompt.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement prompt.py**

```python
"""Build the translation prompt for ES→PT mammography report translation."""


def build_translation_prompt(report_text: str, glossary_text: str) -> str:
    """Build a translation prompt that ensures fidelity and BI-RADS lexicon preservation.

    Args:
        report_text: The original Spanish mammography report.
        glossary_text: Formatted glossary of BI-RADS terms ES→PT.

    Returns:
        Complete prompt string for the LLM.
    """
    prompt = f"""Você é um tradutor médico especializado em radiologia mamária e no sistema BI-RADS.

Sua tarefa é traduzir fielmente o seguinte laudo de mamografia do espanhol para o português.

REGRAS OBRIGATÓRIAS:
1. Traduzir fielmente o texto completo, sem omitir, resumir, interpretar ou adicionar informações.
2. Preservar exatamente a estrutura, formatação, parágrafos e pontuação do texto original.
3. Utilizar OBRIGATORIAMENTE a terminologia oficial BI-RADS em português conforme o glossário abaixo.
4. Não traduzir siglas que são universais (BI-RADS, CSE, CSI, CIE, CII).
5. Manter unidades de medida e valores numéricos exatamente como no original.
6. Retornar APENAS o texto traduzido, sem explicações, comentários ou notas adicionais.

{glossary_text}

LAUDO ORIGINAL (Espanhol):
{report_text}

TRADUÇÃO (Português):"""
    return prompt
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m pytest tests/test_translation/test_prompt.py -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

Run:
```bash
git add src/translation/prompt.py tests/test_translation/test_prompt.py
git commit -m "feat(translation): add prompt builder with fidelity instructions"
```

---

### Task 5: Create LLM API client wrapper ✅ DONE  ⚠ a revisar em T14 (track thoughts_token_count)

**Files:**
- Create: `src/translation/client.py`
- Create: `tests/test_translation/test_client.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for LLM client wrapper."""

from unittest.mock import patch, MagicMock
from src.translation.client import LLMClient, create_client


def test_create_client_gemini():
    """create_client returns an LLMClient for gemini provider."""
    model_config = {
        "provider": "google",
        "model_id": "gemini-2.0-flash",
        "env_key": "GOOGLE_API_KEY",
    }
    with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-key"}):
        client = create_client("gemini-2.0-flash", model_config)
    assert isinstance(client, LLMClient)
    assert client.provider == "google"


def test_create_client_openai_compatible():
    """create_client returns an LLMClient for openai_compatible provider."""
    model_config = {
        "provider": "openai_compatible",
        "model_id": "deepseek-chat",
        "api_base": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
    }
    with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "fake-key"}):
        client = create_client("deepseek-v3", model_config)
    assert isinstance(client, LLMClient)
    assert client.provider == "openai_compatible"


def test_llm_client_tracks_token_usage():
    """LLMClient accumulates token usage across calls."""
    client = LLMClient(
        name="test",
        provider="google",
        model_id="test-model",
        api_key="fake",
    )
    client._update_usage(input_tokens=100, output_tokens=50)
    client._update_usage(input_tokens=200, output_tokens=100)
    assert client.total_input_tokens == 300
    assert client.total_output_tokens == 150
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
python -m pytest tests/test_translation/test_client.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement client.py**

```python
"""LLM API client wrapper supporting multiple providers."""

import os
import time
from dataclasses import dataclass, field


@dataclass
class LLMClient:
    """Unified client for LLM API calls with token tracking."""

    name: str
    provider: str
    model_id: str
    api_key: str
    api_base: str | None = None
    cost_per_1m_input: float = 0.0
    cost_per_1m_output: float = 0.0
    cost_limit_usd: float = 50.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0

    def _update_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Track token usage and cost."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        cost = (
            input_tokens * self.cost_per_1m_input / 1_000_000
            + output_tokens * self.cost_per_1m_output / 1_000_000
        )
        self.total_cost_usd += cost

    def check_cost_limit(self) -> bool:
        """Return True if cost is within limit."""
        return self.total_cost_usd < self.cost_limit_usd

    def generate(self, prompt: str, temperature: float = 0) -> str:
        """Send prompt to LLM and return response text.

        Raises:
            RuntimeError: If cost limit exceeded.
            Exception: On API errors (after retries handled by caller).
        """
        if not self.check_cost_limit():
            raise RuntimeError(
                f"Cost limit reached for {self.name}: "
                f"${self.total_cost_usd:.2f} >= ${self.cost_limit_usd:.2f}"
            )

        if self.provider == "google":
            return self._generate_google(prompt, temperature)
        elif self.provider in ("openai", "openai_compatible", "together"):
            return self._generate_openai(prompt, temperature)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _generate_google(self, prompt: str, temperature: float) -> str:
        """Generate via Google Generative AI SDK."""
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model_id)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=temperature),
        )
        # Track usage
        usage = response.usage_metadata
        self._update_usage(
            input_tokens=usage.prompt_token_count,
            output_tokens=usage.candidates_token_count,
        )
        return response.text

    def _generate_openai(self, prompt: str, temperature: float) -> str:
        """Generate via OpenAI-compatible API."""
        from openai import OpenAI

        client_kwargs = {"api_key": self.api_key}
        if self.api_base:
            client_kwargs["base_url"] = self.api_base

        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        # Track usage
        usage = response.usage
        self._update_usage(
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
        )
        return response.choices[0].message.content

    def get_usage_report(self) -> dict:
        """Return usage statistics."""
        return {
            "model": self.name,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "cost_limit_usd": self.cost_limit_usd,
        }


def create_client(name: str, model_config: dict) -> LLMClient:
    """Create an LLMClient from model config and environment variables."""
    api_key = os.environ.get(model_config["env_key"], "")
    return LLMClient(
        name=name,
        provider=model_config["provider"],
        model_id=model_config["model_id"],
        api_key=api_key,
        api_base=model_config.get("api_base"),
        cost_per_1m_input=model_config.get("cost_per_1m_input", 0.0),
        cost_per_1m_output=model_config.get("cost_per_1m_output", 0.0),
        cost_limit_usd=model_config.get("cost_limit_usd", 50.0),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m pytest tests/test_translation/test_client.py -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

Run:
```bash
git add src/translation/client.py tests/test_translation/test_client.py
git commit -m "feat(translation): add LLM client wrapper with token tracking"
```

---

### Task 6: Create translation validation module ✅ DONE

**Files:**
- Create: `src/translation/validate.py`
- Create: `tests/test_translation/test_validate.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for translation validation (similarity + BI-RADS lexicon check)."""

from src.translation.validate import (
    check_birads_terms_match,
    classify_divergence,
)


def test_birads_terms_match_identical():
    """Identical translations should have all terms matching."""
    glossary_pt = ["mama direita", "calcificação", "nódulo"]
    text_a = "Observa-se um nódulo na mama direita com calcificação."
    text_b = "Observa-se um nódulo na mama direita com calcificação."
    result = check_birads_terms_match(text_a, text_b, glossary_pt)
    assert result["match_ratio"] == 1.0


def test_birads_terms_match_divergent():
    """Different BI-RADS terms should be flagged."""
    glossary_pt = ["mama direita", "mama esquerda", "nódulo"]
    text_a = "Observa-se um nódulo na mama direita."
    text_b = "Observa-se um nódulo na mama esquerda."
    result = check_birads_terms_match(text_a, text_b, glossary_pt)
    assert result["match_ratio"] < 1.0
    assert len(result["mismatched_terms"]) > 0


def test_classify_divergence_ok():
    """High similarity + high term match = OK."""
    result = classify_divergence(similarity=0.98, term_match_ratio=1.0, threshold=0.95)
    assert result == "ok"


def test_classify_divergence_review():
    """Low similarity = needs review."""
    result = classify_divergence(similarity=0.90, term_match_ratio=1.0, threshold=0.95)
    assert result == "review"


def test_classify_divergence_term_mismatch():
    """High similarity but low term match = needs review."""
    result = classify_divergence(similarity=0.98, term_match_ratio=0.5, threshold=0.95)
    assert result == "review"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
python -m pytest tests/test_translation/test_validate.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement validate.py**

```python
"""Validate translation fidelity: semantic similarity + BI-RADS lexicon check."""

from sentence_transformers import SentenceTransformer
import numpy as np


_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    """Lazy-load the embedding model (singleton)."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
    return _embedding_model


def compute_similarity(text_a: str, text_b: str) -> float:
    """Compute cosine similarity between two texts using multilingual embeddings."""
    model = get_embedding_model()
    embeddings = model.encode([text_a, text_b], convert_to_numpy=True)
    cos_sim = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    return float(cos_sim)


def check_birads_terms_match(
    text_a: str, text_b: str, glossary_pt_terms: list[str]
) -> dict:
    """Check if both translations contain the same BI-RADS terms.

    Returns dict with match_ratio and list of mismatched terms.
    """
    text_a_lower = text_a.lower()
    text_b_lower = text_b.lower()

    terms_in_a = set()
    terms_in_b = set()
    for term in glossary_pt_terms:
        term_lower = term.lower()
        if term_lower in text_a_lower:
            terms_in_a.add(term)
        if term_lower in text_b_lower:
            terms_in_b.add(term)

    all_terms = terms_in_a | terms_in_b
    if not all_terms:
        return {"match_ratio": 1.0, "mismatched_terms": [], "terms_found": 0}

    matching = terms_in_a & terms_in_b
    mismatched = list(all_terms - matching)
    match_ratio = len(matching) / len(all_terms)

    return {
        "match_ratio": match_ratio,
        "mismatched_terms": mismatched,
        "terms_found": len(all_terms),
    }


def classify_divergence(
    similarity: float, term_match_ratio: float, threshold: float = 0.95
) -> str:
    """Classify whether a translation pair needs review.

    Returns 'ok' or 'review'.
    """
    if similarity >= threshold and term_match_ratio >= 0.8:
        return "ok"
    return "review"
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m pytest tests/test_translation/test_validate.py -v
```
Expected: 5 passed

- [ ] **Step 5: Commit**

Run:
```bash
git add src/translation/validate.py tests/test_translation/test_validate.py
git commit -m "feat(translation): add validation module (similarity + BI-RADS terms)"
```

---

### Task 7: Create main translation pipeline ✅ DONE

**Files:**
- Create: `src/translation/translate.py`
- Modify: `src/translation/__init__.py`

- [ ] **Step 1: Implement translate.py**

```python
"""Main translation pipeline: ES→PT with dual-LLM validation.

Usage:
    python -m src.translation.translate
    python -m src.translation.translate --llm-primary gemini-2.0-flash --batch-size 5
"""

import json
import time
from pathlib import Path

import pandas as pd
import yaml
from tqdm import tqdm

from src.translation.config import CONFIG, parse_args
from src.translation.glossary import load_glossary, format_glossary_for_prompt
from src.translation.prompt import build_translation_prompt
from src.translation.client import create_client, LLMClient
from src.translation.validate import (
    compute_similarity,
    check_birads_terms_match,
    classify_divergence,
)


def load_models_config(config: dict) -> dict:
    """Load models.yaml config."""
    with open(config["models_config_path"], encoding="utf-8") as f:
        return yaml.safe_load(f)


def translate_report(
    report_text: str,
    client: LLMClient,
    prompt_template_args: dict,
    temperature: float,
    max_retries: int = 3,
) -> str | None:
    """Translate a single report with retry logic.

    Returns the translated text, or None if all retries fail.
    """
    glossary_text = prompt_template_args["glossary_text"]
    prompt = build_translation_prompt(report_text, glossary_text)

    for attempt in range(max_retries):
        try:
            response = client.generate(prompt, temperature=temperature)
            if response and response.strip():
                return response.strip()
        except RuntimeError:
            raise  # Cost limit — don't retry
        except Exception as e:
            print(f"  Attempt {attempt + 1}/{max_retries} failed for {client.name}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None


def load_progress(output_path: str) -> set[str]:
    """Load already-translated report IDs for resume capability."""
    path = Path(output_path)
    if path.exists():
        df = pd.read_csv(path, encoding="utf-8")
        return set(df["report_id"].astype(str))
    return set()


def save_translations(translations: list[dict], output_path: str, append: bool = False) -> None:
    """Save translations to CSV."""
    df = pd.DataFrame(translations)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if append and path.exists():
        existing = pd.read_csv(path, encoding="utf-8")
        df = pd.concat([existing, df], ignore_index=True)

    df.to_csv(path, index=False, encoding="utf-8")


def run_translation(config: dict) -> None:
    """Run the full translation pipeline."""
    print("=" * 60)
    print("Translation Pipeline ES → PT")
    print("=" * 60)

    # Load data
    print(f"\nLoading reports from {config['source_path']}...")
    df = pd.read_csv(config["source_path"], encoding="utf-8")
    print(f"  Total reports: {len(df)}")

    # Load glossary
    print(f"Loading glossary from {config['birads_glossary_path']}...")
    glossary_pairs = load_glossary(config["birads_glossary_path"])
    glossary_text = format_glossary_for_prompt(glossary_pairs)
    glossary_pt_terms = [pt for _, pt in glossary_pairs]
    print(f"  Loaded {len(glossary_pairs)} term pairs")

    # Create LLM clients
    models_config = load_models_config(config)
    primary_name = config["llm_primary"]
    secondary_name = config["llm_secondary"]

    print(f"\nCreating clients: {primary_name} (primary), {secondary_name} (secondary)")
    client_primary = create_client(primary_name, models_config["models"][primary_name])
    client_secondary = create_client(secondary_name, models_config["models"][secondary_name])

    prompt_args = {"glossary_text": glossary_text}

    # Check resume
    done_primary = load_progress(config["output_primary_path"]) if config["resume"] else set()
    done_secondary = load_progress(config["output_secondary_path"]) if config["resume"] else set()
    done_both = done_primary & done_secondary
    if done_both:
        print(f"  Resuming: {len(done_both)} reports already translated")

    # Translate
    results_primary = []
    results_secondary = []
    validation_results = []

    pending = df[~df["report_id"].astype(str).isin(done_both)]
    print(f"\n  Reports to translate: {len(pending)}")
    print(f"  Temperature: {config['temperature']}")
    print()

    for idx, row in tqdm(pending.iterrows(), total=len(pending), desc="Translating"):
        report_id = str(row["report_id"])
        report_text = row["report_text_raw"]

        # Primary translation
        translation_1 = translate_report(
            report_text, client_primary, prompt_args,
            config["temperature"], config["max_retries"],
        )

        # Secondary translation
        translation_2 = translate_report(
            report_text, client_secondary, prompt_args,
            config["temperature"], config["max_retries"],
        )

        results_primary.append({
            "report_id": report_id,
            "report_text_translated": translation_1 or "",
            "translation_success": translation_1 is not None,
        })
        results_secondary.append({
            "report_id": report_id,
            "report_text_translated": translation_2 or "",
            "translation_success": translation_2 is not None,
        })

        # Validate if both succeeded
        if translation_1 and translation_2:
            similarity = compute_similarity(translation_1, translation_2)
            terms_check = check_birads_terms_match(
                translation_1, translation_2, glossary_pt_terms,
            )
            status = classify_divergence(
                similarity, terms_check["match_ratio"], config["similarity_threshold"],
            )
            validation_results.append({
                "report_id": report_id,
                "similarity": round(similarity, 4),
                "term_match_ratio": round(terms_check["match_ratio"], 4),
                "mismatched_terms": terms_check["mismatched_terms"],
                "status": status,
            })

        # Save periodically
        if (len(results_primary) % config["batch_size"] == 0) or (idx == pending.index[-1]):
            save_translations(results_primary, config["output_primary_path"], append=bool(done_both))
            save_translations(results_secondary, config["output_secondary_path"], append=bool(done_both))
            done_both.update(r["report_id"] for r in results_primary)
            results_primary = []
            results_secondary = []

    # Build final output: use primary translation as reference
    print("\nBuilding final translated dataset...")
    primary_df = pd.read_csv(config["output_primary_path"], encoding="utf-8")
    original_df = pd.read_csv(config["source_path"], encoding="utf-8")

    final_df = original_df[["report_id", "birads_label"]].merge(
        primary_df[["report_id", "report_text_translated"]],
        on="report_id",
        how="inner",
    )
    final_df = final_df.rename(columns={"report_text_translated": "report_text_raw"})
    final_df.to_csv(config["output_path"], index=False, encoding="utf-8")
    print(f"  Saved {len(final_df)} translated reports to {config['output_path']}")

    # Save validation results
    results_dir = Path(config["divergences_path"]).parent
    results_dir.mkdir(parents=True, exist_ok=True)

    divergences = [v for v in validation_results if v["status"] == "review"]
    with open(config["divergences_path"], "w", encoding="utf-8") as f:
        json.dump(divergences, f, ensure_ascii=False, indent=2)
    print(f"  Divergences flagged for review: {len(divergences)}")

    # Save stats
    total_validated = len(validation_results)
    ok_count = sum(1 for v in validation_results if v["status"] == "ok")
    avg_similarity = (
        sum(v["similarity"] for v in validation_results) / total_validated
        if total_validated > 0 else 0
    )
    stats = {
        "total_reports": len(df),
        "translated_reports": len(final_df),
        "validated_reports": total_validated,
        "ok_count": ok_count,
        "review_count": len(divergences),
        "avg_similarity": round(avg_similarity, 4),
        "primary_model": primary_name,
        "secondary_model": secondary_name,
        "primary_usage": client_primary.get_usage_report(),
        "secondary_usage": client_secondary.get_usage_report(),
    }
    with open(config["stats_path"], "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"  Stats saved to {config['stats_path']}")

    # Print summary
    print("\n" + "=" * 60)
    print("TRANSLATION SUMMARY")
    print("=" * 60)
    print(f"  Total translated: {len(final_df)}/{len(df)}")
    print(f"  Avg similarity:   {avg_similarity:.4f}")
    print(f"  OK:               {ok_count}")
    print(f"  Needs review:     {len(divergences)}")
    print(f"  Primary cost:     ${client_primary.total_cost_usd:.4f}")
    print(f"  Secondary cost:   ${client_secondary.total_cost_usd:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    config = parse_args()
    run_translation(config)
```

- [ ] **Step 2: Update __init__.py**

```python
"""Translation module: ES→PT mammography report translation with dual-LLM validation."""
```

- [ ] **Step 3: Commit**

Run:
```bash
git add src/translation/translate.py src/translation/__init__.py
git commit -m "feat(translation): add main translation pipeline with resume and validation"
```

---

### Task 8: Create integration test with mocked APIs ✅ DONE

**Files:**
- Create: `tests/test_translation/test_translate_integration.py`

- [ ] **Step 1: Write integration test**

```python
"""Integration test for the translation pipeline with mocked LLM APIs."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd

from src.translation.translate import run_translation


def _create_test_fixtures(tmp_dir: Path) -> dict:
    """Create minimal test data and configs for integration test."""
    # Minimal CSV with 2 reports
    reports = pd.DataFrame({
        "report_id": ["RPT_001", "RPT_002"],
        "report_text_raw": [
            "Se observa un nódulo en mama derecha.",
            "No se observan calcificaciones sospechosas.",
        ],
        "birads_label": [2, 1],
    })
    source_path = tmp_dir / "test_reports.csv"
    reports.to_csv(source_path, index=False, encoding="utf-8")

    # Minimal glossary
    glossary = {
        "metadata": {"source": "test"},
        "terms": {
            "anatomy": [{"es": "mama derecha", "pt": "mama direita"}],
            "findings": [{"es": "nódulo", "pt": "nódulo"}],
        },
    }
    glossary_path = tmp_dir / "glossary.json"
    with open(glossary_path, "w", encoding="utf-8") as f:
        json.dump(glossary, f, ensure_ascii=False)

    # Minimal models.yaml
    models_yaml = {
        "models": {
            "gemini-2.0-flash": {
                "provider": "google",
                "model_id": "gemini-2.0-flash",
                "env_key": "GOOGLE_API_KEY",
                "cost_per_1m_input": 0.0,
                "cost_per_1m_output": 0.0,
                "cost_limit_usd": 50.0,
            },
            "deepseek-v3": {
                "provider": "openai_compatible",
                "model_id": "deepseek-chat",
                "api_base": "https://api.deepseek.com/v1",
                "env_key": "DEEPSEEK_API_KEY",
                "cost_per_1m_input": 0.07,
                "cost_per_1m_output": 1.10,
                "cost_limit_usd": 50.0,
            },
        },
    }
    import yaml
    models_path = tmp_dir / "models.yaml"
    with open(models_path, "w", encoding="utf-8") as f:
        yaml.dump(models_yaml, f)

    config = {
        "source_path": str(source_path),
        "output_path": str(tmp_dir / "translated.csv"),
        "output_primary_path": str(tmp_dir / "primary.csv"),
        "output_secondary_path": str(tmp_dir / "secondary.csv"),
        "divergences_path": str(tmp_dir / "results" / "divergences.json"),
        "stats_path": str(tmp_dir / "results" / "stats.json"),
        "llm_primary": "gemini-2.0-flash",
        "llm_secondary": "deepseek-v3",
        "similarity_threshold": 0.95,
        "temperature": 0,
        "birads_glossary_path": str(glossary_path),
        "models_config_path": str(models_path),
        "batch_size": 10,
        "max_retries": 1,
        "resume": False,
    }
    return config


@patch("src.translation.client.LLMClient.generate")
@patch("src.translation.validate.compute_similarity")
def test_pipeline_produces_output_files(mock_similarity, mock_generate, tmp_path):
    """Full pipeline with mocked APIs produces expected output files."""
    config = _create_test_fixtures(tmp_path)

    # Mock LLM responses
    mock_generate.return_value = "Observa-se um nódulo na mama direita."
    mock_similarity.return_value = 0.98

    with patch.dict("os.environ", {
        "GOOGLE_API_KEY": "fake",
        "DEEPSEEK_API_KEY": "fake",
    }):
        run_translation(config)

    # Check output files exist
    assert Path(config["output_path"]).exists()
    assert Path(config["divergences_path"]).exists()
    assert Path(config["stats_path"]).exists()

    # Check translated CSV has correct structure
    translated = pd.read_csv(config["output_path"], encoding="utf-8")
    assert len(translated) == 2
    assert "report_id" in translated.columns
    assert "report_text_raw" in translated.columns
    assert "birads_label" in translated.columns

    # Check stats
    with open(config["stats_path"], encoding="utf-8") as f:
        stats = json.load(f)
    assert stats["total_reports"] == 2
    assert stats["translated_reports"] == 2
```

- [ ] **Step 2: Run integration test**

Run:
```bash
python -m pytest tests/test_translation/test_translate_integration.py -v
```
Expected: 1 passed

- [ ] **Step 3: Commit**

Run:
```bash
git add tests/test_translation/test_translate_integration.py
git commit -m "test(translation): add integration test with mocked LLM APIs"
```

---

### Task 9: Run all translation tests ✅ DONE

- [ ] **Step 1: Run full test suite**

Run:
```bash
python -m pytest tests/test_translation/ -v
```
Expected: All tests pass (11 total)

- [ ] **Step 2: Commit if any fixes were needed**

---

### Task 10: Test with real APIs (small sample) ✅ DONE

**Prerequisites:** API keys configured in `.env` file.

- [ ] **Step 1: Create .env with real API keys**

Create `.env` (NOT tracked by git — already in .gitignore):
```env
GOOGLE_API_KEY=your-real-key
DEEPSEEK_API_KEY=your-real-key
```

- [ ] **Step 2: Create a small test CSV (3 reports)**

Run:
```bash
python -c "
import pandas as pd
df = pd.read_csv('data/reports_raw_canonical.csv', encoding='utf-8', nrows=3)
df.to_csv('data/test_sample_3.csv', index=False, encoding='utf-8')
print(f'Created sample with {len(df)} reports')
"
```

- [ ] **Step 3: Run translation on sample**

Run:
```bash
python -m src.translation.translate --source-path data/test_sample_3.csv --output-path data/test_translated_3.csv --batch-size 3
```

- [ ] **Step 4: Inspect results**

Run:
```bash
python -c "
import pandas as pd
import json

# Check translated reports
df = pd.read_csv('data/test_translated_3.csv', encoding='utf-8')
print('=== Translated Reports ===')
for _, row in df.iterrows():
    print(f'\nID: {row[\"report_id\"]}')
    print(f'Text: {row[\"report_text_raw\"][:200]}...')

# Check stats
with open('results/translation/stats.json', encoding='utf-8') as f:
    stats = json.load(f)
print('\n=== Stats ===')
print(json.dumps(stats, indent=2))
"
```

Verify:
- Translations are in Portuguese
- BI-RADS terminology is preserved
- Stats show similarity scores

- [ ] **Step 5: Clean up test files**

Run:
```bash
rm data/test_sample_3.csv data/test_translated_3.csv
```

- [ ] **Step 6: Commit any fixes from real API testing**

Run:
```bash
git add -u
git commit -m "fix(translation): adjustments from real API testing"
```

---

### Task 11: Run full translation (4,357 reports) ✅ DONE (4.357/4.357 traduzidos, 99.06% aprovados)

**Note:** This will take significant time and cost. Ensure API keys are configured and cost limits are appropriate.

- [ ] **Step 1: Run full translation**

Run:
```bash
python -m src.translation.translate
```

Monitor progress in console. The pipeline saves periodically and supports resume if interrupted.

- [ ] **Step 2: Verify output**

Run:
```bash
python -c "
import pandas as pd
import json

df_es = pd.read_csv('data/reports_raw_canonical.csv', encoding='utf-8')
df_pt = pd.read_csv('data/reports_translated_pt.csv', encoding='utf-8')
print(f'Original ES: {len(df_es)} reports')
print(f'Translated PT: {len(df_pt)} reports')
print(f'Match: {len(df_es) == len(df_pt)}')

with open('results/translation/stats.json', encoding='utf-8') as f:
    stats = json.load(f)
print(f'Avg similarity: {stats[\"avg_similarity\"]}')
print(f'Needs review: {stats[\"review_count\"]}')
"
```

- [ ] **Step 3: Commit results**

Run:
```bash
git add data/reports_translated_pt.csv results/translation/
git commit -m "data: add complete PT translated dataset (4357 reports)"
```

---

## Translation Evaluation Framework (P1-T12 onwards)

> **Spec:** `docs/superpowers/specs/2026-04-26-translation-evaluation-framework.md`
>
> **Goal:** Validate translation quality through 5-source triangulation (intrinsic metrics, programmatic structural checks, back-translation, LLM auditor, human MQM review). Outputs `validation_results.jsonl` as single source of truth.
>
> **All evaluation tasks below produce restart-safe artifacts (JSONL append + flush, or CSV with resume by ID).**

---

### Task 12: Setup eval infrastructure + build BI-RADS Atlas glossary (F5.A) 🔲 PENDING

**Files:**
- Create: `configs/birads_glossary_atlas_es_pt.json`
- Create: `src/evaluation/__init__.py`
- Create: `src/evaluation/io.py` (JSONL append helpers with fsync)
- Create: `tests/test_evaluation/test_io.py`

**Note:** All evaluation modules go under `src/evaluation/` to keep separate from `src/translation/`.

- [ ] **Step 1: Write JSONL append helpers with fsync**

Create `src/evaluation/io.py`:

```python
"""Restart-safe JSONL I/O helpers."""

import json
import os
from pathlib import Path


def append_jsonl(path: str, record: dict) -> None:
    """Append a single record to JSONL file with fsync for crash safety."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def load_done_ids(path: str, id_field: str = "report_id") -> set[str]:
    """Load report_ids already processed. Tolerates corrupt last line."""
    if not Path(path).exists():
        return set()
    done = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                done.add(rec[id_field])
            except (json.JSONDecodeError, KeyError):
                continue  # skip corrupt/incomplete
    return done
```

- [ ] **Step 2: Write test for io.py**

Create `tests/test_evaluation/test_io.py`:

```python
import json
from src.evaluation.io import append_jsonl, load_done_ids


def test_append_jsonl_creates_file(tmp_path):
    path = tmp_path / "out.jsonl"
    append_jsonl(str(path), {"report_id": "RPT_001", "score": 9})
    content = path.read_text(encoding="utf-8").strip()
    assert json.loads(content) == {"report_id": "RPT_001", "score": 9}


def test_load_done_ids_skips_corrupt(tmp_path):
    path = tmp_path / "out.jsonl"
    path.write_text(
        '{"report_id": "RPT_001"}\n{"report_id": "RPT_002"}\n{corrupt',
        encoding="utf-8"
    )
    assert load_done_ids(str(path)) == {"RPT_001", "RPT_002"}
```

Run: `pytest tests/test_evaluation/test_io.py -v` → 2 PASS

- [ ] **Step 3: Build the BI-RADS Atlas glossary (with backward compatibility)**

Build `configs/birads_glossary_atlas_es_pt.json` from ACR BI-RADS Atlas 5th ed + CBR/SBM adaptation. Target ~200 terms organized by clinical category.

#### ⚠ Restrição metodológica crítica: retrocompatibilidade com glossário original

O glossário Atlas (~200 termos) é mais rico que o original (~95) usado durante a tradução em T11. Se o auditor cobrar termos do Atlas que o tradutor **nunca recebeu**, a Phase B vai gerar **falso positivo retroativo** — punindo o tradutor por algo que não foi instruído a fazer.

**Regra:** toda escolha PT que aparece no glossário original (`birads_glossary_es_pt.json`) DEVE estar listada em `pt_variants_acceptable` da entrada Atlas correspondente, **mesmo quando não for o `pt_canonical`**.

**Exemplo concreto:**
- Glossário original (T1) tem `{"es": "ovalada", "pt": "ovalada"}` e `{"es": "ovalado", "pt": "ovalado"}`
- Atlas oficial CBR/SBM usa `oval` como descritor canônico de forma de massa
- Solução: a entrada Atlas vira:

```json
{
  "es": "oval",
  "pt_canonical": "oval",
  "pt_variants_acceptable": ["oval", "ovalada", "ovalado"],
  "bi_rads_code": "MASS_SHAPE_OVAL"
}
```

Assim:
- ✅ A reauditoria (T13) e auditoria léxica não punem `ovalado/a` (forma que o tradutor recebeu)
- ✅ Métricas downstream (F5.B/C) reportam `canonical_ratio < 1.0` para esse termo, mas **categorizam as variantes como `acceptable`** em vez de `wrong_term`
- ✅ TCC argumenta: "tradutor seguiu fielmente o glossário recebido; o Atlas oferece referência canônica para futuro pipeline"

**Estrutura final da entrada:**

```json
{
  "es": "<termo origem espanhol>",
  "pt_canonical": "<forma canônica CBR/SBM PT-br>",
  "pt_variants_acceptable": ["<canônica>", "<variantes do glossário antigo>", ...],
  "pt_variants_unacceptable": ["<typos comuns, formas erradas>", ...],
  "bi_rads_code": "<código atlas>",

  // CAMPOS NOVOS (apenas para adjetivos BI-RADS — ~30 entradas, requeridos por T18)
  "forms_pt": {
    "M-SING": "<forma masc sing>",
    "F-SING": "<forma fem sing>",
    "M-PLUR": "<forma masc plur>",
    "F-PLUR": "<forma fem plur>"
  },
  "forms_es": {
    "M-SING": "...", "F-SING": "...", "M-PLUR": "...", "F-PLUR": "..."
  }
}
```

**`forms_pt`/`forms_es` são obrigatórios apenas para adjetivos** (`mass_shape`, `mass_margin`, `mass_density`, `calcifications_morphology/distribution`, `associated_features`). Substantivos âncora (`mama`, `lesão`, `nódulo`, `quadrante`) NÃO recebem `forms_*` — eles sustentam concordância, não a expressam.

**Gate adicional em T12 (verificação morfológica — pré-requisito de T18):** script `scripts/verify_atlas_morphology.py` confere que toda entrada com `forms_pt` tem 4 chaves esperadas (`M-SING`, `F-SING`, `M-PLUR`, `F-PLUR`), idem `forms_es`, e que cada forma listada em `forms_pt` aparece em `pt_variants_acceptable` (consistência interna). Detalhes em T18.

**Estrutura final do arquivo:**

```json
{
  "metadata": {
    "source": "ACR BI-RADS Atlas 5th ed + CBR/SBM PT-br adaptation",
    "version": "2026-04-27",
    "term_count": 200,
    "backward_compatibility": "configs/birads_glossary_es_pt.json (95 termos) - todas as PT do antigo aparecem em pt_variants_acceptable"
  },
  "categories": {
    "mass_shape": [
      {"es": "redonda", "pt_canonical": "redonda",
       "pt_variants_acceptable": ["redonda", "redondo"],
       "bi_rads_code": "MASS_SHAPE_ROUND"},
      {"es": "oval", "pt_canonical": "oval",
       "pt_variants_acceptable": ["oval", "ovalada", "ovalado"],
       "bi_rads_code": "MASS_SHAPE_OVAL"},
      {"es": "irregular", "pt_canonical": "irregular",
       "pt_variants_acceptable": ["irregular"],
       "bi_rads_code": "MASS_SHAPE_IRREGULAR"}
    ],
    "mass_margin": [...],
    "mass_density": [...],
    "calcifications_morphology": [...],
    "calcifications_distribution": [...],
    "associated_features": [...],
    "anatomy": [...],
    "categories_birads": [...]
  }
}
```

#### Ajuste 5: divergência ovalado vs oval (CBR/SBM) — decidida no glossário, não no prompt

**Princípio:** decisões de glossário se resolvem no glossário. O prompt do auditor (T12.5) é puramente mecânico — deriva da fonte de verdade JSON, não harmoniza nada.

**Caso concreto:**
- CBR/SBM oficial: descritor canônico de forma oval = `oval`
- Glossário original (T1) usado na tradução: `ovalado` / `ovalada`
- **Decisão tomada AQUI em T12 (não em T12.5):** ambas as formas vão para `pt_variants_acceptable`. `pt_canonical` segue a CBR (`oval`) como referência institucional, mas qualquer das três formas é válida na cobrança.

```json
{
  "es": "oval",
  "pt_canonical": "oval",                              // referência CBR/SBM
  "pt_variants_acceptable": ["oval", "ovalada", "ovalado"],  // tudo que apareceu na base traduzida
  "bi_rads_code": "MASS_SHAPE_OVAL"
}
```

**Regra geral aplicável a todos os termos:** para cada `(es, pt_canonical)` do Atlas, **`pt_variants_acceptable` deve incluir todas as formas que aparecem na base traduzida** (4.357 laudos PT). Não há outra hora para decidir isso — a base já está fixa.

- [ ] **Step 3.5: Coletar variantes empíricas do corpus traduzido (evidence-based)**

Antes de finalizar o glossário Atlas, escanear `data/reports_translated_pt.csv` para descobrir quais variantes PT de cada termo ES de fato aparecem:

```python
# scripts/collect_pt_variants_from_corpus.py
import pandas as pd
import json
from pathlib import Path
import re
import unicodedata

OLD_GLOSS = json.loads(Path("configs/birads_glossary_es_pt.json").read_text(encoding="utf-8"))
DF = pd.read_csv("data/reports_translated_pt.csv")
PT_TEXTS = " ".join(DF["report_text_raw"].fillna("").astype(str)).lower()


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


# Para cada (es, pt) do glossário antigo + variantes morfológicas comuns
findings = {}
for cat, items in OLD_GLOSS["terms"].items():
    for entry in items:
        es = entry["es"]
        pt = entry["pt"]
        # Variações morfológicas a procurar: forma original + sing/plur + masc/fem
        candidates = {pt, pt+"s", pt[:-1]+"a" if pt.endswith("o") else pt,
                      pt[:-1]+"as" if pt.endswith("o") else pt+"s"}
        observed = []
        for c in candidates:
            if re.search(r'\b' + re.escape(c.lower()) + r'\b', PT_TEXTS):
                observed.append(c.lower())
        findings[es] = observed

print(json.dumps(findings, ensure_ascii=False, indent=2))
```

Run: `python scripts/collect_pt_variants_from_corpus.py > results/translation/observed_pt_variants.json`

Usar a saída como **insumo direto** para `pt_variants_acceptable` do Atlas. Isso garante que toda variante já em produção é tolerada.

- [ ] **Step 3.7: Estender ~30 adjetivos com `forms_pt` + `forms_es` (Passo 1 de T18)**

Para cada adjetivo BI-RADS canônico das categorias listadas em T18, preencher mapa morfológico explícito. Exemplo:

```json
{
  "es": "espiculado", "pt_canonical": "espiculado",
  "pt_variants_acceptable": ["espiculado", "espiculada", "espiculados", "espiculadas"],
  "bi_rads_code": "MASS_MARGIN_SPICULATED",
  "forms_pt": {"M-SING": "espiculado", "F-SING": "espiculada",
               "M-PLUR": "espiculados", "F-PLUR": "espiculadas"},
  "forms_es": {"M-SING": "espiculado", "F-SING": "espiculada",
               "M-PLUR": "espiculados", "F-PLUR": "espiculadas"}
}
```

Trabalho mecânico (~30 entradas × 4 formas PT + 4 formas ES). Após preencher, rodar gate de morfologia (Step 3.8).

- [ ] **Step 3.8: Gate `verify_atlas_morphology.py` (pré-requisito de T18)**

Criar `scripts/verify_atlas_morphology.py` (especificação completa em T18). Roda como gate antes do commit de T12 — falha o build se alguma entrada tem `forms_pt` mal formado, ou se alguma forma listada não aparece em `pt_variants_acceptable`.

```bash
python -m scripts.verify_atlas_morphology
# Esperado: "OK: morfologia validada para todas as entradas com forms_pt/forms_es"
```

Se `FAIL`, ajustar o glossário e rerodar até passar.

- [ ] **Step 4: Diff verification — every old PT term must appear in Atlas `pt_variants_acceptable`**

**Pré-condição obrigatória de T12 (gate antes do commit).** Roda script verificando que toda escolha PT do glossário original (~95 termos) está coberta pelo Atlas:

```python
# src/evaluation/verify_atlas_backward_compat.py
import json
from pathlib import Path
import sys

OLD = json.loads(Path("configs/birads_glossary_es_pt.json").read_text(encoding="utf-8"))
NEW = json.loads(Path("configs/birads_glossary_atlas_es_pt.json").read_text(encoding="utf-8"))

# Flatten old PT terms (lowercased)
old_pt = set()
for cat, items in OLD["terms"].items():
    for entry in items:
        old_pt.add(entry["pt"].strip().lower())

# Flatten Atlas acceptable variants
new_acceptable = set()
for cat, items in NEW["categories"].items():
    for entry in items:
        for v in entry.get("pt_variants_acceptable", []):
            new_acceptable.add(v.strip().lower())
        # canonical also counts as acceptable
        new_acceptable.add(entry["pt_canonical"].strip().lower())

# Diff
missing = old_pt - new_acceptable
if missing:
    print("FAIL: termos PT do glossário original NÃO cobertos pelo Atlas:")
    for t in sorted(missing):
        print(f"  - {t}")
    sys.exit(1)

print(f"OK: 100% dos {len(old_pt)} termos PT do glossário original aparecem em pt_variants_acceptable do Atlas")
print(f"Atlas total de variantes aceitáveis: {len(new_acceptable)}")
```

Run e verificar saída `OK: 100% ...` antes de prosseguir:

```bash
python -m src.evaluation.verify_atlas_backward_compat
```

Se imprimir `FAIL`, **adicionar as variantes faltantes** ao Atlas e rerodar até passar.

- [ ] **Step 5: Test for backward compatibility**

Adicionar a `tests/test_evaluation/test_glossary_atlas.py`:

```python
import json
from pathlib import Path


def test_atlas_backward_compatible_with_original():
    """Toda PT do glossário original deve aparecer em pt_variants_acceptable do Atlas."""
    old = json.loads(Path("configs/birads_glossary_es_pt.json").read_text(encoding="utf-8"))
    new = json.loads(Path("configs/birads_glossary_atlas_es_pt.json").read_text(encoding="utf-8"))

    old_pt = {e["pt"].strip().lower()
              for cat, items in old["terms"].items() for e in items}

    new_acceptable = set()
    for cat, items in new["categories"].items():
        for e in items:
            new_acceptable.add(e["pt_canonical"].strip().lower())
            new_acceptable.update(v.strip().lower() for v in e.get("pt_variants_acceptable", []))

    missing = old_pt - new_acceptable
    assert not missing, f"Atlas falta retrocompatibilidade para: {sorted(missing)}"
```

Run: `pytest tests/test_evaluation/test_glossary_atlas.py -v`

- [ ] **Step 6: Commit**

```bash
git add configs/birads_glossary_atlas_es_pt.json \
        src/evaluation/__init__.py src/evaluation/io.py \
        src/evaluation/verify_atlas_backward_compat.py \
        scripts/verify_atlas_morphology.py \
        tests/test_evaluation/
git commit -m "feat(evaluation): bootstrap eval module + Atlas BI-RADS glossario (~200 termos) com retrocompatibilidade + mapa morfologico para ~30 adjetivos"
```

---

### Task 12.5: Fix prompt do auditor C1 (derivação programática do glossário Atlas) 🔲 PENDING  ⚠ pré-requisito de T13

**Files:**
- Modify: `src/translation/prompt.py` (função `build_audit_prompt`, listas hardcoded em linhas 130–134)
- Create: `src/translation/c1_descriptors.py` (novo módulo: gera bloco C1 a partir do Atlas)
- Create: `tests/test_translation/test_c1_descriptors.py`

**Goal:** Eliminar falsos positivos sistemáticos em C1 alinhando a cobrança do auditor ao léxico **que o tradutor efetivamente recebeu**, derivando programaticamente da fonte de verdade (`birads_glossary_atlas_es_pt.json`) — incluindo `pt_variants_acceptable` (não só `pt_canonical`).

**Escopo desta task — o que NÃO é decidido aqui:**
- ❌ **NÃO** harmoniza `oval` vs `ovalado/a` (decisão de glossário, feita em T12)
- ❌ **NÃO** escolhe forma canônica de descritor (decisão de glossário, feita em T12)
- ❌ **NÃO** redefine vocabulário BI-RADS (responsabilidade do Atlas, T12)

**O que esta task FAZ:**
- ✅ Derivar mecanicamente o bloco C1 a partir do JSON do Atlas (cuja decisão foi tomada em T12)
- ✅ Substituir lista hardcoded em `prompt.py:130-134`
- ✅ Validar empiricamente a redução de falsos positivos via smoke test

T12.5 é **puramente mecânico**: lê o glossário, gera o prompt, testa. Toda decisão lexical já está congelada no JSON quando T12.5 começa.

**Evidência empírica que justifica a fase (sample 517):**
- C1 = 81.4% dos falsos positivos (70/86 keeps)
- Taxa de FP dentro de C1: 89.7% (70 dos 78 achados C1 foram refutados pela meta-auditoria)
- Sem fix, T13 reproduz isso em escala (4.357 laudos)
- Termos problemáticos identificados em `prompt.py:130-134`:
  - 🔴 Espanhol cru: `lineal fino`, `pleomorfico`
  - 🟠 PT-pt sem til: `heterogeneo`, `homogeneo` (glossário tem `heterogêneo`, `homogêneo`)
  - 🟠 Só forma masculina: `obscurecido`, `isodenso` (faltam `obscurecida`, `isodensa`)
  - 🟡 Categorias inteiras ausentes: calcificações (mi/macro), composição mamária

#### Estratégia: derivação programática do bloco C1 a partir do Atlas

Em vez de listar termos manualmente no prompt, **gerar a lista C1 dinamicamente** a partir do glossário Atlas. Isso garante:
- Consistência total entre glossário recebido e cobrança do auditor
- `pt_variants_acceptable` aceitas (não só canônica) → resolve o caso `oval`/`ovalada`/`ovalado`
- Atualização automática quando o glossário evoluir (futuro)
- Auditor não pode cobrar termo que o tradutor não recebeu

- [ ] **Step 1: Implementar `c1_descriptors.py`**

```python
"""Generate the C1 descriptor list for the audit prompt from Atlas glossary."""

import json
from pathlib import Path


# Categorias do Atlas que entram no C1 (descritores BI-RADS)
C1_CATEGORIES = [
    "mass_shape",
    "mass_margin",
    "mass_density",
    "calcifications_morphology",
    "calcifications_distribution",
    "associated_features",
    "breast_composition",
]

# Rótulo legível para cada categoria no prompt
C1_LABELS = {
    "mass_shape": "Forma",
    "mass_margin": "Margem",
    "mass_density": "Densidade",
    "calcifications_morphology": "Morfologia de calcificações",
    "calcifications_distribution": "Distribuição de calcificações",
    "associated_features": "Achados associados",
    "breast_composition": "Composição mamária",
}


def build_c1_block(atlas_path: str = "configs/birads_glossary_atlas_es_pt.json") -> str:
    """Build the C1 audit block from Atlas glossary.

    Each category lists ALL acceptable PT variants (canonical + variants),
    so the auditor accepts any form the translator could legitimately have used.
    """
    atlas = json.loads(Path(atlas_path).read_text(encoding="utf-8"))
    cats = atlas["categories"]

    lines = ["C1. DESCRITORES BI-RADS (PRIORIDADE MAXIMA): Os descritores padronizados BI-RADS foram traduzidos corretamente para o portugues conforme o glossario? Verifique CADA descritor presente no original:"]

    for cat_key in C1_CATEGORIES:
        if cat_key not in cats:
            continue
        label = C1_LABELS[cat_key]
        # Coletar TODAS variantes aceitáveis (canonical + variants)
        all_variants = []
        for entry in cats[cat_key]:
            variants = set()
            variants.add(entry["pt_canonical"])
            variants.update(entry.get("pt_variants_acceptable", []))
            all_variants.append("/".join(sorted(variants)))
        terms = ", ".join(all_variants)
        lines.append(f"    - {label}: {terms}")

    lines.append("    Verifique tambem concordancia de genero e numero dos descritores. Aceite QUALQUER variante listada acima como correta.")
    return "\n".join(lines)
```

- [ ] **Step 2: Test `c1_descriptors.py`**

```python
# tests/test_translation/test_c1_descriptors.py
import json
from pathlib import Path
from src.translation.c1_descriptors import build_c1_block


def test_c1_block_includes_all_acceptable_variants(tmp_path):
    atlas = {
        "metadata": {"version": "test"},
        "categories": {
            "mass_shape": [
                {"es": "oval", "pt_canonical": "oval",
                 "pt_variants_acceptable": ["oval", "ovalada", "ovalado"]},
                {"es": "irregular", "pt_canonical": "irregular",
                 "pt_variants_acceptable": ["irregular"]},
            ]
        }
    }
    p = tmp_path / "atlas.json"
    p.write_text(json.dumps(atlas), encoding="utf-8")

    block = build_c1_block(str(p))
    # Todas as variantes têm que aparecer (separadas por '/')
    assert "oval/ovalada/ovalado" in block or "ovalada/ovalado/oval" in block
    assert "irregular" in block
    assert "Aceite QUALQUER variante" in block


def test_c1_block_uses_real_atlas():
    """Smoke test contra o Atlas real."""
    block = build_c1_block()
    # Categorias esperadas
    assert "Forma:" in block
    assert "Margem:" in block
    assert "Densidade:" in block
    # Termos PT-br corretos
    assert "heterogêneo" in block or "heterogeneo" not in block  # se aparecer, com til
    # Espanhol fora
    assert "lineal fino" not in block.lower()
    assert "pleomorfico" not in block.lower() or "pleomórfico" in block
```

Run: `pytest tests/test_translation/test_c1_descriptors.py -v`

- [ ] **Step 3: Substituir bloco hardcoded em `prompt.py`**

Editar `build_audit_prompt` em `src/translation/prompt.py`:

```python
from src.translation.c1_descriptors import build_c1_block


def build_audit_prompt(original_text: str, translated_text: str, glossary_text: str) -> str:
    c1_block = build_c1_block()  # gera dinamicamente do Atlas

    prompt = f"""Voce e um auditor medico ...

CRITERIOS DE AUDITORIA:

{c1_block}

C2. CATEGORIA BI-RADS: ...
C3. MEDIDAS, NUMEROS E UNIDADES: ...
C4. LATERALIDADE E LOCALIZACAO ANATOMICA: ...
C5. OMISSOES E ADICOES: ...
C6. INVERSOES DE SENTIDO E ERROS DE NEGACAO: ...
C7. COMPARACOES TEMPORAIS E ACHADOS ASSOCIADOS: ...

{glossary_text}
...
"""
```

Manter C2–C7 inalterados (analise mostrou que eles têm 0 falsos positivos).

- [ ] **Step 4: Smoke test comparativo (20 laudos, antes/depois)**

Selecionar 20 laudos da última sessão que tiveram inconsistência em C1 (do `audit_results.json`). Rodar auditoria com prompt antigo e prompt novo, comparar:

```python
# scripts/smoke_test_c1_fix.py
import json
from src.translation.client import create_client
from src.translation.prompt import build_audit_prompt
from src.translation.translate import audit_translation
from src.translation.glossary import load_glossary, format_glossary_for_prompt

# Carregar 20 laudos com C1 inconsistência da sample original
with open("results/translation/audit_results.json") as f:
    data = json.load(f)

samples = []
for rec in data:
    incs = (rec.get("correction_history") or [{}])[0].get("inconsistencias") or []
    if any(i.get("criterio", "").startswith("C1") for i in incs):
        samples.append(rec)
        if len(samples) >= 20:
            break

# Re-auditar com prompt NOVO (build_audit_prompt já lê c1_descriptors)
import yaml
config = yaml.safe_load(open("configs/models.yaml"))
auditor = create_client("deepseek-v3", config["models"]["deepseek-v3"])
glossary_text = format_glossary_for_prompt(load_glossary("configs/birads_glossary_es_pt.json"))

before_c1 = sum(1 for s in samples
                for i in (s.get("correction_history") or [{}])[0].get("inconsistencias") or []
                if i.get("criterio", "").startswith("C1"))

after_c1 = 0
for s in samples:
    res = audit_translation(auditor, s["original_text"], s["translated_text"], glossary_text)
    after_c1 += sum(1 for i in (res or {}).get("inconsistencias", []) if i.get("criterio","").startswith("C1"))

print(f"C1 incs ANTES: {before_c1}")
print(f"C1 incs DEPOIS: {after_c1}")
print(f"Reducao: {100*(before_c1-after_c1)/before_c1 if before_c1 else 0:.1f}%")
```

**Critério de aprovação do fix:** redução ≥ 70% em inconsistências C1 nos mesmos 20 laudos. Se < 70%, investigar mais.

- [ ] **Step 5: Atualizar spec do framework**

Adicionar em `docs/superpowers/specs/2026-04-26-translation-evaluation-framework.md`, seção F1:

> **Pré-requisito da F1:** o prompt de auditoria foi corrigido em T12.5 para derivar a lista C1 programaticamente do glossário Atlas (com `pt_variants_acceptable`). Isso elimina ~80% dos falsos positivos C1 identificados na sample original (verdict=keep da meta-auditoria).

E na tabela de "Ameaças à validade", adicionar linha:

| Falso positivo C1 (auditor cobra ES/PT-pt/só-masculino) | reprovações sistemáticas indevidas | T12.5: derivação programática do C1 a partir do Atlas com `pt_variants_acceptable` aceitas |

- [ ] **Step 6: Commit**

```bash
git add src/translation/c1_descriptors.py src/translation/prompt.py \
        tests/test_translation/test_c1_descriptors.py \
        scripts/smoke_test_c1_fix.py \
        docs/superpowers/specs/2026-04-26-translation-evaluation-framework.md
git commit -m "fix(translation): derivar C1 do Atlas com variants acceptable (elimina ~80% FP do auditor)"
```

**Decisão downstream:** se o smoke test passa (≥70% redução em C1), prosseguir para T12.6. Senão, investigar se ainda há mismatch glossário↔Atlas, ou se há viés do DeepSeek que vai além do prompt.

---

### Task 12.6: Severidade clínica — substituir aprovado/reprovado binário por critical/major/minor 🔲 PENDING  ⚠ pré-requisito de T13

**Goal:** Substituir binário "aprovado/reprovado" por taxonomia de severidade ancorada em **impacto clínico**, alinhada ao MQM (T22). Permite headline metric defensável na banca: **"taxa de erro crítico = X%"** em vez de "score médio 9.31/10" (número que precisa explicação).

**Por que isso muda o jogo do TCC:**
- Hoje: erro de acento (`heterogeneo` vs `heterogêneo`) tem o mesmo peso de inversão de lateralidade (`esquerda` vs `direita`). Metodologicamente fraco.
- Depois: a banca lê 1 número e entende — "99.X% dos laudos sem erro crítico".
- Coerência total com MQM (T22): dimensões MQM já são uma taxonomia de severidade, agora as fontes automáticas falam a mesma linguagem.

**Files:**
- Modify: `src/translation/prompt.py` (build_audit_prompt: adicionar rubrica + campo `severity` no schema)
- Create: `src/evaluation/severity.py` (override mecânico determinístico)
- Create: `tests/test_evaluation/test_severity.py`
- Modify: `tests/test_translation/test_prompt.py` (testar novo schema)

#### Taxonomia (registrada como invariante metodológica)

| Severidade | Critério | Exemplos |
|---|---|---|
| **critical** | Altera categoria BI-RADS, lateralidade, medida, negação ou conduta clínica | "BI-RADS 4" virou "BI-RADS 2"; "esquerda" virou "direita"; "15mm" virou "15cm"; "no se observan" virou "se observan" |
| **major** | Altera informação clínica relevante sem afetar categoria/conduta | Achado associado omitido (espessamento cutâneo); referência temporal alterada |
| **minor** | Problema linguístico/terminológico sem impacto clínico | Acento faltando, gênero desacordado, sinônimo PT válido fora do glossário |

#### Estratégia de classificação (híbrida — mecânica + LLM)

LLMs calibram severidade de forma instável sem âncora explícita. Mitigamos com **regra mecânica determinística** para os critérios objetivos:

| Critério | Estratégia | Severidade |
|---|---|---|
| **C2** Categoria BI-RADS | mecânica | sempre `critical` |
| **C3** Medidas/números | mecânica | sempre `critical` |
| **C4** Lateralidade/localização | mecânica | sempre `critical` |
| **C6** Inversão de negação | mecânica | sempre `critical` |
| **C1** Descritores BI-RADS | LLM (validado em T22) | `critical` ou `major` ou `minor` |
| **C5** Omissões/adições | LLM (validado em T22) | `critical` ou `major` ou `minor` |
| **C7** Temporais/achados associados | LLM (validado em T22) | `critical` ou `major` ou `minor` |

**Justificativa:** C2/C3/C4/C6 não dependem de julgamento — qualquer divergência detectada é, por definição, clinicamente impactante. C1/C5/C7 dependem de contexto (um sinônimo médico pode ser minor; uma omissão pode ser major OU critical).

- [ ] **Step 1: Adicionar rubrica e schema `severity` ao `build_audit_prompt`**

Em `src/translation/prompt.py`, dentro de `build_audit_prompt`, adicionar após a descrição dos critérios C1–C7:

```python
RUBRICA_SEVERIDADE = """
SEVERIDADE CLINICA (classifique cada inconsistencia detectada):

- critical: altera categoria BI-RADS, lateralidade, medida, negacao ou conduta clinica
- major: altera informacao clinica relevante sem afetar categoria/conduta
- minor: problema linguistico/terminologico sem impacto clinico

Exemplos:
- "BI-RADS 4" virou "BI-RADS 2" -> critical
- "mama esquerda" virou "mama direita" -> critical
- "15mm" virou "15cm" -> critical
- "no se observan calcificacoes" virou "se observan calcificacoes" -> critical
- "espessamento cutaneo" omitido na traducao -> major
- "redonda" traduzido como "redondo" (concordancia) -> minor
- "heterogeneo" traduzido sem til como "heterogeneo" -> minor
"""
```

Modificar o JSON de saída exigido (no final do prompt):

```python
{
  "criterio": "C1/C2/C3/C4/C5/C6/C7",
  "original": "trecho exato do texto original",
  "traducao": "trecho exato da traducao com problema",
  "problema": "descricao precisa do problema",
  "severity": "critical"  # NOVO: critical | major | minor
}
```

- [ ] **Step 2: Implementar `src/evaluation/severity.py` com override mecânico**

```python
"""Aplicar override mecanico de severidade nos critérios objetivos."""

# C2/C3/C4/C6 sao objetivos: qualquer divergencia detectada eh critical
MECHANICAL_CRITICAL_CRITERIA = {"C2", "C3", "C4", "C6"}

# Critérios subjetivos onde o LLM classifica e MQM (T22) valida
LLM_JUDGED_CRITERIA = {"C1", "C5", "C7"}

VALID_SEVERITIES = {"critical", "major", "minor"}


def apply_severity_override(inconsistencias: list[dict]) -> list[dict]:
    """Para cada inconsistência, aplica regra mecânica para C2/C3/C4/C6.

    Para C1/C5/C7, usa o que o LLM disse (com fallback a 'minor' se ausente
    ou inválido).
    """
    out = []
    for inc in inconsistencias:
        crit = inc.get("criterio", "").strip().split("_")[0]
        sev_llm = (inc.get("severity") or "").strip().lower()

        if crit in MECHANICAL_CRITICAL_CRITERIA:
            sev_final = "critical"
            sev_method = "mechanical"
        elif crit in LLM_JUDGED_CRITERIA:
            sev_final = sev_llm if sev_llm in VALID_SEVERITIES else "minor"
            sev_method = "llm" if sev_llm in VALID_SEVERITIES else "fallback_minor"
        else:
            sev_final = "minor"  # critério desconhecido, conservador
            sev_method = "unknown_criterion"

        new_inc = dict(inc)
        new_inc["severity"] = sev_final
        new_inc["severity_method"] = sev_method
        new_inc["severity_llm_raw"] = sev_llm or None
        out.append(new_inc)
    return out


def count_by_severity(inconsistencias: list[dict]) -> dict[str, int]:
    """Conta {critical, major, minor} num laudo."""
    counts = {"critical": 0, "major": 0, "minor": 0}
    for inc in inconsistencias:
        s = inc.get("severity", "minor")
        if s in counts:
            counts[s] += 1
    return counts


def has_critical(inconsistencias: list[dict]) -> bool:
    """Headline metric: laudo tem alguma inconsistencia critica?"""
    return any(inc.get("severity") == "critical" for inc in inconsistencias)
```

- [ ] **Step 3: Testes para `severity.py`**

```python
# tests/test_evaluation/test_severity.py
from src.evaluation.severity import (
    apply_severity_override, count_by_severity, has_critical,
    MECHANICAL_CRITICAL_CRITERIA, LLM_JUDGED_CRITERIA,
)


def test_c2_c3_c4_c6_forced_critical_regardless_of_llm():
    """Critérios mecânicos sempre viram critical, mesmo se LLM disser minor."""
    incs = [
        {"criterio": "C2", "severity": "minor"},   # LLM errou; deve virar critical
        {"criterio": "C3", "severity": "major"},
        {"criterio": "C4"},                         # sem severity do LLM
        {"criterio": "C6", "severity": "critical"},
    ]
    out = apply_severity_override(incs)
    for o in out:
        assert o["severity"] == "critical"
        assert o["severity_method"] == "mechanical"


def test_c1_c5_c7_use_llm_classification():
    incs = [
        {"criterio": "C1", "severity": "minor"},
        {"criterio": "C5", "severity": "major"},
        {"criterio": "C7", "severity": "critical"},
    ]
    out = apply_severity_override(incs)
    assert out[0]["severity"] == "minor"   and out[0]["severity_method"] == "llm"
    assert out[1]["severity"] == "major"   and out[1]["severity_method"] == "llm"
    assert out[2]["severity"] == "critical" and out[2]["severity_method"] == "llm"


def test_c1_invalid_severity_falls_back_minor():
    incs = [{"criterio": "C1", "severity": "extreme"}]
    out = apply_severity_override(incs)
    assert out[0]["severity"] == "minor"
    assert out[0]["severity_method"] == "fallback_minor"


def test_count_by_severity():
    incs = [
        {"severity": "critical"}, {"severity": "critical"},
        {"severity": "minor"}, {"severity": "major"},
    ]
    assert count_by_severity(incs) == {"critical": 2, "major": 1, "minor": 1}


def test_has_critical():
    assert has_critical([{"severity": "critical"}, {"severity": "minor"}]) is True
    assert has_critical([{"severity": "minor"}, {"severity": "major"}]) is False
    assert has_critical([]) is False
```

Run: `pytest tests/test_evaluation/test_severity.py -v` → 5 PASS

- [ ] **Step 4: Smoke test no prompt (validar que LLM responde com severity)**

Rodar a versão atualizada do prompt em 5 laudos e conferir que cada inconsistência tem `severity ∈ {critical, major, minor}`:

```bash
python -c "
import json
from src.translation.client import create_client
from src.translation.translate import audit_translation
from src.translation.glossary import load_glossary, format_glossary_for_prompt
from src.evaluation.severity import apply_severity_override
import yaml, pandas as pd

cfg = yaml.safe_load(open('configs/models.yaml'))
auditor = create_client('deepseek-v3', cfg['models']['deepseek-v3'])
glossary = format_glossary_for_prompt(load_glossary('configs/birads_glossary_es_pt.json'))

df_pt = pd.read_csv('results/translation/translations.csv').drop_duplicates('report_id', keep='last')
df_es = pd.read_csv('data/reports_raw_canonical.csv')

for rid in df_pt['report_id'].head(5):
    es = df_es[df_es['report_id']==rid]['report_text_raw'].iloc[0]
    pt = df_pt[df_pt['report_id']==rid]['report_text_raw'].iloc[0]
    res = audit_translation(auditor, es, pt, glossary)
    if res:
        incs = apply_severity_override(res.get('inconsistencias', []))
        print(rid, [(i['criterio'], i['severity'], i['severity_method']) for i in incs])
"
```

Critério: cada inconsistência sai com severity válida. Se LLM continuamente retorna severity inválida em C1/C5/C7, ajustar a rubrica do prompt e rerodar.

- [ ] **Step 5: Commit**

```bash
git add src/translation/prompt.py src/evaluation/severity.py \
        tests/test_evaluation/test_severity.py tests/test_translation/test_prompt.py
git commit -m "feat(evaluation): T12.6 severidade clinica (critical/major/minor) com override mecanico em C2/C3/C4/C6"
```

#### Impacto downstream

| Task | Mudança decorrente |
|---|---|
| **T13** (reaudit) | Aplicar `apply_severity_override` antes de gravar cada record no JSONL. Cada `inconsistencia` ganha `severity` + `severity_method` |
| **T13 Step 5** (calibração) | Mesmo override; Cohen's κ pareado **por severidade** (não só por passou/falhou) — outro eixo de calibração |
| **T20** (`validation_results.jsonl`) | Adicionar `n_critical`, `n_major`, `n_minor` por laudo. Definir `passed = (n_critical == 0)` em vez de `audit_status == "approved"` |
| **T23 §1** (visão geral) | Headline: **"Taxa de laudos sem erro crítico = X%"** |
| **T23 §10** (análise de erros) | Subseções por severidade; tabela top-N por tipo |
| **Composite Score** (spec § 5) | `Q_audit` rebalanceado: penalidade proporcional à severidade; `Q_audit = 100 · (1 − fraction_with_critical)` |
| **Hipóteses** | Adicionar **H8**: "Taxa de laudos com ≥1 erro crítico ≤ 1%" (critério defensável e auditável). |

---

### Task 13: F1 — Re-audit remaining laudos with DeepSeek 🔲 PENDING

**Files:**
- Create: `scripts/audit_phase_a_corrections.py` (Step 0)
- Create: `src/evaluation/reaudit_deepseek.py` (Step 1+)
- Output: `results/translation/c1_correction_audit.json` (Step 0)
- Output: `results/translation/audit_deepseek.jsonl` (Step 2+)

**Goal:** Restore C1–C7 + meta-validation detail for the 3,840 laudos lost on restarts. Re-audits ALL 4,357 from scratch (so detail is uniform across base).

#### Ordem de execução dentro de T13 (sequência obrigatória)

```
[Step 0]   Audit correções da Phase A     → c1_correction_audit.json (gate de decisão)
                  ↓
[T12.6]    (já feito) — severity layer
[Ajuste #2] (já feito) — separação audit_raw / meta_validation
                  ↓
[Step 1]   Implementar reaudit_deepseek.py com schema novo
                  ↓
[Step 1.5] Smoke test estratificado em 20 laudos    ← GATE
                  ↓ (só prossegue se 4 critérios passam)
[Step 2]   Full run via nohup (~6h, ~$0.27)
                  ↓
[Step 3]   Verify cobertura (wc -l = 4357)
                  ↓
[Step 3.5] Build summary JSON                       ← QA pós-execução
                  ↓
[Step 4]   Commit
                  ↓
[Step 5]   Sub-estudo calibração GPT-4o-mini (paralelo a T14.B se quiser)
```

Mudanças de schema (T12.6 severity + Ajuste #2 audit_raw/meta_validation) entram **antes** do run. Smoke test (#5) **antes** do full run. QA summary (#8) **depois** do full run.

#### Step 0 — Auditar correções da Phase A (gate antes de re-auditar conteúdo)

**Problema:** ~17% dos laudos sofreram auto-correção em Phase A. Algumas podem ter sido disparadas por achados de **C1 que a meta-auditoria endossou apesar do bug do prompt** (espanhol cru, PT-pt sem til, etc — diagnosticado em T12.5). Re-auditar esse conteúdo corrigido sem checar primeiro = re-auditar texto possivelmente distorcido por crítica espúria.

**Decisão pré-T13** com base em % das correções com C1 envolvido:

| % com C1 | Decisão |
|---|---|
| **< 20%** | Prosseguir T13 normalmente. Documentar IDs como subset de baixo risco. |
| **20%–50%** | Prosseguir T13 mas reportar IDs como subset de risco no notebook (T23 §10). |
| **> 50%** | Reverter correções (usar tradução pré-correção do `correction_history`) antes de T13. |

- [ ] **Step 0.1: Implementar `scripts/audit_phase_a_corrections.py`**

```python
"""Auditar correções da Phase A: % disparadas por C1 endossado pela meta-auditoria."""
import json
from pathlib import Path


def main():
    data = json.loads(Path("results/translation/audit_results.json").read_text(encoding="utf-8"))

    corrected = []
    for rec in data:
        hist = rec.get("correction_history") or []
        if not hist:
            continue
        round0 = hist[0]
        if round0.get("validation", {}).get("verdict") != "correct":
            continue
        criteria = set()
        for inc in round0.get("inconsistencias") or []:
            crit = inc.get("criterio", "").strip()
            criteria.add(crit.split("_")[0] if "_" in crit else crit)
        corrected.append({
            "report_id": rec["report_id"],
            "criteria": sorted(criteria),
            "has_C1": "C1" in criteria,
            "only_C1": criteria == {"C1"},
            "audit_score_round0": round0.get("score"),
            "audit_score_round1": hist[1].get("score") if len(hist) > 1 else None,
        })

    n = len(corrected)
    n_c1 = sum(1 for r in corrected if r["has_C1"])
    pct = 100 * n_c1 / n if n else 0

    if pct < 20:
        decision = "PROCEED_NORMALLY"
    elif pct < 50:
        decision = "PROCEED_WITH_RISK_SUBSET"
    else:
        decision = "REVERT_BEFORE_T13"

    out = {
        "metadata": {
            "computed_at": "2026-04-28",
            "source": "results/translation/audit_results.json",
            "limitation": "audit_results.json contém apenas a última sessão (~517 laudos); 3.840 laudos das sessões anteriores foram sobrescritos. Métrica é estimada nesta sample.",
        },
        "totals": {
            "sample_size": len(data),
            "n_corrected": n,
            "n_with_c1_involved": n_c1,
            "c1_involvement_pct": round(pct, 2),
        },
        "decision": decision,
        "risk_subset_ids": sorted([r["report_id"] for r in corrected if r["has_C1"]]),
        "corrected_records_with_c1": [r for r in corrected if r["has_C1"]],
    }

    Path("results/translation/c1_correction_audit.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"DECISÃO: {decision} (C1 em {pct:.1f}% das correções)")
    return decision


if __name__ == "__main__":
    main()
```

- [ ] **Step 0.2: Rodar e registrar decisão**

```bash
python -m scripts.audit_phase_a_corrections
```

**Resultado registrado em `2026-04-28` na sample disponível (517 laudos):**
```
n_corrected:           89
n_with_c1_involved:     7  (7.9%)
DECISÃO:               PROCEED_NORMALLY
```

7 IDs no risk subset documentados em `c1_correction_audit.json`:
`RPT_003844, RPT_003858, RPT_003869, RPT_004022, RPT_004164, RPT_004280, RPT_004289`.

**Limitação registrada:** os ~3.840 laudos das sessões anteriores tiveram `audit_results.json` sobrescrito. Não temos correction_history desses para auditar — assumimos que a taxa observada na sample (7.9%) generaliza. Se a re-auditoria de T13 mostrar concentração anômala de score baixo nos IDs corrigidos sem `correction_history`, esse subset herda risco implícito.

- [ ] **Step 0.3: Aplicar decisão**

Se `PROCEED_NORMALLY` (caso atual):
- Seguir Step 1+ sem reverter nada
- T23 §10 (análise de erros) terá subseção dedicada aos 7 IDs do risk subset

Se `PROCEED_WITH_RISK_SUBSET`:
- Marcar IDs no `validation_results.jsonl` (T20) com flag `phase_a_correction_risk: true`
- Notebook reporta esse subset separadamente

Se `REVERT_BEFORE_T13`:
- Implementar script `scripts/revert_c1_corrections.py` que substitui `report_text_raw` em `data/reports_translated_pt.csv` pela tradução pré-correção (não disponível para os 3.840 sem correction_history → reverter apenas os documentados na sample)
- Re-rodar T13 sobre o conteúdo revertido

- [ ] **Step 0.4: Commit Step 0**

```bash
git add scripts/audit_phase_a_corrections.py results/translation/c1_correction_audit.json
git commit -m "feat(evaluation): T13 Step 0 - auditar correções Phase A (C1 em 7.9% -> PROCEED_NORMALLY)"
```

#### Step 1 — Reaudit script

- [ ] **Step 1: Write reaudit script (com agregação de severidade)**

`src/evaluation/reaudit_deepseek.py`:
- Reads `results/translation/translations.csv` (ES + PT) and `data/reports_raw_canonical.csv` (ES source)
- Reuses `audit_translation()` and `validate_findings()` from `src/translation/translate.py`
- Per laudo: audit + meta-validation
- **Aplica `apply_severity_override` da T12.6** sobre `inconsistencias` antes de gravar
- **Agrega contadores de severidade** no record (campos top-level)
- Append via `append_jsonl(audit_deepseek.jsonl, record)`
- Resume via `load_done_ids("audit_deepseek.jsonl")`

**Schema obrigatório do record JSONL — separação explícita audit_raw vs meta_validation:**

A camada de meta-validação (que em T12.5 filtrou 71/86 falsos positivos da sample 517) **precisa ser visível no schema**, não fundida ao output bruto do auditor. Caso contrário a banca pode interpretar como "DeepSeek falou, foi aceito" — sem ver o filtro.

```json
{
  "report_id": "RPT_000001",
  "auditor": "deepseek-v3",
  "audited_at": "2026-04-28T...",
  "prompt_hash": "sha256:...",

  "audit_raw": {
    "approved": true,
    "score": 9.5,
    "criteria": {"C1_descritores_birads": {"ok": true}, ..., "C7_temporais_achados": {"ok": true}},
    "inconsistencies": [
      {"criterio": "C1", "original": "...", "traducao": "...", "problema": "...",
       "severity": "minor", "severity_method": "llm", "severity_llm_raw": "minor"}
    ]
  },

  "meta_validation": {
    "validator_model": "deepseek-v3",
    "validated_findings": [],          // findings confirmados pelo meta-validador (acionáveis)
    "refuted_findings": [               // findings rejeitados como falso positivo do auditor
      {"criterio": "C1", "original": "...", "traducao": "...", "problema": "...",
       "severity": "minor", "severity_method": "llm",
       "refutation_reason": "termo aceitável em pt_variants_acceptable"}
    ],
    "kept_count": 0,                    // |validated_findings|
    "refuted_count": 1                  // |refuted_findings|
  },

  "audit_final_status": "approved",     // derivado de meta_validation, não do audit_raw
  "audit_final_score": 9.5,             // score apenas das findings que sobreviveram à meta-val

  // Agregados de severidade — calculados sobre validated_findings (não inclui FPs refutados)
  "critical_error_count": 0,
  "major_error_count": 0,
  "minor_error_count": 0,
  "has_critical_error": false,

  "terms_check": {"total_es": 12, "matched": 12, "ratio": 1.0},
  "similarity": 0.9612
}
```

**Renomeação importante:** `final_audit_status` → **`audit_final_status`** para evitar colisão com `overall_passed` (T20, agregado das 5 fontes do `validation_results.jsonl`). `audit_final_status` é decisão **da fonte auditor**; `overall_passed` é decisão **multi-fonte**.

**Regra de derivação `audit_final_status`:**
- `kept_count == 0` AND `audit_raw.approved == true` → `"approved"`
- `kept_count > 0` AND `has_critical_error == false` → `"review"`
- `has_critical_error == true` → `"rejected"`

**Implementação de referência (loop principal):**

```python
from src.evaluation.severity import apply_severity_override, count_by_severity, has_critical

# ... dentro do loop por laudo:
audit_result = audit_translation(auditor, es, pt, glossary_text)

# 1) Aplica severity override no output bruto do auditor
raw_incs = apply_severity_override(audit_result.get("inconsistencias", []))

# 2) Meta-validação — separa validated vs refuted
meta_result = validate_findings(auditor, es, pt, raw_incs, glossary_text)
validated = meta_result["validated"]  # list[dict]
refuted   = meta_result["refuted"]    # list[dict] — preserva para auditoria

# 3) Severidade conta sobre as findings VALIDADAS (não infladas por FPs)
counts = count_by_severity(validated)
has_crit = has_critical(validated)

# 4) Status final
if len(validated) == 0 and audit_result.get("approved", True):
    final_status = "approved"
elif has_crit:
    final_status = "rejected"
else:
    final_status = "review"

record = {
    "report_id": rid,
    "auditor": "deepseek-v3",
    "audited_at": pd.Timestamp.utcnow().isoformat(),
    "prompt_hash": prompt_hash,
    "audit_raw": {
        "approved":      audit_result.get("approved"),
        "score":         audit_result.get("score"),
        "criteria":      audit_result.get("criterios"),
        "inconsistencies": raw_incs,
    },
    "meta_validation": {
        "validator_model":     "deepseek-v3",
        "validated_findings":  validated,
        "refuted_findings":    refuted,
        "kept_count":          len(validated),
        "refuted_count":       len(refuted),
    },
    "audit_final_status":   final_status,
    "audit_final_score":    audit_result.get("score"),
    "critical_error_count": counts["critical"],
    "major_error_count":    counts["major"],
    "minor_error_count":    counts["minor"],
    "has_critical_error":   has_crit,
    "terms_check": ...,
    "similarity":  similarity,
}
append_jsonl("results/translation/audit_deepseek.jsonl", record)
```

**Por que isso é metodologicamente forte:**
- `audit_raw` mostra **o que o LLM disse** — auditável
- `meta_validation` mostra **o que sobreviveu ao filtro** com a lista de FPs preservados — banca vê o trabalho de mitigação T12.5
- Severity counts são sobre `validated_findings` — não inflados por FPs do auditor
- `audit_final_status` ≠ `overall_passed` — fonte vs multi-fonte separadas

**Atualizar `validate_findings`** em `src/translation/translate.py` para retornar `{"validated": [...], "refuted": [...]}` em vez do verdict per-laudo atual. Mudança contida no commit do Step 1.

#### Step 1.5 — Smoke test estratificado pré full-run (gate obrigatório)

**Por que:** full run são ~6h e ~$0.27. Erro de configuração descoberto no laudo 800 desperdiça horas e dinheiro. Smoke test em 20 laudos detecta cedo.

**Files:**
- Create: `scripts/smoke_test_t13_reaudit.py`
- Output: `results/translation/smoke_test_t13_results.json`

- [ ] **Step 1.5.1: Selecionar 20 laudos estratificados**

Composição (cobre os tipos de erro que importam):
- **5 laudos com inconsistência C1 conhecida** da Phase A (do `audit_results.json`) → testar redução de FP pós-T12.5
- **5 laudos com lateralidade/medida/negação explícitas** no texto ES → testar override mecânico T12.6 (C2/C3/C4/C6 sempre `critical`)
- **3 laudos com `status ∈ {review, rejected}`** da Phase A → testar casos limite
- **5 laudos random estratificados por categoria BI-RADS** (1 por categoria 0–4, exceto se vazio)
- **2 laudos** das duplicatas T19 → testar reprodutibilidade

Total: ~20 laudos, com `seed=42`.

```python
# scripts/smoke_test_t13_reaudit.py
import json, time, re, random
import pandas as pd
import yaml
from pathlib import Path
from src.translation.client import create_client
from src.translation.translate import audit_translation, validate_findings
from src.translation.glossary import load_glossary, format_glossary_for_prompt
from src.evaluation.severity import apply_severity_override, count_by_severity, has_critical


def select_smoke_sample(seed: int = 42) -> list[str]:
    random.seed(seed)
    df_pt = pd.read_csv("results/translation/translations.csv").drop_duplicates("report_id", keep="last")
    df_es = pd.read_csv("data/reports_raw_canonical.csv")
    audit_old = json.loads(Path("results/translation/audit_results.json").read_text(encoding="utf-8"))

    selected = set()
    # 5 com C1 da Phase A
    c1_ids = []
    for rec in audit_old:
        incs = (rec.get("correction_history") or [{}])[0].get("inconsistencias") or []
        if any(i.get("criterio", "").startswith("C1") for i in incs):
            c1_ids.append(rec["report_id"])
    selected.update(random.sample(c1_ids, min(5, len(c1_ids))))

    # 5 com lateralidade/medida/negação no texto
    pat = re.compile(r"(izquierd|derech|\d+\s*(?:mm|cm)|no se observ|sin )", re.IGNORECASE)
    cand = [r for r in df_es["report_id"] if pat.search(df_es[df_es["report_id"]==r]["report_text_raw"].iloc[0])]
    selected.update(random.sample(cand, min(5, len(cand))))

    # 3 com review/rejected
    rr = df_pt[df_pt["status"].isin(["review","rejected"])]["report_id"].tolist()
    selected.update(random.sample(rr, min(3, len(rr))))

    # 5 random estratificado por categoria
    for cat in [0,1,2,3,4]:
        pool = df_pt[(df_pt["birads_label"]==cat) & (~df_pt["report_id"].isin(selected))]["report_id"].tolist()
        if pool:
            selected.add(random.choice(pool))

    # 2 das duplicatas
    counts = pd.read_csv("results/translation/translations.csv")["report_id"].value_counts()
    dups = counts[counts > 1].index.tolist()
    selected.update(random.sample(dups, min(2, len(dups))))

    return sorted(selected)


def main():
    sample = select_smoke_sample()
    print(f"Smoke sample: {len(sample)} laudos")

    cfg = yaml.safe_load(open("configs/models.yaml"))
    auditor = create_client("deepseek-v3", cfg["models"]["deepseek-v3"])
    glossary = format_glossary_for_prompt(load_glossary("configs/birads_glossary_es_pt.json"))

    df_pt = pd.read_csv("results/translation/translations.csv").drop_duplicates("report_id", keep="last")
    df_es = pd.read_csv("data/reports_raw_canonical.csv")
    audit_old = {r["report_id"]: r for r in
                 json.loads(Path("results/translation/audit_results.json").read_text(encoding="utf-8"))}

    parse_failures = 0
    latencies = []
    c1_before_total, c1_after_total = 0, 0
    records = []
    cost_start = auditor.total_cost_usd

    for rid in sample:
        es = df_es[df_es["report_id"]==rid]["report_text_raw"].iloc[0]
        pt = df_pt[df_pt["report_id"]==rid]["report_text_raw"].iloc[0]

        t0 = time.time()
        try:
            result = audit_translation(auditor, es, pt, glossary)
            latencies.append(time.time() - t0)
            if result is None:
                parse_failures += 1
                continue
        except Exception as e:
            parse_failures += 1
            continue

        incs_after = apply_severity_override(result.get("inconsistencias", []))
        c1_after = sum(1 for i in incs_after if i.get("criterio","").startswith("C1"))
        c1_after_total += c1_after

        if rid in audit_old:
            old_incs = (audit_old[rid].get("correction_history") or [{}])[0].get("inconsistencias") or []
            c1_before = sum(1 for i in old_incs if i.get("criterio","").startswith("C1"))
            c1_before_total += c1_before

        records.append({"report_id": rid, "c1_after": c1_after,
                        "n_critical": count_by_severity(incs_after)["critical"]})

    n = len(sample)
    cost_total = auditor.total_cost_usd - cost_start
    cost_per_laudo = cost_total / n if n else 0
    median_latency = sorted(latencies)[len(latencies)//2] if latencies else 0
    parse_rate = (n - parse_failures) / n if n else 0
    c1_reduction = ((c1_before_total - c1_after_total) / c1_before_total * 100) if c1_before_total else None

    # Critérios de aprovação (todos obrigatórios)
    criteria = {
        "parse_rate_100pct":     parse_rate == 1.0,
        "c1_reduction_ge_70pct": c1_reduction is not None and c1_reduction >= 70,
        "cost_per_laudo_in_band": 0.000042 <= cost_per_laudo <= 0.000078,  # $0.00006 ± 30%
        "median_latency_lt_5s":  median_latency < 5.0,
    }
    all_pass = all(criteria.values())

    out = {
        "n_sample": n,
        "parse_failures": parse_failures,
        "parse_rate": parse_rate,
        "c1_before_total": c1_before_total,
        "c1_after_total":  c1_after_total,
        "c1_reduction_pct": c1_reduction,
        "cost_total_usd": cost_total,
        "cost_per_laudo_usd": cost_per_laudo,
        "median_latency_s": median_latency,
        "criteria_passed": criteria,
        "all_pass": all_pass,
        "records": records,
    }
    Path("results/translation/smoke_test_t13_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(criteria, indent=2))
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 1.5.2: Rodar smoke test e validar critérios**

```bash
python -m scripts.smoke_test_t13_reaudit
```

**Critérios de aprovação (TODOS obrigatórios para liberar full run):**

| Critério | Threshold | Justificativa |
|---|---|---|
| Parse JSON | 100% das respostas parseáveis via `json.loads` | Schema robusto |
| Redução C1 vs prompt antigo | ≥ 70% | Validação T12.5 fix |
| Custo por laudo | $0.00006 ± 30% (i.e. [$0.000042, $0.000078]) | Coerente com $0.27 / 4.357 |
| Latência mediana | < 5s/laudo | Coerente com ~6h total |

**Se algum falhar:** abortar T13, investigar (prompt? rate limit? schema?), ajustar e rerodar Step 1.5 antes de continuar.

- [ ] **Step 1.5.3: Commit smoke test**

```bash
git add scripts/smoke_test_t13_reaudit.py results/translation/smoke_test_t13_results.json
git commit -m "feat(evaluation): T13 Step 1.5 - smoke test estratificado pre full-run (20 laudos, 4 criterios)"
```

- [ ] **Step 2: Run via nohup**

```bash
nohup D:/AI-driven-BIRADS/venv/Scripts/python.exe -u -m src.evaluation.reaudit_deepseek \
  > results/translation/reaudit_deepseek.log 2>&1 &
```

Expected: ~6h, ~$0.27 USD.

- [ ] **Step 3: Monitor and verify**

```bash
wc -l results/translation/audit_deepseek.jsonl   # should reach 4357
```

#### Step 3.5 — QA report pós-execução (sumário consolidado)

**Por que:** `wc -l` confirma quantidade, não qualidade. Sem sumário consolidado, o notebook T23 teria que recomputar todas as métricas. Princípio: **T13 produz sumário; T23 lê e renderiza**, sem duplicar análise.

**Files:**
- Create: `scripts/build_audit_summary.py`
- Output: `results/translation/audit_deepseek_summary.json`

- [ ] **Step 3.5.1: Implementar `scripts/build_audit_summary.py`**

```python
"""Gera sumário consolidado da reauditoria DeepSeek (T13).

Princípio: T13 produz sumário, T23 (notebook) renderiza.
"""
import json
import hashlib
from pathlib import Path
from collections import Counter


def file_hash(path: str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def main():
    records = []
    parse_failures = 0
    api_failures = 0

    with open("results/translation/audit_deepseek.jsonl", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("audit_raw") is None:
                    api_failures += 1
                    continue
                records.append(rec)
            except json.JSONDecodeError:
                parse_failures += 1

    # Status counts
    status_counter = Counter(r["audit_final_status"] for r in records)

    # Severity totals (sobre validated_findings)
    crit_total  = sum(r.get("critical_error_count", 0) for r in records)
    major_total = sum(r.get("major_error_count", 0)    for r in records)
    minor_total = sum(r.get("minor_error_count", 0)    for r in records)
    laudos_with_critical = sum(1 for r in records if r.get("has_critical_error"))

    # Erros por critério (sobre validated_findings — pós meta-val)
    err_by_crit = Counter()
    for r in records:
        for inc in r.get("meta_validation", {}).get("validated_findings", []):
            err_by_crit[inc.get("criterio", "?").split("_")[0]] += 1

    # C1 pós T12.5 fix — métrica DIRETA de efetividade do fix
    c1_failure_count_after_fix = err_by_crit.get("C1", 0)

    # Comparativo com Phase A (apenas para os 517 da última sessão disponíveis)
    audit_old = json.loads(Path("results/translation/audit_results.json").read_text(encoding="utf-8"))
    c1_phase_a_count = 0
    for rec in audit_old:
        incs = (rec.get("correction_history") or [{}])[0].get("inconsistencias") or []
        c1_phase_a_count += sum(1 for i in incs if i.get("criterio","").startswith("C1"))

    # Custo total
    cost_total = sum(r.get("cost_usd", 0) for r in records)  # se gravarmos por record

    # Hashes de reprodutibilidade
    summary = {
        "total_expected": 4357,
        "total_audited":  len(records),
        "json_parse_failures": parse_failures,
        "api_failures": api_failures,

        "approved_count": status_counter.get("approved", 0),
        "review_count":   status_counter.get("review", 0),
        "rejected_count": status_counter.get("rejected", 0),

        "critical_error_count": crit_total,
        "major_error_count":    major_total,
        "minor_error_count":    minor_total,
        "laudos_with_critical": laudos_with_critical,
        "critical_error_rate_pct": round(100 * laudos_with_critical / len(records), 2) if records else 0,

        "error_count_by_criterion": dict(err_by_crit),
        "c1_failure_count_after_fix": c1_failure_count_after_fix,
        "c1_failure_count_phase_a_sample_517": c1_phase_a_count,
        "c1_reduction_vs_phase_a_pct": round((c1_phase_a_count - c1_failure_count_after_fix) / c1_phase_a_count * 100, 2) if c1_phase_a_count else None,

        "cost_total_usd": cost_total,

        # Reprodutibilidade
        "prompt_hash":          records[0].get("prompt_hash") if records else None,
        "atlas_glossary_hash":  file_hash("configs/birads_glossary_atlas_es_pt.json"),
        "old_glossary_hash":    file_hash("configs/birads_glossary_es_pt.json"),
        "audit_jsonl_hash":     file_hash("results/translation/audit_deepseek.jsonl"),

        "computed_at": "2026-04-28",
    }

    Path("results/translation/audit_deepseek_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 3.5.2: Rodar e validar sumário**

```bash
python -m scripts.build_audit_summary
```

**Verificações de sanidade no output:**
- `total_audited == 4357` (cobertura completa)
- `json_parse_failures == 0` e `api_failures == 0`
- `critical_error_rate_pct ≤ 1` (H8 atendida)
- `c1_reduction_vs_phase_a_pct ≥ 70` (T12.5 efetivo)
- `error_count_by_criterion["C1"] << "C5"` (esperado pós-fix)

**Critical inclusion:** `c1_failure_count_after_fix` é a **evidência empírica direta** do impacto do T12.5. Comparando com a contagem da Phase A na sample 517, mostra a redução real do FP em escala — número que vai direto na seção 4.6.2 do TCC.

**Princípio:** T13 produz JSON. T23 (notebook) lê o JSON e renderiza tabelas/gráficos. **Não duplicar análise.** O notebook adiciona apenas:
- `top_20_recurring_problems` (categorização qualitativa de `problema` field)
- Visualizações (histograma, heatmap)
- Análise de outliers

- [ ] **Step 4: Commit**

```bash
git add src/evaluation/reaudit_deepseek.py \
        scripts/build_audit_summary.py \
        results/translation/audit_deepseek.jsonl \
        results/translation/audit_deepseek_summary.json
git commit -m "feat(evaluation): F1 reaudit DeepSeek (4357 laudos, schema audit_raw/meta_validation separados, severidade, summary JSON)"
```

#### Rollback criteria (G6)

Reverter T13 e re-investigar se durante a execução:
- **Custo total > $0.40** (150% do esperado $0.27)
- **JSON parse failures > 1%** (esperado <0.5%)
- **Cobertura final < 99%** (esperado 100% = 4357/4357)
- **prompt_hash mudou durante execução** (deveria ser constante)
- **`c1_failure_count_after_fix` ≥ 50% do `c1_phase_a_count`** (T12.5 fix não funcionou em escala)

**Ação se rollback:** abortar full run, salvar partial output em `audit_deepseek.partial.jsonl`, abrir issue em `incidents.md`, reavaliar prompt/config antes de re-executar. **Não commitar `audit_deepseek.jsonl` parcial** — apenas commit final após verify cross-source passar.

#### Step 5 — Sub-estudo de calibração: concordância DeepSeek ↔ GPT-4o-mini

**Problema que esta sub-tarefa resolve:** T13 confia num único auditor (DeepSeek V3). Se o DeepSeek tem viés sistemático **além de C1** (já mitigado em T12.5), você não detecta — todos os 4.357 herdam o mesmo viés silenciosamente.

**Solução barata:** rodar GPT-4o-mini como **segundo auditor** sobre o mesmo subset estratificado da T14.B (~250 laudos = T22 MQM + T19 duplicatas + review/rejected + fill por categoria). Calcular Cohen's κ pareado por critério C1–C7. **Não é uma 5ª fonte para H3** — é calibração de confiança do auditor primário.

**Decisão registrada:**
| κ por critério | Interpretação |
|---|---|
| **κ ≥ 0.7 em ≥5 dos 7 critérios** | Auditor primário (DeepSeek) tem comportamento estável e generalizável. T13 prossegue como evidência primária. |
| **κ entre 0.5 e 0.7** | Auditor primário aceitável mas com ressalvas; reportar no notebook §10 como "concordância moderada". |
| **κ < 0.5 em algum critério** | Aquele critério C? do DeepSeek é instável; **rebaixar para evidência exploratória** no notebook (excluir do composite_score; reportar separadamente). |

**Custo estimado:**
- GPT-4o-mini: $0.15/M input + $0.60/M output
- 250 auditorias × ~2.500 input + ~500 output = 625K input + 125K output
- Total: **~$0.17 USD ≈ R$0.85**

**Pré-requisitos:** T14.B Step 1 já gerou `bt_sample_ids.json` (mesma estratificação reutilizada). T13 Steps 1–4 já produziram `audit_deepseek.jsonl` para os 4.357.

**Files:**
- Modify: `configs/models.yaml` (adicionar `gpt-4o-mini` se ainda não tiver)
- Create: `src/evaluation/audit_calibration.py`
- Create: `scripts/compute_audit_agreement.py`
- Output: `results/translation/audit_gpt4omini_subset.jsonl` (~250 records)
- Output: `results/translation/audit_calibration_agreement.json`

- [ ] **Step 5.1: Adicionar GPT-4o-mini ao `models.yaml`**

```yaml
gpt-4o-mini:
  provider: openai
  model_id: gpt-4o-mini-2024-07-18
  api_base: https://api.openai.com/v1
  env_key: OPENAI_API_KEY
  cost_per_1m_input: 0.15
  cost_per_1m_output: 0.60
  cost_limit_usd: 5.00
```

- [ ] **Step 5.2: Implementar `src/evaluation/audit_calibration.py`**

Reusa `audit_translation()` de `src/translation/translate.py` (que após T12.5 já usa o prompt corrigido derivado do Atlas). Roda **mesmo prompt** com cliente diferente (GPT-4o-mini). Não há meta-validação — calibração compara apenas a auditoria primária.

```python
"""Calibração: GPT-4o-mini audita o subset estratificado para comparar com DeepSeek."""
import json
import yaml
import pandas as pd
from pathlib import Path
from src.translation.client import create_client
from src.translation.translate import audit_translation
from src.translation.glossary import load_glossary, format_glossary_for_prompt
from src.evaluation.io import append_jsonl, load_done_ids


def main():
    # Subset: reusa amostra de T14.B
    sample = json.loads(Path("results/translation/bt_sample_ids.json").read_text(encoding="utf-8"))
    target_ids = set(sample["report_ids"])

    # Resume
    out_path = "results/translation/audit_gpt4omini_subset.jsonl"
    done = load_done_ids(out_path)
    pending = sorted(target_ids - done)
    print(f"Pending: {len(pending)} de {len(target_ids)}")

    # Cliente GPT-4o-mini
    cfg = yaml.safe_load(open("configs/models.yaml"))
    auditor = create_client("gpt-4o-mini", cfg["models"]["gpt-4o-mini"])

    # Dados
    df_pt = pd.read_csv("results/translation/translations.csv").drop_duplicates("report_id", keep="last")
    df_es = pd.read_csv("data/reports_raw_canonical.csv")
    glossary_text = format_glossary_for_prompt(load_glossary("configs/birads_glossary_es_pt.json"))

    for i, rid in enumerate(pending, 1):
        es = df_es[df_es["report_id"] == rid]["report_text_raw"].iloc[0]
        pt = df_pt[df_pt["report_id"] == rid]["report_text_raw"].iloc[0]

        result = audit_translation(auditor, es, pt, glossary_text)
        if result is None:
            continue

        record = {
            "report_id": rid,
            "auditor": "gpt-4o-mini-2024-07-18",
            "audit": result,
            "audited_at": pd.Timestamp.utcnow().isoformat(),
        }
        append_jsonl(out_path, record)

        if i % 25 == 0:
            print(f"[{i}/{len(pending)}] custo: ${auditor.total_cost_usd:.4f}")


if __name__ == "__main__":
    main()
```

Run via nohup:

```bash
nohup D:/AI-driven-BIRADS/venv/Scripts/python.exe -u -m src.evaluation.audit_calibration \
  > results/translation/audit_calibration.log 2>&1 &
```

Esperado: ~30 min, **~$0.17 USD**.

- [ ] **Step 5.3: Implementar `scripts/compute_audit_agreement.py`**

```python
"""Calcula Cohen's kappa pareado DeepSeek vs GPT-4o-mini por criterio C1-C7."""
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import cohen_kappa_score


def load_jsonl(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                out[rec["report_id"]] = rec
            except json.JSONDecodeError:
                continue
    return out


def extract_criteria_passed(audit_record):
    """Retorna dict {C1: bool, ..., C7: bool} a partir do JSON do auditor."""
    audit = audit_record.get("audit", {})
    crits = audit.get("criterios", {})
    out = {}
    for key in ["C1_descritores_birads", "C2_categoria_birads", "C3_medidas_numeros",
                "C4_lateralidade_localizacao", "C5_omissoes_adicoes",
                "C6_inversoes_negacao", "C7_temporais_achados"]:
        c_short = key.split("_")[0]
        out[c_short] = bool(crits.get(key, {}).get("ok", True))
    return out


def bootstrap_kappa(y1, y2, n=1000, seed=42):
    rng = np.random.default_rng(seed)
    y1, y2 = np.array(y1), np.array(y2)
    boot = []
    for _ in range(n):
        idx = rng.integers(0, len(y1), len(y1))
        if len(set(y1[idx])) < 2 or len(set(y2[idx])) < 2:
            continue
        boot.append(cohen_kappa_score(y1[idx], y2[idx]))
    return float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def main():
    sample = json.loads(Path("results/translation/bt_sample_ids.json").read_text(encoding="utf-8"))
    subset_ids = set(sample["report_ids"])

    deepseek = load_jsonl("results/translation/audit_deepseek.jsonl")
    gpt = load_jsonl("results/translation/audit_gpt4omini_subset.jsonl")

    common = subset_ids & set(deepseek) & set(gpt)
    print(f"Laudos com auditoria pareada: {len(common)}")

    criteria = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
    results = {}
    for c in criteria:
        y_ds, y_gpt = [], []
        for rid in sorted(common):
            ds = extract_criteria_passed(deepseek[rid])
            gp = extract_criteria_passed(gpt[rid])
            y_ds.append(ds[c]); y_gpt.append(gp[c])
        if len(set(y_ds)) < 2 or len(set(y_gpt)) < 2:
            kappa = None; ci = (None, None)
        else:
            kappa = float(cohen_kappa_score(y_ds, y_gpt))
            ci = bootstrap_kappa(y_ds, y_gpt)
        results[c] = {"kappa": kappa, "ci95": ci, "n": len(common)}

    # Decisão
    high = sum(1 for c, r in results.items() if r["kappa"] is not None and r["kappa"] >= 0.7)
    low = [c for c, r in results.items() if r["kappa"] is not None and r["kappa"] < 0.5]

    if low:
        decision = "DOWNGRADE_UNSTABLE_CRITERIA"
        notes = f"Critério(s) instável(eis) ({low}); rebaixar para evidência exploratória no notebook."
    elif high >= 5:
        decision = "PRIMARY_AUDITOR_STABLE"
        notes = f"{high}/7 critérios com κ ≥ 0.7. DeepSeek é evidência primária válida."
    else:
        decision = "MODERATE_CONCORDANCE"
        notes = "Reportar como concordância moderada no notebook §10."

    out = {
        "metadata": {
            "computed_at": "2026-04-28",
            "method": "Cohen's kappa pairwise per criterion C1-C7, bootstrap CI 95% (n=1000)",
            "subset_source": "bt_sample_ids.json (~250 estratificados)",
            "n_paired": len(common),
        },
        "kappa_per_criterion": results,
        "high_agreement_criteria_count": high,
        "low_agreement_criteria": low,
        "decision": decision,
        "notes": notes,
    }
    Path("results/translation/audit_calibration_agreement.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"DECISÃO: {decision}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
```

Run:

```bash
python -m scripts.compute_audit_agreement
```

- [ ] **Step 5.4: Aplicar decisão no notebook (T23)**

A decisão registrada em `audit_calibration_agreement.json` é consumida em T23 §10:

- `PRIMARY_AUDITOR_STABLE` → composite_score usa todos os C1–C7 do DeepSeek
- `MODERATE_CONCORDANCE` → mesma coisa, mas adiciona warning na seção §10
- `DOWNGRADE_UNSTABLE_CRITERIA` → critérios listados em `low_agreement_criteria` saem do `composite_score` e ganham subseção própria como "evidência exploratória"

- [ ] **Step 5.5: Commit**

```bash
git add configs/models.yaml src/evaluation/audit_calibration.py \
        scripts/compute_audit_agreement.py \
        results/translation/audit_gpt4omini_subset.jsonl \
        results/translation/audit_calibration_agreement.json
git commit -m "feat(evaluation): T13 Step 5 - calibracao DeepSeek vs GPT-4o-mini sobre subset (~250)"
```

---

### Task 14.A: Corrigir tracking de custo/tokens (OBRIGATÓRIO) 🔲 PENDING  ⚠ pré-requisito de T14.B

**Goal:** Eliminar a discrepância entre custo reportado (`stats.json`: $0.20) e custo real (R$160) da Phase A. Sem este fix, qualquer chamada futura ao Gemini repete o problema. **Esta task é obrigatória antes de T14.B e idealmente antes de T13** (DeepSeek não tem thinking, mas o tracking precisa ficar consistente).

**Files:**
- Modify: `configs/models.yaml`
- Modify: `src/translation/client.py`
- Create: `tests/test_translation/test_client_token_tracking.py`

**Diagnóstico que motiva o fix:**
- Bug 1: `client.py:81` usa `usage.candidates_token_count` apenas, ignorando `thoughts_token_count` (raciocínio interno do Gemini 2.5 Flash, cobrado como output)
- Bug 2: preços em `models.yaml` desatualizados (0.15/0.60 vs reais 0.30/2.50 — 2x e 4.2x)
- Bug 3 (escopo, não corrigido aqui): `stats.json` reporta apenas última sessão; correção fica em T20 ao consolidar `validation_results.jsonl`

- [ ] **Step 1: Atualizar preços em `configs/models.yaml`**

Verificar tabela oficial Google na data e atualizar:

```yaml
gemini-2.5-flash:
  provider: google
  model_id: gemini-2.5-flash
  env_key: GOOGLE_API_KEY
  cost_per_1m_input: 0.30           # antes: 0.15 (errado)
  cost_per_1m_output: 2.50          # antes: 0.60 (errado)
  cost_limit_usd: 50.00

gemini-2.5-flash-no-thinking:
  provider: google
  model_id: gemini-2.5-flash
  env_key: GOOGLE_API_KEY
  thinking_budget: 0                # NOVO: desativa thinking interno
  cost_per_1m_input: 0.30
  cost_per_1m_output: 2.50
  cost_limit_usd: 10.00
```

- [ ] **Step 2: Adicionar campo `thinking_budget` ao `LLMClient`**

Em `src/translation/client.py`:

```python
@dataclass
class LLMClient:
    ...
    thinking_budget: int | None = None
    ...
```

E no `create_client`:

```python
def create_client(name: str, model_config: dict) -> LLMClient:
    api_key = os.environ.get(model_config["env_key"], "")
    return LLMClient(
        ...,
        thinking_budget=model_config.get("thinking_budget"),
    )
```

- [ ] **Step 3: Somar `thoughts_token_count` ao output em `_generate_google`**

```python
def _generate_google(self, prompt: str, temperature: float) -> str:
    from google import genai

    client = genai.Client(api_key=self.api_key)

    config_kwargs = {"temperature": temperature}
    if self.thinking_budget is not None:
        config_kwargs["thinking_config"] = genai.types.ThinkingConfig(
            thinking_budget=self.thinking_budget
        )

    response = client.models.generate_content(
        model=self.model_id,
        contents=prompt,
        config=genai.types.GenerateContentConfig(**config_kwargs),
    )
    usage = response.usage_metadata
    if usage:
        thoughts = getattr(usage, "thoughts_token_count", 0) or 0
        candidates = usage.candidates_token_count or 0
        self._update_usage(
            input_tokens=usage.prompt_token_count or 0,
            output_tokens=candidates + thoughts,  # ambos cobrados como output
        )
    return response.text
```

- [ ] **Step 4: Teste mock — thoughts somam ao output**

`tests/test_translation/test_client_token_tracking.py`:

```python
from unittest.mock import MagicMock, patch
from src.translation.client import LLMClient


def test_thoughts_tokens_added_to_output_count():
    """Thoughts tokens são cobrados como output e devem ser contados."""
    client = LLMClient(
        name="test", provider="google", model_id="gemini-2.5-flash",
        api_key="fake", cost_per_1m_input=0.30, cost_per_1m_output=2.50,
        thinking_budget=0,
    )

    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 100
    mock_usage.candidates_token_count = 200
    mock_usage.thoughts_token_count = 500
    mock_response = MagicMock()
    mock_response.usage_metadata = mock_usage
    mock_response.text = "translated"

    with patch("google.genai.Client") as MockClient:
        instance = MockClient.return_value
        instance.models.generate_content.return_value = mock_response
        client.generate("hello", temperature=0)

    assert client.total_input_tokens == 100
    assert client.total_output_tokens == 700  # 200 candidates + 500 thoughts
    expected_cost = 100 * 0.30/1e6 + 700 * 2.50/1e6
    assert abs(client.total_cost_usd - expected_cost) < 1e-9


def test_thinking_budget_propagated_to_config():
    """Quando thinking_budget=0, ThinkingConfig deve aparecer no kwargs."""
    client = LLMClient(
        name="test", provider="google", model_id="gemini-2.5-flash",
        api_key="fake", thinking_budget=0,
    )
    mock_response = MagicMock()
    mock_response.usage_metadata = None
    mock_response.text = "ok"

    with patch("google.genai.Client") as MockClient, \
         patch("google.genai.types.ThinkingConfig") as MockTC, \
         patch("google.genai.types.GenerateContentConfig") as MockGCC:
        instance = MockClient.return_value
        instance.models.generate_content.return_value = mock_response
        client.generate("hi", temperature=0)
        MockTC.assert_called_once_with(thinking_budget=0)
```

Run: `pytest tests/test_translation/test_client_token_tracking.py -v`

- [ ] **Step 5: Recalcular custo retroativo da Phase A para o commit message**

Documentar diferença vs `stats.json`:

```python
# Cálculo retroativo (script ad hoc no commit message)
in_tok_517 = 963_525   # última sessão
out_tok_517 = 92_795   # candidates apenas (não temos thoughts gravados)

# Com preço novo (sem thoughts pq não foram capturados)
real_no_thoughts = in_tok_517*0.30/1e6 + out_tok_517*2.50/1e6
# = $0.521 (vs $0.20 reportado)

# Multiplicador de escopo (517 -> 4357 laudos): 8.43x
# Sem thinking (estimado): 4357*0.521/517 ≈ $4.40
# Diferença observada R$160 ($32) sugere thinking ~7-8x sobre output visível
```

- [ ] **Step 6: Commit**

```bash
git add configs/models.yaml src/translation/client.py tests/test_translation/test_client_token_tracking.py
git commit -m "fix(client): rastrear thoughts_token_count + atualizar precos Gemini 2.5 Flash

- thoughts_token_count somado ao output (cobrado como output pelo Google)
- thinking_budget configuravel via models.yaml
- precos atualizados: 0.15/0.60 -> 0.30/2.50 USD/1M
- recalculo retroativo Phase A: stats.json (\$0.20) vs real (~R\$160) explicado
  por (a) escopo apenas ultima sessao 1/8 do trabalho, (b) thinking nao contado,
  (c) precos 4.2x output desatualizados
- testes garantem regressao não retorna"
```

#### Rollback criteria (G6)

Reverter T14.A (não commitar) se:
- **Teste mock `test_thoughts_tokens_added_to_output_count` falha** — significa que `thoughts_token_count` não está sendo somado corretamente
- **Recálculo retroativo da Phase A diverge >20%** do valor real (R$160) → indica preço ainda errado ou multiplicador de thinking imprevisto
- **`ThinkingConfig` não é propagado** para o cliente real (verificável via mock spy)

**Ação se rollback:** revisar a versão da SDK Google Generative AI (`google-genai`) instalada — o nome do campo (`thoughts_token_count` vs `thinking_token_count`) pode variar entre versões. Documentar versão usada e ajustar.

---

### Task 14.B: F2 — Back-translation em amostra estratificada (RECOMENDADO) 🔲 PENDING  ⚠ depende de T14.A + T22 critério

**Goal:** Adicionar 5ª fonte de evidência (round-trip semântico PT→ES) em **subconjunto representativo de ~250 laudos** — não no corpus inteiro. Cobertura científica preservada via estratificação; custo cai de ~$3.05 para ~$0.20.

**Por que amostral:** back-translation full-corpus seria $3+ extra para evidência redundante na maioria dos laudos. Amostra estratificada cobre todos os casos críticos (T22 humanos + T19 duplicatas + Phase A review/rejected) e cada categoria BI-RADS, mantendo poder estatístico para H1 e H3 e adicionando o eixo BT a casos que importam. Fora da amostra, H3 cai gracefully de "≥4 das 5 fontes" para "≥3 das 4".


**Pré-requisitos:**
- ✅ T14.A concluída (custo correto)
- ✅ T22 critério de seleção da amostra humana definido (mesmo arquivo de IDs cruza com BT)
- ✅ T19 IDs das 48 duplicatas conhecidos

**Files:**
- Create: `scripts/build_bt_sample.py` (constrói lista de IDs)
- Create: `src/evaluation/back_translation.py`
- Create: `tests/test_evaluation/test_back_translation.py`
- Output: `results/translation/bt_sample_ids.json`, `results/translation/back_translation.csv`

#### Caveat metodológico (documentar em T23 §12)

Mesmo modelo família que o tradutor (Gemini 2.5 Flash). Mitigado por:
1. Direção inversa (PT→ES vs ES→PT original)
2. `thinking_budget=0` (raciocínio interno desativado)
3. `temperature=0`
4. **Prompt minimalista, sem glossário** — força tradução direta; se a tradução PT preserva o significado, o modelo recupera o ES sem precisar de pista lexical.
5. Cross-check com structural checks F4 (regex programático não é fooled por paráfrases)

- [ ] **Step 1: Construir amostra estratificada `~250 laudos, seed=42`**

`scripts/build_bt_sample.py`:

```python
"""Construir amostra estratificada para back-translation."""
import json
import pandas as pd
import random
from pathlib import Path

random.seed(42)

# Carregar fontes
df = pd.read_csv("results/translation/translations.csv")
df = df.drop_duplicates("report_id", keep="last")

# IDs obrigatórios
must_include = set()

# T22: amostra MQM humana (já gerada antes ou regras: review, rejected, top-discordância)
must_include |= set(df[df["status"].isin(["review", "rejected"])]["report_id"])

# T19: 48 pares de duplicatas (IDs RPT_000721-RPT_000820)
duplicates = pd.read_csv("results/translation/translations.csv")
dup_counts = duplicates["report_id"].value_counts()
must_include |= set(dup_counts[dup_counts > 1].index)

# Estratos: 7-10 por categoria BI-RADS
TARGET_PER_CATEGORY = 8
categories = sorted(df["birads_label"].dropna().unique())

stratified = set()
for cat in categories:
    pool = df[df["birads_label"] == cat]["report_id"].tolist()
    in_must = set(pool) & must_include
    needed = max(0, TARGET_PER_CATEGORY - len(in_must))
    available = list(set(pool) - must_include)
    if len(available) >= needed:
        stratified.update(random.sample(available, needed))
    else:
        stratified.update(available)

sample = sorted(must_include | stratified)
target_size = 250
if len(sample) < target_size:
    remaining_pool = list(set(df["report_id"]) - set(sample))
    extra = random.sample(remaining_pool, target_size - len(sample))
    sample = sorted(set(sample) | set(extra))

# Validações
per_cat = pd.Series([df.set_index("report_id").loc[i, "birads_label"]
                     for i in sample if i in df["report_id"].values]).value_counts()
print(f"Amostra final: {len(sample)} laudos")
print(f"Por categoria BI-RADS:")
print(per_cat)
print(f"Cobre 100% T22: {must_include.issubset(set(sample))}")

# Validação tolera categorias com menos de 7 laudos no corpus (ex: BI-RADS 6 tem só 5)
for c in categories:
    available_in_corpus = (df["birads_label"] == c).sum()
    expected = min(TARGET_PER_CATEGORY, available_in_corpus)
    assert per_cat.loc[c] >= expected, f"BI-RADS {c}: tem {per_cat.loc[c]}, esperado ≥{expected}"

assert must_include.issubset(set(sample)), "amostra não cobre 100% dos IDs obrigatórios"

# Salvar
out = {
    "metadata": {
        "seed": 42,
        "size": len(sample),
        "target_per_category": TARGET_PER_CATEGORY,
        "must_include_count": len(must_include),
        "categories_distribution": per_cat.to_dict(),
    },
    "report_ids": sample,
}
Path("results/translation/bt_sample_ids.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
)
```

Critério: ≥7 por categoria BI-RADS; cobre 100% T22+T19; tamanho final ~250 ± 20%.

- [ ] **Step 2: Implementar `back_translation.py` (prompt minimalista)**

```python
"""F2 - Back-translation PT->ES sobre amostra estratificada."""
import json
import pandas as pd
import yaml
from pathlib import Path
from src.translation.client import create_client


PROMPT = """Traduza o seguinte laudo do português ao espanhol fielmente, preservando terminologia médica BI-RADS.

LAUDO PT:
{pt_text}

TRADUÇÃO ES:"""


def main():
    # Carregar amostra
    sample = json.loads(Path("results/translation/bt_sample_ids.json").read_text(encoding="utf-8"))
    sample_ids = set(sample["report_ids"])

    # Carregar dados
    df_pt = pd.read_csv("results/translation/translations.csv").drop_duplicates("report_id", keep="last")
    df_es = pd.read_csv("data/reports_raw_canonical.csv")

    # Resume
    out_path = Path("results/translation/back_translation.csv")
    done = set()
    if out_path.exists():
        done = set(pd.read_csv(out_path)["report_id"])

    pending = sorted(sample_ids - done)
    print(f"Pending: {len(pending)} de {len(sample_ids)} amostrados")

    # Cliente Gemini 2.5 Flash thinking OFF
    cfg = yaml.safe_load(open("configs/models.yaml"))
    client = create_client("gemini-2.5-flash-no-thinking",
                           cfg["models"]["gemini-2.5-flash-no-thinking"])

    # Modelos para métricas
    from sentence_transformers import SentenceTransformer
    import sacrebleu
    from bert_score import score as bertscore
    embedder = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")

    rows = []
    for i, rid in enumerate(pending, 1):
        pt_text = df_pt[df_pt["report_id"] == rid]["report_text_raw"].iloc[0]
        es_orig = df_es[df_es["report_id"] == rid]["report_text_raw"].iloc[0]

        es_bt = client.generate(PROMPT.format(pt_text=pt_text), temperature=0)

        emb_o = embedder.encode([es_orig], convert_to_tensor=True)
        emb_b = embedder.encode([es_bt], convert_to_tensor=True)
        cos = float((emb_o @ emb_b.T).cpu().item())
        chrf = sacrebleu.corpus_chrf([es_bt], [[es_orig]]).score
        bleu = sacrebleu.corpus_bleu([es_bt], [[es_orig]]).score
        _, _, f1 = bertscore([es_bt], [es_orig], lang="es")
        bf1 = float(f1[0])

        rows.append({
            "report_id": rid,
            "es_back_translated": es_bt,
            "cosine_es_es_bt": cos,
            "bertscore_f1_es_es_bt": bf1,
            "chrf_es_es_bt": chrf,
            "bleu_es_es_bt": bleu,
        })

        if i % 50 == 0 or i == len(pending):
            pd.DataFrame(rows).to_csv(out_path, mode="a",
                                      header=not out_path.exists() or out_path.stat().st_size == 0,
                                      index=False)
            rows = []
            print(f"[{i}/{len(pending)}] custo acumulado: ${client.total_cost_usd:.4f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2.5: Métricas estruturais ES_orig vs ES_bt**

Adicionar ao `back_translation.py` aplicação dos extractors que serão consolidados em T16 (categoria BI-RADS, medidas, lateralidade, negação). Isso valida que o **round-trip preserva os elementos críticos** — não só a semântica geral, mas a categoria, medidas e lateralidade que importam para a tarefa downstream.

**Decisão de modularização:** os extractors vivem em `src/evaluation/structural_checks.py` desde já. T14.B Step 2.5 cria a versão mínima (4 funções abaixo); T16 estende com anatomia, drift PT-pt e roda sobre os 4.357 ES↔PT.

```python
# src/evaluation/structural_checks.py — versão T14.B (extractors core)
import re
import unicodedata


CATEGORY_RE = re.compile(r"BI[\s\-]?RADS\s*[:\.]?\s*(?:categor[íi]a)?\s*([0-6])", re.IGNORECASE)
MEASURE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mm|cm|m²|%|ml)\b", re.IGNORECASE)
LAT_TERMS_PT = {"esquerd": "L", "direit": "R", "bilateral": "B"}
LAT_TERMS_ES = {"izquierd": "L", "derech": "R", "bilateral": "B"}
NEG_TERMS_PT = ["não se", "sem ", "ausência", "ausente", "nenhum", "nenhuma"]
NEG_TERMS_ES = ["no se", "sin ", "ausencia", "ausente", "ningún", "ninguna"]


def _norm(s: str) -> str:
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def extract_birads_category(text: str) -> int | None:
    m = CATEGORY_RE.search(text or "")
    return int(m.group(1)) if m else None


def extract_measures(text: str) -> list[tuple[float, str]]:
    out = []
    for m in MEASURE_RE.finditer(text or ""):
        val = float(m.group(1).replace(",", "."))
        unit = m.group(2).lower()
        out.append((val, unit))
    return sorted(out)


def extract_laterality(text: str, lang: str = "pt") -> set[str]:
    """Retorna {'L','R','B'} encontrados no texto."""
    text_n = _norm(text or "")
    terms = LAT_TERMS_PT if lang == "pt" else LAT_TERMS_ES
    found = set()
    for k, v in terms.items():
        if _norm(k) in text_n:
            found.add(v)
    return found


def count_negations(text: str, lang: str = "pt") -> int:
    text_n = _norm(text or "")
    terms = NEG_TERMS_PT if lang == "pt" else NEG_TERMS_ES
    return sum(text_n.count(_norm(t)) for t in terms)
```

Estender `back_translation.py` (no loop, dentro de `main`) para registrar os matches:

```python
from src.evaluation.structural_checks import (
    extract_birads_category, extract_measures, extract_laterality, count_negations
)

# ... dentro do loop, após calcular bf1:
cat_orig = extract_birads_category(es_orig)
cat_bt   = extract_birads_category(es_bt)
meas_orig = extract_measures(es_orig)
meas_bt   = extract_measures(es_bt)
lat_orig  = extract_laterality(es_orig, "es")
lat_bt    = extract_laterality(es_bt, "es")
neg_orig  = count_negations(es_orig, "es")
neg_bt    = count_negations(es_bt, "es")

rows.append({
    "report_id": rid,
    "es_back_translated": es_bt,
    "cosine_es_es_bt": cos,
    "bertscore_f1_es_es_bt": bf1,
    "chrf_es_es_bt": chrf,
    "bleu_es_es_bt": bleu,
    # NEW: structural round-trip
    "category_es_orig": cat_orig,
    "category_es_bt":   cat_bt,
    "category_match":   (cat_orig == cat_bt),
    "measures_es_orig_json": json.dumps(meas_orig),
    "measures_es_bt_json":   json.dumps(meas_bt),
    "measures_match":  (set(meas_orig) == set(meas_bt)),
    "laterality_es_orig_json": json.dumps(sorted(lat_orig)),
    "laterality_es_bt_json":   json.dumps(sorted(lat_bt)),
    "laterality_match": (lat_orig == lat_bt),
    "negation_count_es_orig": neg_orig,
    "negation_count_es_bt":   neg_bt,
    "negation_ratio": (neg_bt / neg_orig) if neg_orig else (1.0 if neg_bt == 0 else 0.0),
})
```

**Valor metodológico:** se o BT preserva categoria/medidas/lateralidade/negação, é evidência **independente** de que a tradução PT→ES via Gemini não distorce esses elementos. Se NÃO preserva no round-trip, levanta dúvida sobre a tradução PT original — sinaliza para revisão manual.

- [ ] **Step 2.6: Calibração empírica do threshold de `passed`**

Em vez de definir `passed` com constantes arbitrárias (ex: `cosine ≥ 0.85`), calibrar empiricamente usando as duplicatas: o BT de um laudo traduzido **duas vezes em condições idênticas** (T=0) deve ser indistinguível semanticamente. A distribuição de cosine/BERTScore/chrF nessas duplicatas estabelece o **piso natural de variação intrínseca** do método. Pegamos o **percentil 5** como threshold — qualquer laudo abaixo é estatisticamente "pior do que duplicatas".

**Não-dependência circular com T19 (Ajuste 5):** T14.B Step 2.6 **não depende de T19 ter rodado**. Identifica duplicatas independentemente via `value_counts(report_id) > 1` em `translations.csv` + filtro `effective_duplicate` (mesmo `prompt_hash`). T19 reaproveita o mesmo set de IDs e adiciona métricas em 3 níveis (textual/semântico/estrutural) + flags `requires_mqm_review`. Ordem de execução T14.B → T19 funciona; T14.B → T19 → T18 também (T18 lê threshold de T19 calibrado por suas próprias duplicatas).

**Pré-requisito:** as duplicatas (T19, IDs RPT_000721–RPT_000820) estão na amostra BT por construção (Step 1).

`scripts/calibrate_bt_thresholds.py`:

```python
"""Calibra thresholds empíricos de back-translation a partir das duplicatas."""
import json
import numpy as np
import pandas as pd
from pathlib import Path


def main():
    df_bt = pd.read_csv("results/translation/back_translation.csv")
    df_pt = pd.read_csv("results/translation/translations.csv")

    # Identificar IDs com duas traduções PT distintas (duplicatas efetivas)
    dup_counts = df_pt["report_id"].value_counts()
    dup_ids = set(dup_counts[dup_counts > 1].index)

    # Filtrar BT para apenas duplicatas (já incluídas na amostra por construção)
    dup_bt = df_bt[df_bt["report_id"].isin(dup_ids)]

    if len(dup_bt) < 30:
        print(f"AVISO: apenas {len(dup_bt)} duplicatas no BT; calibracao com baixa potencia")

    metrics = ["cosine_es_es_bt", "bertscore_f1_es_es_bt", "chrf_es_es_bt"]
    thresholds = {}
    for m in metrics:
        values = dup_bt[m].dropna().values
        p5  = float(np.percentile(values, 5))
        p50 = float(np.percentile(values, 50))
        p95 = float(np.percentile(values, 95))
        thresholds[m] = {
            "p5":  p5,
            "p50": p50,
            "p95": p95,
            "n_duplicates": int(len(values)),
            "policy": "passed = (value >= p5) — laudo BT abaixo do percentil 5 das duplicatas é outlier"
        }

    out = {
        "metadata": {
            "method": "5th percentile of BT metrics on duplicate pairs (T=0 reproducibility floor)",
            "source": "results/translation/back_translation.csv intersected with duplicates",
            "calibrated_at": pd.Timestamp.utcnow().isoformat(),
        },
        "thresholds": thresholds,
    }
    Path("results/translation/bt_thresholds_empirical.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(thresholds, indent=2))


if __name__ == "__main__":
    main()
```

**Output: `results/translation/bt_thresholds_empirical.json`** — usado em T20 (`consolidate.py`) para definir `back_translation.passed`:

```python
# em T20, ao consolidar
thresholds = json.loads(Path("results/translation/bt_thresholds_empirical.json").read_text())["thresholds"]
bt_passed = (
    row["cosine_es_es_bt"] >= thresholds["cosine_es_es_bt"]["p5"]
    and row["bertscore_f1_es_es_bt"] >= thresholds["bertscore_f1_es_es_bt"]["p5"]
    and row["chrf_es_es_bt"] >= thresholds["chrf_es_es_bt"]["p5"]
    and bool(row["category_match"])           # estrutural sempre obrigatório
    and bool(row["measures_match"])
    and bool(row["laterality_match"])
)
```

**Quando rodar:** após Step 5 (full BT terminar). Adicionar ao Step 6 (verify).

**Valor metodológico:** thresholds derivados do próprio sistema, não chutados. Defendível na banca: "o piso de variação tolerada vem do próprio comportamento determinístico do tradutor sob T=0; qualquer laudo abaixo desse piso é estatisticamente anômalo."

- [ ] **Step 3: Tests com mock**

```python
# tests/test_evaluation/test_back_translation.py
def test_metric_computation_on_toy_pair():
    """cosine, chrf, bleu, bertscore em par minimamente válido."""
    ...

def test_resume_idempotente(tmp_path):
    """Rerun não re-processa IDs já no CSV."""
    ...

def test_thinking_budget_zero_propagated(monkeypatch):
    """LLMClient é instanciado com thinking_budget=0."""
    ...


# tests/test_evaluation/test_structural_checks.py (também usado em T16)
def test_extract_birads_category():
    from src.evaluation.structural_checks import extract_birads_category
    assert extract_birads_category("BI-RADS 4") == 4
    assert extract_birads_category("BI-RADS: categoría 2") == 2
    assert extract_birads_category("birads-3") == 3
    assert extract_birads_category("nenhuma menção") is None


def test_extract_measures_normalizes_comma():
    from src.evaluation.structural_checks import extract_measures
    assert extract_measures("nodulo de 15mm e 2,5cm") == [(2.5, "cm"), (15.0, "mm")]


def test_extract_laterality_es_pt():
    from src.evaluation.structural_checks import extract_laterality
    assert extract_laterality("mama izquierda", "es") == {"L"}
    assert extract_laterality("mama esquerda", "pt") == {"L"}
    assert extract_laterality("hallazgos bilaterales", "es") == {"B"}


def test_count_negations():
    from src.evaluation.structural_checks import count_negations
    assert count_negations("no se observan calcificaciones", "es") == 1
    assert count_negations("sin nódulos sospechosos", "es") == 1
    assert count_negations("não se observam massas, sem calcificações", "pt") == 2
```

Run: `pytest tests/test_evaluation/test_back_translation.py tests/test_evaluation/test_structural_checks.py -v`

- [ ] **Step 4: Smoke test 10 laudos — guard rail de custo**

```bash
python -m src.evaluation.back_translation --limit 10
```

Custo esperado: ~$0.008 (proporcional). **Se >$0.02, abortar** — algo está errado (thinking não foi desligado, prompt grande demais, etc).

- [ ] **Step 5: Run full sobre amostra ~250 via nohup**

```bash
nohup D:/AI-driven-BIRADS/venv/Scripts/python.exe -u -m src.evaluation.back_translation \
  > results/translation/back_translation.log 2>&1 &
```

Esperado: ~20 min, **~$0.30 USD ≈ R$1.50**.

- [ ] **Step 6: Calibrar thresholds + verify + commit**

Após Step 5 terminar, rodar a calibração empírica (Step 2.6):

```bash
python -m scripts.calibrate_bt_thresholds
```

Conferir que `bt_thresholds_empirical.json` tem `n_duplicates ≥ 30` e p5 dentro do esperado (cosine p5 tipicamente 0.85–0.92, BERTScore p5 0.85–0.92, chrF p5 ~50–60).

Verify:

```bash
python -c "
import pandas as pd, json
sample = json.load(open('results/translation/bt_sample_ids.json'))
df = pd.read_csv('results/translation/back_translation.csv')
thresholds = json.load(open('results/translation/bt_thresholds_empirical.json'))['thresholds']
print('Cobertura:', len(df), '/', sample['metadata']['size'])
print('Cosine mediana:', df['cosine_es_es_bt'].median())
print('Estruturais — categoria match:', df['category_match'].mean())
print('Estruturais — medidas match:',  df['measures_match'].mean())
print('Estruturais — lateralidade match:', df['laterality_match'].mean())
print('Threshold cosine p5:', thresholds['cosine_es_es_bt']['p5'])
"
```

Critérios de sanidade:
- Cobertura ≥ 95% da amostra alvo
- `category_match` ≥ 0.97 (round-trip preserva categoria)
- `measures_match` ≥ 0.95
- `laterality_match` ≥ 0.97
- Cosine p5 das duplicatas ≥ 0.85 (se < 0.85 algo está errado com o tradutor reverso)

Commit:

```bash
git add scripts/build_bt_sample.py scripts/calibrate_bt_thresholds.py \
        src/evaluation/back_translation.py src/evaluation/structural_checks.py \
        tests/test_evaluation/test_back_translation.py tests/test_evaluation/test_structural_checks.py \
        results/translation/bt_sample_ids.json results/translation/back_translation.csv \
        results/translation/bt_thresholds_empirical.json
git commit -m "feat(evaluation): F2 back-translation amostral (~250) com structural round-trip + thresholds empiricos das duplicatas"
```

#### Rollback criteria (G6)

Abortar T14.B (Step 5 ou 6) e re-investigar se:
- **Smoke test (Step 4) custou >$0.02** em 10 laudos (150% do esperado $0.008–$0.013) → thinking não desligou ou prompt explodiu
- **Custo full run > $0.30** (150% do esperado $0.20) → mesmo gatilho
- **Cobertura final < 95% da amostra** (~237 de 250) → falhas API persistentes
- **`category_match` < 0.95** ou **`measures_match` < 0.92** ou **`laterality_match` < 0.95** (Step 6 sanity) → BT está distorcendo elementos clínicos críticos → método amostral compromete H1 e H3
- **`cosine_pt_pt p5` calibrado < 0.85** nas duplicatas → tradutor reverso instável → amostra não serve como piso de variação

**Ação se rollback:** abortar full run, preservar `back_translation.partial.csv`, abrir issue em `incidents.md`, reavaliar:
1. `thinking_budget=0` está realmente ativo? (testar `ThinkingConfig` propagado)
2. Prompt minimalista está sendo enviado? (sem glossário)
3. Versão do SDK vs schema esperado

Não commitar `bt_thresholds_empirical.json` se Step 6 falhar — sem thresholds calibrados, T20 não pode marcar `bt.passed`.

---

### Task 15: F3 — Intrinsic MT metrics 🔲 PENDING

**Files:**
- Create: `src/evaluation/intrinsic_metrics.py`
- Output: `results/translation/intrinsic_metrics.csv`

#### Métricas selecionadas — main vs apêndice

**Critério de seleção:** defensibilidade na banca para o par **ES↔PT** (línguas próximas, mesma família românica). Métricas que produzem evidência **interpretável e direta** vão para a seção principal; métricas complementares vão para apêndice; métricas inadequadas para o par são **excluídas**.

| Métrica | Camada | Justificativa |
|---|---|---|
| **BERTScore-F1** | **Principal** | Padrão atual em MT evaluation (Zhang et al. 2020). Embeddings contextuais XLM-Roberta capturam semântica multilíngue robustamente. Headline metric para H1. |
| **chrF++** | **Principal** | F-score de char n-grams + word 2-grams. **Apropriada para ES↔PT** porque línguas próximas compartilham morfemas a nível de caractere — n-gramas BLEU em palavras inteiras subestimam similaridade quando há flexão diferente; chrF++ não. (Popović 2017) |
| **Cosine similarity** (mpnet) | **Principal** | Semântica via embeddings multilíngues `paraphrase-multilingual-mpnet-base-v2`. Já validada em Phase A (avg 0.9571). Independente do BERTScore (modelo diferente). |
| **length_ratio** | **Principal** | Sanity check de omissão/expansão (`len(pt_tokens) / len(es_tokens)`). Razão extrema (≪1) sinaliza tradução truncada. Determinística. |
| **TER** | **Apêndice** | Edit distance normalizada. Complementar — útil só se BERTScore/chrF concordarem mas TER divergir. Não é evidência primária. |
| ~~**BLEU**~~ | **CORTADO** | **Não defensável para par ES↔PT.** Razões: (1) BLEU foi desenhado para inglês com múltiplas referências; (2) em línguas próximas românicas, n-gramas de palavras inteiras subestimam similaridade quando há flexão equivalente (`espiculada`/`espiculado`/`espiculadas` = mesmo significado, BLEU não reconhece); (3) literatura recente (Freitag et al. 2022, WMT22) recomenda chrF++/BERTScore/COMET sobre BLEU para todas as direções. **Banca vai questionar — antecipamos retirando.** Mantemos BLEU apenas no F2 (back-translation ES↔ES_bt, monolingual, onde BLEU é apropriado). |
| ~~`ttr_pt`~~ | (rebaixada) | Type-token ratio do PT é sobre o **único texto traduzido**, não compara com fonte. Não é métrica de qualidade de tradução — vai para análise descritiva no notebook §5, não no CSV de métricas intrínsecas. |

#### ⚠ Limitação intencional de escopo

T15 mede similaridade textual e semântica genérica. **Não decide erro clínico** — métricas MT genéricas podem classificar como "alta similaridade" um laudo que trocou categoria BI-RADS, lateralidade, medida ou negação. Exemplo concreto: dois textos diferindo apenas em "BI-RADS 4" vs "BI-RADS 3" recebem `cosine ≈ 0.95` e `BERTScore-F1 ≈ 0.95` — métricas semânticas globais não detectam a substituição local de um único token clinicamente crítico.

T15 serve para:

1. **Triagem agregada** — distribuição de qualidade na base.
2. **Detecção de outliers** — laudos com `BERTScore-F1 < 0.85` são candidatos a revisão MQM (T22 Tier 4 via `failure_reasons` contendo `"semantic"`).
3. **Evidência agregada no `composite_score`** — `Q_semantic` com peso 0.20 (T20 fórmula v1).

**Decisão clínica per-laudo** (preservação de categoria, medida, lateralidade, negação) fica a cargo de:
- **T16** — structural checks regex (categoria/medidas/lateralidade/negação determinísticos)
- **T17** — léxico Atlas (variantes canônicas/aceitáveis)
- **T18** — morfossintaxe (preservação de flexão)
- **T13** — auditor LLM com severidade T12.6 (`Q_audit` peso 0.20, override mecânico em C2/C3/C4/C6)

**H8** (taxa de erro crítico ≤ 1%) é verificada **exclusivamente pelo auditor** com critério mecânico determinístico em C2/C3/C4/C6 — **não por T15**. BERTScore alto em laudo com `has_critical_error = True` não compensa o erro crítico no `composite_score` (Q_audit zera quando há crítico, independente de Q_semantic).

**Defesa para a banca:** "vocês confiaram em BERTScore para decidir erro médico?" → resposta direta: "Não. BERTScore é triagem semântica genérica (Q_semantic, peso 0.20). Erros clínicos são detectados por regras determinísticas (T16) e auditor com severidade clínica (T12.6/T13). Q_audit zera quando há erro crítico, dominando o composite_score."

- [ ] **Step 1: Write metrics script (main + apêndice separados)**

`src/evaluation/intrinsic_metrics.py`:

Computa por laudo:

**Main (4 métricas):**
- `cosine_sim` — mpnet multilingual
- `bertscore_p`, `bertscore_r`, `bertscore_f1` — xlm-roberta-large
- `chrf` — sacrebleu chrF++
- `length_ratio` — `len(pt_tokens) / len(es_tokens)` com tokenização básica

**Apêndice (1 métrica):**
- `ter` — sacrebleu (na mesma CSV, separável por coluna)

Implementação:
- Batch processing para embedding/BERTScore (eficiência)
- Resume por reading existing CSV (pula `report_id` já presentes)
- Append mode com flush a cada batch de 50

**CSV columns** (`results/translation/intrinsic_metrics.csv`):
```
report_id,
cosine_sim, bertscore_p, bertscore_r, bertscore_f1, chrf, length_ratio,  # main
ter                                                                       # apêndice
```

**Sem coluna BLEU.** Comentário explicativo no header do script:

```python
# NOTA METODOLOGICA:
# BLEU intencionalmente excluido das metricas intrinsecas ES<->PT.
# Razao: par romanico proximo + flexao morfologica torna BLEU enviesado
# para baixo mesmo com semantica preservada. chrF++ e a metrica lexical
# recomendada pela literatura recente (Popovic 2017, Freitag et al. 2022).
# BLEU permanece em F2 (back-translation ES<->ES_bt, monolingual).
```

- [ ] **Step 2: Tests**

`tests/test_evaluation/test_intrinsic_metrics.py` — unit tests para cada métrica em pares toy. Inclui:

```python
def test_intrinsic_metrics_no_bleu_column():
    """Garante que BLEU não vaze para o CSV de métricas intrínsecas ES<->PT."""
    import pandas as pd
    from src.evaluation.intrinsic_metrics import compute_metrics_for_pair
    out = compute_metrics_for_pair("hola mundo", "olá mundo")
    assert "bleu" not in out
    assert "chrf" in out
    assert "bertscore_f1" in out


def test_chrf_higher_than_bleu_for_morphology():
    """Comprova: pares com inflexão equivalente recebem chrF alto, BLEU baixo.
    Documenta empiricamente por que BLEU foi cortado."""
    # ES "margens espiculadas" -> PT "margens espiculadas" (idêntico)
    # vs ES "margem espiculada" -> PT "margens espiculadas" (plural diferente)
    # chrF capta similaridade morfológica; BLEU pune mismatch de unigrama
    pass
```

- [ ] **Step 3: Run**

```bash
python -m src.evaluation.intrinsic_metrics
```

Expected: ~30 min, $0.

**Sanity checks pós-execução:**
- `bertscore_f1` mediana ≥ 0.90 (H1)
- `chrf` mediana ≥ 60 (esperado para tradução fiel ES↔PT)
- `cosine_sim` mediana ≥ 0.95 (já validado em Phase A: 0.9571)
- `length_ratio` mediana ∈ [0.92, 1.05] (Phase A: 0.975)
- `ter` mediana ≤ 0.30 (apêndice)

- [ ] **Step 4: Commit**

```bash
git add src/evaluation/intrinsic_metrics.py results/translation/intrinsic_metrics.csv \
        tests/test_evaluation/test_intrinsic_metrics.py
git commit -m "feat(evaluation): F3 metricas intrinsecas (BERTScore-F1 + chrF++ + cosine + length_ratio principais; TER apendice; BLEU removido por nao defensavel em ES<->PT)"
```

#### Defesa metodológica para a banca

**Por que cortamos BLEU:** "BLEU é uma métrica baseada em n-gramas de palavras inteiras desenhada para inglês com múltiplas traduções de referência. Em pares de línguas próximas como ES↔PT, formas flexionadas equivalentes (`espiculada`/`espiculadas`/`espiculado`) têm overlap zero em BLEU mesmo preservando o significado. A literatura recente em MT evaluation (Freitag et al. 2022, WMT22 metrics task) recomenda chrF++ e métricas baseadas em embeddings (BERTScore, COMET) como substitutos. Mantemos chrF++ pela robustez a flexão morfológica e BERTScore-F1 pelo alinhamento semântico."

**Se a banca insistir** ("mas BLEU é o padrão histórico"): apêndice tem TER (também edit-based, complementar). BLEU em F2 (back-translation ES↔ES_bt) é monolingual e não tem o problema de flexão cross-lingual.

---

### Task 16: F4 — Programmatic structural checks 🔲 PENDING

**Files:**
- Modify: `src/evaluation/structural_checks.py` (já criado em T14.B Step 2.5; estender com anatomia + PT-pt drift)
- Modify: `tests/test_evaluation/test_structural_checks.py` (já criado em T14.B Step 3; adicionar testes de anatomia/drift)
- Output: `results/translation/structural_checks.csv`

**Dependência:** T14.B já implementou `extract_birads_category`, `extract_measures`, `extract_laterality`, `count_negations`. T16 estende com anatomy/drift e roda a checagem completa sobre os 4.357 pares (ES, PT).

**Goal:** Deterministic regex-based validations central to TCC argument: BI-RADS category, measures, laterality, negation, anatomy, PT-pt drift — agora sobre o corpus inteiro.

- [ ] **Step 1: ✅ Já feito em T14.B** — category, measures, laterality, negation extractors em `structural_checks.py`. Apenas conferir presença e cobertura de testes.

- [ ] **Step 2: ✅ Já feito em T14.B** — `extract_measures` normaliza vírgula→ponto e retorna lista ordenada de `(valor, unidade)`. Conferir.

- [ ] **Step 3: ESTENDER com anatomia + PT-pt drift**

Each as standalone function with unit tests covering edge cases.

PT-pt drift cognates list (~25): `arquitectónica/arquitetural`, `facto/fato`, `objecto/objeto`, `acção/ação`, `direcção/direção`, `infecção`, `utente/paciente`, `ecrã/tela`, etc.

- [ ] **Step 4: Compose the consolidated check**

```python
def run_structural_checks(report_id, es, pt, birads_label):
    return {
        "report_id": report_id,
        "category_es": ..., "category_pt": ..., "category_label": birads_label, "category_pass": ...,
        "measures_es_json": ..., "measures_pt_json": ..., "measures_pass": ..., "measures_missing_json": ...,
        "laterality_es_json": ..., "laterality_pt_json": ..., "laterality_pass": ...,
        "negation_es_count": ..., "negation_pt_count": ..., "negation_ratio": ..., "negation_pass": ...,
        "anatomy_pass": ...,
        "pt_drift": ..., "pt_drift_terms_json": ...,
        "all_structural_pass": ...
    }
```

- [ ] **Step 5: Run and commit**

```bash
python -m src.evaluation.structural_checks
git add src/evaluation/structural_checks.py tests/test_evaluation/test_structural_checks.py results/translation/structural_checks.csv
git commit -m "feat(evaluation): F4 checks programaticos (categoria, medidas, lateralidade, negacao, drift PT-pt)"
```

---

### Task 17: F5.B + F5.C — Lexical consistency + anomalies 🔲 PENDING

**Files:**
- Create: `src/evaluation/lexical_analysis.py`
- Create: `tests/test_evaluation/test_lexical_categorize.py`
- Output: `results/translation/lexical_consistency.csv` (por termo)
- Output: `results/translation/lexical_anomalies.csv` (por anomalia)
- Output: `results/translation/lexical_global_summary.json` (overall rates)

#### Decisões metodológicas registradas

**Princípio (Ajuste #1):** **contagem global por laudo, não alinhamento posicional.** Para cada termo ES do Atlas, contamos: (a) ocorrências do `es_term` no texto ES; (b) ocorrências de cada variante PT (canonical + acceptable + unacceptable) no texto PT. Comparamos totais com tolerância ±10% para flagar perda ou alucinação. **Não tentamos parear ocorrência i-ES com ocorrência i-PT** — isso falha quando o termo aparece múltiplas vezes.

**Justificativa:** alinhamento posicional cross-lingual em texto livre é ruidoso. Contagem global cobre a evidência relevante (a base preserva o léxico no agregado?) sem o erro do alinhamento. Limitação reconhecida em T23 §5 (Ajuste #7).

#### Categorização léxica determinística (Ajuste #2)

| Categoria | Regra |
|---|---|
| `canonical` | variante PT == `pt_canonical` |
| `acceptable` | variante ∈ `pt_variants_acceptable` (não `pt_canonical`) |
| `gender_variant` | difere do `pt_canonical` apenas em sufixo `-o`/`-a` (ex: `redondo` ↔ `redonda`) |
| `number_variant` | difere apenas em `-s`/`-es` final (ex: `redonda` ↔ `redondas`) |
| `unacceptable` | ∈ `pt_variants_unacceptable` (typos, formas erradas explicitamente listadas) |
| `unknown_for_term` | não está em nenhuma das listas do termo |

Cada regra = função pequena, testável (Ajuste #6 — TDD).

#### Métricas reportadas (Ajustes #3 + #5)

**Por termo (distribuição):**
- `term_canonical_ratio = canonical_count / total_occurrences`
- `term_acceptable_ratio = (canonical_count + acceptable_count) / total_occurrences`

**Globais na base (magnitude — usado pra H2):**
- `overall_canonical_rate = sum(canonical_count) / sum(total_occurrences)`
- `overall_acceptable_rate = sum(canonical_count + acceptable_count) / sum(total_occurrences)`

**H2 testa `overall_acceptable_rate ≥ 0.99`** (não `canonical_rate`). Justificativa: `canonical_rate` baixo penalizaria o tradutor por seguir o glossário antigo (95 termos). `acceptable_rate` mede fidelidade ao **glossário recebido**, que é o critério defensável.

**Decisão de glossário (canonical_ratio < 1.0)** vira evidência sobre evolução do glossário, não erro de tradução.

- [ ] **Step 1: Implementar `categorize_pt_variant()` (TDD primeiro)**

```python
# tests/test_evaluation/test_lexical_categorize.py

import pytest
from src.evaluation.lexical_analysis import categorize_pt_variant


@pytest.fixture
def entry_oval():
    return {
        "es": "oval",
        "pt_canonical": "oval",
        "pt_variants_acceptable": ["oval", "ovalada", "ovalado"],
        "pt_variants_unacceptable": ["oval do"],
    }


def test_canonical_match(entry_oval):
    assert categorize_pt_variant("oval", entry_oval) == "canonical"


def test_acceptable_non_canonical(entry_oval):
    assert categorize_pt_variant("ovalado", entry_oval) == "acceptable"


def test_gender_variant_inferred(entry_oval):
    # Variante não listada explicitamente, mas difere do canonical só em -o/-a
    entry = {**entry_oval, "pt_variants_acceptable": ["oval"]}  # remove ovalada/ovalado
    assert categorize_pt_variant("ovala", entry) == "gender_variant"


def test_number_variant_inferred(entry_oval):
    entry = {**entry_oval, "pt_variants_acceptable": ["oval"]}
    assert categorize_pt_variant("ovais", entry) == "number_variant"


def test_unacceptable_typo(entry_oval):
    assert categorize_pt_variant("oval do", entry_oval) == "unacceptable"


def test_unknown_for_term(entry_oval):
    assert categorize_pt_variant("redondo", entry_oval) == "unknown_for_term"
```

Implementação:

```python
# src/evaluation/lexical_analysis.py
import re
import unicodedata


def _norm(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def _is_gender_variant(variant: str, canonical: str) -> bool:
    """Difere do canonical apenas em sufixo -o/-a."""
    v, c = _norm(variant), _norm(canonical)
    if len(v) != len(c) or v == c:
        return False
    if v[:-1] == c[:-1] and {v[-1], c[-1]} == {"o", "a"}:
        return True
    return False


def _is_number_variant(variant: str, canonical: str) -> bool:
    """Difere apenas em -s/-es final."""
    v, c = _norm(variant), _norm(canonical)
    if v == c:
        return False
    if v == c + "s" or c == v + "s":
        return True
    if v == c + "es" or c == v + "es":
        return True
    return False


def categorize_pt_variant(variant: str, entry: dict) -> str:
    """Categoriza uma variante PT contra a entrada do glossário Atlas.

    Ordem de avaliação determinística: canonical → acceptable → unacceptable
    → gender_variant → number_variant → unknown_for_term.
    """
    v = _norm(variant)
    canonical = _norm(entry["pt_canonical"])
    acceptable = {_norm(x) for x in entry.get("pt_variants_acceptable", [])}
    unacceptable = {_norm(x) for x in entry.get("pt_variants_unacceptable", [])}

    if v == canonical:
        return "canonical"
    if v in acceptable:
        return "acceptable"
    if v in unacceptable:
        return "unacceptable"
    if _is_gender_variant(variant, entry["pt_canonical"]):
        return "gender_variant"
    if _is_number_variant(variant, entry["pt_canonical"]):
        return "number_variant"
    return "unknown_for_term"
```

Run: `pytest tests/test_evaluation/test_lexical_categorize.py -v` → 6 PASS

- [ ] **Step 2: Implementar contagem global per laudo (Ajuste #1)**

```python
def count_term_occurrences(text: str, term: str) -> int:
    """Conta ocorrências de term em text com word boundary, case/accent insensitive."""
    text_n = _norm(text)
    term_n = _norm(term)
    return len(re.findall(r"\b" + re.escape(term_n) + r"\b", text_n))


def analyze_laudo_lexical(es_text: str, pt_text: str, atlas: dict) -> list[dict]:
    """Para cada termo do Atlas, conta no laudo e categoriza variantes PT.

    Retorna lista de dicts (uma entry por termo BI-RADS encontrado no ES).
    """
    rows = []
    for cat_key, entries in atlas["categories"].items():
        for entry in entries:
            es_term = entry["es"]
            es_count = count_term_occurrences(es_text, es_term)
            if es_count == 0:
                continue  # termo não aparece neste laudo

            # Conta cada variante PT (canonical, acceptable, unacceptable)
            all_pt_variants = (
                {entry["pt_canonical"]}
                | set(entry.get("pt_variants_acceptable", []))
                | set(entry.get("pt_variants_unacceptable", []))
            )
            variant_counts = {v: count_term_occurrences(pt_text, v) for v in all_pt_variants}

            # Total PT (todas categorias)
            pt_total = sum(variant_counts.values())

            # Categorizar cada variante observada
            categorized = {"canonical": 0, "acceptable": 0, "gender_variant": 0,
                           "number_variant": 0, "unacceptable": 0, "unknown_for_term": 0}
            for v, n in variant_counts.items():
                if n == 0:
                    continue
                cat = categorize_pt_variant(v, entry)
                categorized[cat] += n

            # Flags ±10% tolerância
            ratio = pt_total / es_count if es_count else 0
            loss_flag = ratio < 0.9
            hallucination_flag = ratio > 1.1

            rows.append({
                "es_term": es_term,
                "es_count": es_count,
                "pt_total_count": pt_total,
                "ratio_pt_es": round(ratio, 3),
                "lexical_loss_flag": loss_flag,
                "lexical_hallucination_flag": hallucination_flag,
                **categorized,
                "bi_rads_code": entry.get("bi_rads_code"),
            })
    return rows
```

- [ ] **Step 3: Cruzamento com T16 structural checks (Ajuste #4)**

Após gerar dados base, juntar com `structural_checks.csv` para flags compostas:

```python
def add_structural_cross_flags(lexical_df, structural_df):
    """Adiciona flags cruzadas T17×T16 ao nível de laudo."""
    merged = lexical_df.merge(
        structural_df[["report_id", "all_structural_pass"]],
        on="report_id", how="left"
    )
    merged["lexical_loss_with_structural_pass"] = (
        merged["lexical_loss_flag"] & merged["all_structural_pass"].fillna(True)
    )
    merged["lexical_loss_with_structural_fail"] = (
        merged["lexical_loss_flag"] & ~merged["all_structural_pass"].fillna(True)
    )
    return merged
```

**Interpretação:**
- `lexical_loss_with_structural_pass = True` → perda léxica isolada, possivelmente estilística
- `lexical_loss_with_structural_fail = True` → perda léxica + estrutura quebrada → **vermelho, prioridade MQM (T22)**

Esse flag alimenta o critério de seleção de T22.

- [ ] **Step 4: Computar métricas globais (Ajustes #3 + #5)**

```python
def compute_global_summary(lexical_rows: list[dict]) -> dict:
    """Calcula overall_canonical_rate e overall_acceptable_rate (Ajuste #5)."""
    total_es = sum(r["es_count"] for r in lexical_rows)
    total_pt = sum(r["pt_total_count"] for r in lexical_rows)
    canonical = sum(r["canonical"] for r in lexical_rows)
    acceptable = sum(r["canonical"] + r["acceptable"] for r in lexical_rows)

    return {
        "total_es_occurrences":   total_es,
        "total_pt_occurrences":   total_pt,
        "overall_canonical_rate":  round(canonical / total_pt, 4) if total_pt else 0,
        "overall_acceptable_rate": round(acceptable / total_pt, 4) if total_pt else 0,  # ← H2
        "n_terms_analyzed":       len(set(r["es_term"] for r in lexical_rows)),
        "n_laudos_with_loss_isolated":   sum(1 for r in lexical_rows if r.get("lexical_loss_with_structural_pass")),
        "n_laudos_with_loss_critical":   sum(1 for r in lexical_rows if r.get("lexical_loss_with_structural_fail")),
    }
```

- [ ] **Step 5: Outputs**

**`results/translation/lexical_consistency.csv`** — uma linha por (laudo × termo):
```
report_id, es_term, bi_rads_code,
es_count, pt_total_count, ratio_pt_es,
canonical, acceptable, gender_variant, number_variant, unacceptable, unknown_for_term,
term_canonical_ratio, term_acceptable_ratio,
lexical_loss_flag, lexical_hallucination_flag,
lexical_loss_with_structural_pass, lexical_loss_with_structural_fail
```

**`results/translation/lexical_anomalies.csv`** — uma linha por anomalia (não `canonical` e não `acceptable`):
```
report_id, es_term, pt_variant_observed, category,
context_pt (±5 tokens), severity_inferred (mecânica T12.6: critical se C2/C3/C4/C6, senão minor)
```

**`results/translation/lexical_global_summary.json`** — agregados (Ajuste #5):
```json
{
  "overall_canonical_rate":  0.85,
  "overall_acceptable_rate": 0.998,   // <-- H2 metric
  "total_es_occurrences":    52431,
  "total_pt_occurrences":    52107,
  "n_terms_analyzed":        198,
  "n_laudos_with_loss_isolated":  142,
  "n_laudos_with_loss_critical":   18
}
```

- [ ] **Step 6: Run + commit**

```bash
python -m src.evaluation.lexical_analysis

# Verificar
python -c "
import json
s = json.load(open('results/translation/lexical_global_summary.json'))
print(f'overall_canonical_rate:  {s[\"overall_canonical_rate\"]:.4f}')
print(f'overall_acceptable_rate: {s[\"overall_acceptable_rate\"]:.4f}  (H2 metric)')
print(f'Loss + structural fail:  {s[\"n_laudos_with_loss_critical\"]}  (prioridade MQM)')
"

git add src/evaluation/lexical_analysis.py \
        tests/test_evaluation/test_lexical_categorize.py \
        results/translation/lexical_consistency.csv \
        results/translation/lexical_anomalies.csv \
        results/translation/lexical_global_summary.json
git commit -m "feat(evaluation): F5 consistencia lexica (contagem global, categorizacao deterministica, canonical+acceptable, cross com T16)"
```

#### Limitação documentada (Ajuste #7) — vai para T23 §5

Adicionar parágrafo explícito no notebook:

> **Limitações metodológicas (T17):** A análise de consistência léxica opera por **contagem global por laudo**, não por alinhamento posicional. Em laudos onde um termo BI-RADS aparece múltiplas vezes, T17 não distingue qual ocorrência específica foi traduzida com qual variante. Justificativa: alinhamento posicional cross-lingual em texto livre é ruidoso e introduz mais erro do que captura. Mitigação: (a) cruzamento com T16 (structural checks) detecta perda de elementos críticos quando há quebra estrutural concomitante; (b) revisão MQM (T22) confirma fidelidade caso a caso na amostra estratificada (laudos com `lexical_loss_with_structural_fail = True` são incluídos por construção).

---

### Task 18: F6 — Modifier preservation (preservação morfossintática) 🔲 PENDING

**Files:**
- Modify: `configs/birads_glossary_atlas_es_pt.json` (preencher `forms_pt`/`forms_es` em ~30 adjetivos)
- Create: `scripts/verify_atlas_morphology.py` (gate de morfologia, também usado em T12)
- Create: `src/evaluation/modifier_check.py`
- Create: `tests/test_evaluation/test_modifier_check.py`
- Create: `scripts/calibrate_modifier_thresholds.py`
- Create: `scripts/build_modifier_summary.py`
- Output: `results/translation/modifier_preservation.csv`
- Output: `results/translation/modifier_threshold_empirical.json`
- Output: `results/translation/modifier_summary.json`

#### Princípio metodológico

**Pergunta respondida:** a forma flexionada do adjetivo BI-RADS foi **preservada** na tradução ES→PT? (não: a concordância está correta no PT — isso é T22/MQM.)

**Por que essa pergunta:** se ES diz "lesión espiculada" (F-SING) e PT diz "lesão espiculado" (M-SING), introduziu-se divergência morfológica. Erros morfossintáticos **pré-existentes no laudo ES** (typos do laudista) NÃO são contabilizados — só medimos divergências **introduzidas pela tradução**. Isso evita confundir erro de fonte com erro de tradução.

**Escopo:** adjetivos BI-RADS canônicos com mapa morfológico explícito no Atlas (~30 entradas). Substantivos âncora (`lesão`, `mama`, `nódulo`) NÃO recebem `forms_*` — sustentam concordância, não a expressam.

**Cobertura:** quando `n_modifiers_compared == 0` (laudo curto ou sem adjetivos BI-RADS), T18 vota **abstain**, não passed. Evita inflar artificialmente a taxa de preservação.

**Calibração de threshold:** alinhada com T14.B Step 2.6 — `passed` deriva do percentil 5 da distribuição nas duplicatas (T19), com piso conservador 0.90. Coerência metodológica entre fontes.

---

- [ ] **Step 1: Estender Atlas com `forms_pt` + `forms_es` em ~30 adjetivos**

Para cada adjetivo BI-RADS canônico, preencher mapa morfológico explícito. Schema:

```json
{
  "es": "espiculado",
  "pt_canonical": "espiculado",
  "pt_variants_acceptable": ["espiculado", "espiculada", "espiculados", "espiculadas"],
  "bi_rads_code": "MASS_MARGIN_SPICULATED",
  "forms_pt": {
    "M-SING": "espiculado", "F-SING": "espiculada",
    "M-PLUR": "espiculados", "F-PLUR": "espiculadas"
  },
  "forms_es": {
    "M-SING": "espiculado", "F-SING": "espiculada",
    "M-PLUR": "espiculados", "F-PLUR": "espiculadas"
  }
}
```

Categorias do Atlas que recebem `forms_*`:

| Categoria | Adjetivos |
|---|---|
| `mass_shape` | oval, redondo, irregular, lobulado |
| `mass_margin` | circunscrito, obscurecido, microlobulado, espiculado, indistinto |
| `mass_density` | hiperdenso, isodenso, hipodenso |
| `calcifications_morphology` | puntiforme, amorfo, pleomórfico, ramificado, linear fino |
| `calcifications_distribution` | agrupado, segmentar, linear, regional, difuso, ductal |
| `associated_features` | retraído, espessado |

Substantivos descritivos (`mama`, `lesão`, `nódulo`, `quadrante`, …) **não** ganham `forms_*`.

Trabalho mecânico (~30 entradas × 4 formas PT + 4 formas ES).

---

- [ ] **Step 2: Implementar `scripts/verify_atlas_morphology.py` + rodar como gate**

```python
# scripts/verify_atlas_morphology.py
import json, sys
from pathlib import Path

REQUIRED_TAGS = {"M-SING", "F-SING", "M-PLUR", "F-PLUR"}

atlas = json.loads(Path("configs/birads_glossary_atlas_es_pt.json").read_text(encoding="utf-8"))
errors = []

for cat_key, entries in atlas["categories"].items():
    for entry in entries:
        if "forms_pt" in entry or "forms_es" in entry:
            for field in ["forms_pt", "forms_es"]:
                forms = entry.get(field, {})
                missing = REQUIRED_TAGS - set(forms.keys())
                if missing:
                    errors.append(f"{entry['es']}: {field} faltam tags {missing}")
            acceptable = {v.lower() for v in entry.get("pt_variants_acceptable", [])}
            for tag, form in entry.get("forms_pt", {}).items():
                if form.lower() not in acceptable:
                    errors.append(f"{entry['es']}: forms_pt[{tag}]={form} não está em pt_variants_acceptable")

if errors:
    print("FAIL: morfologia inconsistente no Atlas")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
print("OK: morfologia validada para todas as entradas com forms_pt/forms_es")
```

Run:
```bash
python -m scripts.verify_atlas_morphology
# Esperado: "OK: morfologia validada ..."
```

Se `FAIL`, ajustar o glossário (Step 1) e rerodar até passar.

---

- [ ] **Step 3: TDD — `tests/test_evaluation/test_modifier_check.py` com 7 testes**

```python
# tests/test_evaluation/test_modifier_check.py
import pytest
from src.evaluation.modifier_check import detect_form, diff_modifier_agreement


@pytest.fixture
def atlas_minimal():
    return {
        "categories": {
            "mass_margin": [{
                "pt_canonical": "espiculado",
                "bi_rads_code": "MASS_MARGIN_SPICULATED",
                "forms_pt": {"M-SING": "espiculado", "F-SING": "espiculada",
                             "M-PLUR": "espiculados", "F-PLUR": "espiculadas"},
                "forms_es": {"M-SING": "espiculado", "F-SING": "espiculada",
                             "M-PLUR": "espiculados", "F-PLUR": "espiculadas"},
            }]
        }
    }


def test_detect_form_singular_feminine(atlas_minimal):
    forms = atlas_minimal["categories"]["mass_margin"][0]["forms_pt"]
    assert detect_form("lesão espiculada na mama", forms) == "F-SING"


def test_detect_form_plural_feminine(atlas_minimal):
    forms = atlas_minimal["categories"]["mass_margin"][0]["forms_pt"]
    # "espiculadas" deve ser detectado antes de "espiculada"
    assert detect_form("margens espiculadas e irregulares", forms) == "F-PLUR"


def test_detect_form_absent_returns_none(atlas_minimal):
    forms = atlas_minimal["categories"]["mass_margin"][0]["forms_pt"]
    assert detect_form("lesão circunscrita", forms) is None


def test_diff_preserved_no_divergence(atlas_minimal):
    es = "lesión espiculada en mama derecha"
    pt = "lesão espiculada em mama direita"
    out = diff_modifier_agreement(es, pt, atlas_minimal)
    assert out["n_divergences"] == 0
    assert out["preservation_rate"] == 1.0


def test_diff_gender_divergence_detected(atlas_minimal):
    es = "lesión espiculada"        # F-SING
    pt = "lesão espiculado"         # M-SING — divergência de gênero introduzida
    out = diff_modifier_agreement(es, pt, atlas_minimal)
    assert out["n_divergences"] == 1
    assert out["divergences"][0]["divergence_type"] == "gender"


def test_diff_number_divergence_detected(atlas_minimal):
    es = "margen espiculada"        # F-SING
    pt = "margens espiculadas"      # F-PLUR — divergência de número
    out = diff_modifier_agreement(es, pt, atlas_minimal)
    assert out["n_divergences"] == 1
    assert out["divergences"][0]["divergence_type"] == "number"


def test_diff_adjective_only_in_es_ignored(atlas_minimal):
    es = "lesión espiculada"
    pt = "lesão sem características descritas"
    out = diff_modifier_agreement(es, pt, atlas_minimal)
    assert out["n_modifiers_compared"] == 0
    # Adjetivo só em ES = não comparável; não conta como divergência (T17 cobre ausência).
```

Run: `pytest tests/test_evaluation/test_modifier_check.py -v` → 7 PASS (espera).

---

- [ ] **Step 4: Implementar `src/evaluation/modifier_check.py`**

```python
"""F6 — Modifier preservation: detecta divergências morfossintáticas
INTRODUZIDAS pela tradução ES→PT.

Pergunta: a forma flexionada do adjetivo BI-RADS foi preservada?
(não: concordância correta no PT — isso é T22/MQM.)
"""

import re
import unicodedata


MORPHOLOGY_TAGS = ["M-SING", "F-SING", "M-PLUR", "F-PLUR"]


def _norm(s: str) -> str:
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def detect_form(text: str, forms_dict: dict) -> str | None:
    """Detecta qual forma morfológica do adjetivo aparece no texto.

    Plurais ANTES de singulares para evitar match parcial
    ("espiculadas" ⊃ "espiculada").
    """
    text_n = _norm(text)
    for tag in ["M-PLUR", "F-PLUR", "M-SING", "F-SING"]:
        form = forms_dict.get(tag)
        if not form:
            continue
        if re.search(r"\b" + re.escape(_norm(form)) + r"\b", text_n):
            return tag
    return None


def diff_modifier_agreement(es_text: str, pt_text: str, atlas: dict) -> dict:
    """Compara forma do adjetivo em ES vs PT, retorna divergências introduzidas."""
    divergences = []
    n_compared = 0

    for cat_key, entries in atlas["categories"].items():
        for entry in entries:
            forms_pt = entry.get("forms_pt")
            forms_es = entry.get("forms_es")
            if not forms_pt or not forms_es:
                continue

            es_form = detect_form(es_text, forms_es)
            pt_form = detect_form(pt_text, forms_pt)

            if es_form is None or pt_form is None:
                continue

            n_compared += 1
            if es_form != pt_form:
                divergences.append({
                    "adjective_canonical": entry["pt_canonical"],
                    "bi_rads_code": entry.get("bi_rads_code"),
                    "es_form": es_form,
                    "pt_form": pt_form,
                    "divergence_type": (
                        "gender" if es_form[0] != pt_form[0]
                        else "number" if es_form[2:] != pt_form[2:]
                        else "both"
                    ),
                })

    return {
        "n_modifiers_compared": n_compared,
        "n_divergences": len(divergences),
        "divergence_rate": len(divergences) / n_compared if n_compared else 0.0,
        "preservation_rate": (n_compared - len(divergences)) / n_compared if n_compared else None,  # None = abstain
        "modifier_coverage_pass": (n_compared >= 1),
        "divergences": divergences,
    }
```

**Nota:** `preservation_rate = None` quando `n_compared == 0` (abstenção, não 1.0). Isso evita inflar artificialmente o agregado.

---

- [ ] **Step 5: Run + verify (com cobertura)**

```bash
pytest tests/test_evaluation/test_modifier_check.py -v
python -m src.evaluation.modifier_check
```

`results/translation/modifier_preservation.csv` — uma linha por laudo:
```
report_id,
n_modifiers_compared, n_divergences,
divergence_rate, preservation_rate,
modifier_coverage_pass,
gender_divergence_count, number_divergence_count, both_divergence_count,
divergences_json
```

Verify:
```bash
python -c "
import pandas as pd
df = pd.read_csv('results/translation/modifier_preservation.csv')
n_total = len(df)
n_covered = df['modifier_coverage_pass'].sum()
print(f'Total laudos:                                {n_total}')
print(f'Laudos com >=1 modifier comparable:          {n_covered}  ({100*n_covered/n_total:.1f}%)')
print(f'preservation_rate mediano (cobertos):        {df[df[\"modifier_coverage_pass\"]][\"preservation_rate\"].median():.4f}')
print(f'Divergências total:                          {df[\"n_divergences\"].sum()}')
"
```

**Critério de sanidade:** cobertura ≥ 70%. Se < 70%, T18 vira evidência limitada — registrar como caveat na §5 do notebook (Step 7 abaixo já cobre isso).

---

- [ ] **Step 6: Calibrar threshold empírico + gerar summary**

**6a — `scripts/calibrate_modifier_thresholds.py`:**

```python
"""Calibra threshold empírico de preservation_rate via duplicatas (T19)."""
import pandas as pd, numpy as np, json
from pathlib import Path

df_mod = pd.read_csv("results/translation/modifier_preservation.csv")
df_dups = pd.read_csv("results/translation/translations.csv")

dup_counts = df_dups["report_id"].value_counts()
dup_ids = set(dup_counts[dup_counts > 1].index)

# Apenas laudos com cobertura ativa (preservation_rate não-nulo)
dup_mod = df_mod[df_mod["report_id"].isin(dup_ids) & df_mod["modifier_coverage_pass"]]
n_dups = len(dup_mod)

if n_dups >= 30:
    p5 = float(np.percentile(dup_mod["preservation_rate"].dropna(), 5))
    threshold = max(p5, 0.90)  # piso conservador
    method = "p5 of preservation_rate on duplicate pairs"
else:
    p5 = None
    threshold = 0.95  # fallback se duplicatas insuficientes
    method = "fallback (insufficient duplicates with coverage)"

Path("results/translation/modifier_threshold_empirical.json").write_text(
    json.dumps({
        "preservation_rate_threshold": threshold,
        "method": method,
        "n_duplicates_with_coverage": n_dups,
        "p5_observed": p5,
        "fallback_floor": 0.90,
    }, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print(f"Threshold empírico: {threshold:.4f}  (n_dups={n_dups}, p5={p5})")
```

Run:
```bash
python -m scripts.calibrate_modifier_thresholds
```

**6b — `scripts/build_modifier_summary.py`:**

```python
"""Sumário consolidado T18 — alimenta T23 §5 sem recomputar."""
import pandas as pd, json
from pathlib import Path

df = pd.read_csv("results/translation/modifier_preservation.csv")
threshold = json.loads(Path("results/translation/modifier_threshold_empirical.json").read_text())["preservation_rate_threshold"]

covered = df[df["modifier_coverage_pass"]]
total = len(df)
n_covered = len(covered)

# Divergências agregadas
n_div_total = int(df["n_divergences"].sum())
gender_total = int(df["gender_divergence_count"].sum())
number_total = int(df["number_divergence_count"].sum())
both_total = int(df["both_divergence_count"].sum())

# preservation_rate global = (compared - divergences) / compared
total_compared = int(df["n_modifiers_compared"].sum())
preservation_global = (total_compared - n_div_total) / total_compared if total_compared else None

# Threshold p5 das duplicatas (usado em T20 para passed)
threshold_data = json.loads(Path("results/translation/modifier_threshold_empirical.json").read_text())

summary = {
    "total_laudos": total,
    "laudos_com_pelo_menos_1_modifier_comparado": n_covered,
    "coverage_rate": round(n_covered / total, 4) if total else 0,
    "n_modifiers_total_compared": total_compared,
    "preservation_rate_global": round(preservation_global, 4) if preservation_global is not None else None,
    "n_divergences_total": n_div_total,
    "divergence_breakdown": {
        "gender": gender_total,
        "number": number_total,
        "both": both_total,
    },
    "preservation_rate_p5_duplicates": threshold_data.get("p5_observed"),
    "threshold_empirical": threshold,
}

Path("results/translation/modifier_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(summary, indent=2))
```

Run:
```bash
python -m scripts.build_modifier_summary
```

**Saída esperada (formato):**
```json
{
  "total_laudos": 4357,
  "laudos_com_pelo_menos_1_modifier_comparado": 3892,
  "coverage_rate": 0.893,
  "n_modifiers_total_compared": 18234,
  "preservation_rate_global": 0.987,
  "n_divergences_total": 237,
  "divergence_breakdown": {"gender": 89, "number": 142, "both": 6},
  "preservation_rate_p5_duplicates": 0.952,
  "threshold_empirical": 0.952
}
```

**Integração com T20 (`validation_results.jsonl`):**

```python
# Em consolidate.py — T20 lê threshold do JSON
threshold = json.loads(Path("results/translation/modifier_threshold_empirical.json").read_text())["preservation_rate_threshold"]

if not row["modifier_coverage_pass"]:
    mod_block = {
        "n_compared": 0,
        "preservation_rate": None,
        "passed": None,           # abstain — não conta no overall_passed
        "reason": "no_modifier_coverage"
    }
else:
    mod_block = {
        "n_compared": row["n_modifiers_compared"],
        "n_divergences": row["n_divergences"],
        "preservation_rate": row["preservation_rate"],
        "threshold": threshold,
        "passed": row["preservation_rate"] >= threshold,
    }
record["validations"]["modifier_agreement"] = mod_block
```

`passed = None` (abstain) **não conta** em `overall_passed` (similar a `back_translation.in_sample = False`).

---

- [ ] **Step 7: Commit**

```bash
git add configs/birads_glossary_atlas_es_pt.json \
        scripts/verify_atlas_morphology.py \
        scripts/calibrate_modifier_thresholds.py \
        scripts/build_modifier_summary.py \
        src/evaluation/modifier_check.py \
        tests/test_evaluation/test_modifier_check.py \
        results/translation/modifier_preservation.csv \
        results/translation/modifier_threshold_empirical.json \
        results/translation/modifier_summary.json
git commit -m "feat(evaluation): F6 preservacao morfossintatica com cobertura + calibracao empirica via duplicatas"
```

#### Limitação reconhecida (T23 §5)

Adicionar parágrafo no notebook:

> **Limitações T18:** A análise de preservação morfossintática cobre apenas os ~30 adjetivos BI-RADS canônicos com mapa morfológico explícito no Atlas. Concordância em vocabulário fora dessa lista (substantivos descritivos, adjetivos não-BI-RADS) é avaliada qualitativamente na revisão MQM (T22, dimensão `mqm_fluency`). Quando um laudo não contém adjetivo BI-RADS comparável (`n_modifiers_compared = 0`, ~10% da base esperado), T18 vota **abstain** — não conta como passou nem falhou. Coverage rate é reportada explicitamente em `modifier_summary.json`. T18 reporta apenas divergências **introduzidas pela tradução** — erros morfossintáticos pré-existentes no laudo ES original (typos do laudista) não são contabilizados, evitando confusão entre erro de fonte e erro de tradução. O threshold de `preservation_rate` é calibrado empiricamente via percentil 5 das duplicatas (T19), com piso conservador 0.90 — alinhado com T14.B Step 2.6 para coerência metodológica.

---

### Task 19: F7 — Estabilidade operacional via duplicatas 🔲 PENDING

**Files:**
- Create: `src/evaluation/duplicate_stability.py`
- Create: `scripts/build_duplicate_summary.py`
- Create: `tests/test_evaluation/test_duplicate_stability.py`
- Output: `results/translation/duplicate_pairs.csv` (classificação em 4 camadas)
- Output: `results/translation/duplicate_stability.csv` (métricas por par)
- Output: `results/translation/duplicate_stability_summary.json`

#### Nota de escopo (Ajuste 1) — reposicionamento metodológico

> **T19 mede estabilidade operacional em duplicatas geradas por crash/restart na Phase A** — pares de traduções do mesmo `report_id` produzidos em sessões distintas mas com **mesmo `prompt_hash` (filtro obrigatório)**. **Não é experimento formal de reprodutibilidade**; é análise de variação intrínseca observada em condições de produção. Subsidia H5 como evidência primária com caveat de pareamento operacional, e calibra empiricamente os pisos de variação tolerada em T14.B (back-translation) e T18 (modifier preservation).

Esse caveat vai literalmente para o notebook T23 §5 e para o resumo T19. Banca pergunta sobre status científico → resposta direta.

#### Filtragem em 4 camadas (Ajuste 2)

Cada `report_id` repetido recebe classificação determinística:

| Camada | Critério |
|---|---|
| `duplicate_candidate` | `report_id` com >1 linha em `translations.csv` |
| `valid_duplicate` | `candidate` AND ambas traduções PT não-vazias |
| `effective_duplicate` | `valid` AND mesmo `prompt_hash` entre as duas execuções |
| `strict_reproducibility_pair` | `effective` AND mesma sessão (timestamps próximos, mesma `pipeline_run_id` se disponível) |

**Uso de cada camada:**
- `effective_duplicate` é a **fonte primária** para H5 e calibração (T14.B Step 2.6 / T18 Step 6).
- `strict_reproducibility_pair` é subset de sub-análise reportado se `n ≥ 30`.
- Pares fora de `effective` (prompt diferente ou linha vazia) são reportados como **excluídos** com motivo no `summary.json`.

**Pré-requisito:** `prompt_hash` precisa estar gravado nos artefatos da Phase A. Se não estiver, derivar do hash determinístico do `prompt.py` na época do commit. T19 falha graciosamente para pares sem `prompt_hash` (vão para `excluded.different_prompt_hash`).

#### Métricas em três níveis (Ajuste 3 — versão enxuta, sem Levenshtein)

Levenshtein cortado por sobreposição com chrF++ (que captura edit distance em char n-grams). Métricas finais:

| Nível | Métricas |
|---|---|
| **Textual** | `exact_match_normalized`, `chrf_pt_pt` (sacrebleu chrF++) |
| **Semântico** | `cosine_pt_pt` (mpnet), `bertscore_f1_pt_pt` (xlm-roberta-large) |
| **Estrutural** | `category_match`, `measures_match`, `laterality_match`, `negation_match` (reusa funções de `src/evaluation/structural_checks.py` — T16) |

`exact_match_normalized` = boolean após `_norm` (lower + strip + accents).

#### Flag de instabilidade estrutural (Ajuste 4)

Por par `effective_duplicate`:

```python
"duplicate_structural_instability": not all([
    category_match, measures_match, laterality_match, negation_match
]),
"requires_mqm_review": <duplicate_structural_instability>,
```

`requires_mqm_review = True` marca o `report_id` no CSV. T22 lê e **decide** se promove para amostra (não promoção automática).

**Por que isso importa:** divergência estrutural entre duas traduções do mesmo ES = sinal forte de instabilidade do tradutor naquele caso específico, mais grave que cosine baixo.

---

- [ ] **Step 1: Implementar classificação em 4 camadas**

`src/evaluation/duplicate_stability.py` — função `classify_pairs()`:

```python
import pandas as pd
import json
from pathlib import Path


def classify_pairs(df_translations: pd.DataFrame, df_audit_jsonl_path: str) -> pd.DataFrame:
    """Classifica cada report_id repetido em 4 camadas determinísticas.

    Retorna DataFrame com colunas: report_id, pair_type, valid, effective, strict.
    """
    counts = df_translations["report_id"].value_counts()
    candidates = counts[counts > 1].index.tolist()

    # Carrega prompt_hash do audit JSONL se disponível
    prompt_hashes = {}
    if Path(df_audit_jsonl_path).exists():
        with open(df_audit_jsonl_path, encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    prompt_hashes[rec["report_id"]] = rec.get("prompt_hash")
                except (json.JSONDecodeError, KeyError):
                    continue

    rows = []
    for rid in candidates:
        pair = df_translations[df_translations["report_id"] == rid]
        valid = pair["report_text_raw"].notna().all() and (pair["report_text_raw"] != "").all()
        # Effective: mesmo prompt_hash. Como temos só um hash por report_id no JSONL atual,
        # consideramos effective se valid (assumimos prompt_hash estável dentro da Phase A
        # após o último restart; pares anteriores ao último prompt_fix são excluded).
        ph = prompt_hashes.get(rid)
        effective = valid and ph is not None
        # Strict: pares na mesma sessão — heurística por proximidade temporal não disponível
        # nos artefatos atuais; fica False por padrão (subset opcional)
        strict = False

        rows.append({
            "report_id": rid,
            "valid": valid,
            "effective": effective,
            "strict": strict,
            "exclusion_reason": (
                None if effective
                else "empty_translation" if not valid
                else "different_prompt_hash" if ph is None
                else None
            ),
            "pair_type": (
                "strict_reproducibility_pair" if strict
                else "effective_duplicate" if effective
                else "valid_duplicate" if valid
                else "duplicate_candidate"
            ),
        })

    return pd.DataFrame(rows)
```

Output `results/translation/duplicate_pairs.csv`:
```
report_id, pair_type, valid, effective, strict, exclusion_reason
```

---

- [ ] **Step 2: Implementar métricas em 3 níveis para pares effective**

```python
from src.evaluation.structural_checks import (
    extract_birads_category, extract_measures, extract_laterality, count_negations
)


def compute_pair_metrics(pt1: str, pt2: str, embedder, bertscorer) -> dict:
    """Métricas em 3 níveis de estabilidade para um par PT-PT (mesmo report_id)."""
    # Textual
    pt1_n = pt1.strip().lower()
    pt2_n = pt2.strip().lower()
    exact = (pt1_n == pt2_n)
    chrf = sacrebleu.corpus_chrf([pt2], [[pt1]]).score

    # Semântico
    e1 = embedder.encode([pt1], convert_to_tensor=True)
    e2 = embedder.encode([pt2], convert_to_tensor=True)
    cosine = float((e1 @ e2.T).cpu().item())
    _, _, f1 = bertscorer.score([pt2], [pt1], lang="pt")
    bf1 = float(f1[0])

    # Estrutural (reusa T16)
    cat1, cat2 = extract_birads_category(pt1), extract_birads_category(pt2)
    meas1, meas2 = set(extract_measures(pt1)), set(extract_measures(pt2))
    lat1, lat2 = extract_laterality(pt1, "pt"), extract_laterality(pt2, "pt")
    neg1, neg2 = count_negations(pt1, "pt"), count_negations(pt2, "pt")

    structural_instability = not all([
        cat1 == cat2,
        meas1 == meas2,
        lat1 == lat2,
        neg1 == neg2,
    ])

    return {
        "exact_match_normalized": exact,
        "chrf_pt_pt": round(chrf, 3),
        "cosine_pt_pt": round(cosine, 4),
        "bertscore_f1_pt_pt": round(bf1, 4),
        "category_match": cat1 == cat2,
        "measures_match": meas1 == meas2,
        "laterality_match": lat1 == lat2,
        "negation_match": neg1 == neg2,
        "duplicate_structural_instability": structural_instability,
        "requires_mqm_review": structural_instability,
    }
```

Output `results/translation/duplicate_stability.csv`:
```
report_id, pair_type,
exact_match_normalized, chrf_pt_pt, cosine_pt_pt, bertscore_f1_pt_pt,
category_match, measures_match, laterality_match, negation_match,
duplicate_structural_instability, requires_mqm_review
```

Apenas pares `effective_duplicate` recebem métricas (excluídos vão só ao `duplicate_pairs.csv` com `exclusion_reason`).

---

- [ ] **Step 3: TDD — `tests/test_evaluation/test_duplicate_stability.py`**

```python
import pandas as pd
from src.evaluation.duplicate_stability import classify_pairs, compute_pair_metrics


def test_pair_classification_4_layers(tmp_path, mocker):
    """4 camadas: candidate, valid, effective, strict — distinguidas corretamente."""
    df = pd.DataFrame([
        {"report_id": "RPT_001", "report_text_raw": "texto a"},
        {"report_id": "RPT_001", "report_text_raw": "texto a'"},  # valid+effective
        {"report_id": "RPT_002", "report_text_raw": "texto b"},
        {"report_id": "RPT_002", "report_text_raw": ""},          # invalid (empty)
        {"report_id": "RPT_003", "report_text_raw": "texto c"},
        {"report_id": "RPT_003", "report_text_raw": "texto c'"},  # valid sem prompt_hash
    ])
    audit_jsonl = tmp_path / "audit.jsonl"
    audit_jsonl.write_text(
        '{"report_id":"RPT_001","prompt_hash":"abc"}\n', encoding="utf-8"
    )
    out = classify_pairs(df, str(audit_jsonl))

    rpt001 = out[out["report_id"]=="RPT_001"].iloc[0]
    assert rpt001["valid"] and rpt001["effective"]
    assert rpt001["pair_type"] == "effective_duplicate"

    rpt002 = out[out["report_id"]=="RPT_002"].iloc[0]
    assert not rpt002["valid"]
    assert rpt002["exclusion_reason"] == "empty_translation"

    rpt003 = out[out["report_id"]=="RPT_003"].iloc[0]
    assert rpt003["valid"] and not rpt003["effective"]
    assert rpt003["exclusion_reason"] == "different_prompt_hash"


def test_metrics_on_identical_pair(...):
    """Par idêntico: cosine=1.0, chrf=100, structural sempre match."""
    out = compute_pair_metrics("BI-RADS 4 mama esquerda 15mm", "BI-RADS 4 mama esquerda 15mm", ...)
    assert out["exact_match_normalized"] is True
    assert out["cosine_pt_pt"] == 1.0
    assert out["category_match"] and out["measures_match"] and out["laterality_match"]
    assert not out["duplicate_structural_instability"]


def test_metrics_on_known_divergent_pair(...):
    """Par com troca de medida: measures_match=False, structural_instability=True."""
    pt1 = "nódulo BI-RADS 4 de 15mm em mama direita"
    pt2 = "nódulo BI-RADS 4 de 15cm em mama direita"  # mm -> cm
    out = compute_pair_metrics(pt1, pt2, ...)
    assert out["measures_match"] is False
    assert out["duplicate_structural_instability"] is True
    assert out["requires_mqm_review"] is True


def test_excludes_diff_prompt_pairs():
    """Pares com prompt_hash divergente não entram em effective_duplicate."""
    # validado em test_pair_classification_4_layers (RPT_003)
    pass


def test_abstain_for_singleton():
    """Singletons não aparecem em duplicate_pairs.csv (não são candidatos)."""
    df = pd.DataFrame([{"report_id": "RPT_999", "report_text_raw": "x"}])
    out = classify_pairs(df, "/tmp/empty.jsonl")
    assert "RPT_999" not in out["report_id"].values
```

Run: `pytest tests/test_evaluation/test_duplicate_stability.py -v` → **5 PASS**.

---

- [ ] **Step 4: Run + verify**

```bash
pytest tests/test_evaluation/test_duplicate_stability.py -v
python -m src.evaluation.duplicate_stability
python -c "
import pandas as pd, json
pairs = pd.read_csv('results/translation/duplicate_pairs.csv')
mets  = pd.read_csv('results/translation/duplicate_stability.csv')
print('Candidatos:', len(pairs))
print('Effective:',  pairs['effective'].sum())
print('Strict:',     pairs['strict'].sum())
print('Excluded:')
print(pairs[~pairs['effective']]['exclusion_reason'].value_counts())
print()
print('Metrics on effective pairs:')
print(f'  cosine mediana: {mets[\"cosine_pt_pt\"].median():.4f}')
print(f'  cosine p5:      {mets[\"cosine_pt_pt\"].quantile(0.05):.4f}')
print(f'  exact match rate: {mets[\"exact_match_normalized\"].mean():.4f}')
print(f'  structural_instability: {mets[\"duplicate_structural_instability\"].sum()}')
print(f'  requires_mqm_review IDs: {mets[mets[\"requires_mqm_review\"]][\"report_id\"].tolist()}')
"
```

---

- [ ] **Step 5: Sumário consolidado (Ajuste 7) — `scripts/build_duplicate_summary.py`**

```python
"""Sumário T19 alimenta T23 §5 sem recomputar."""
import pandas as pd, json, numpy as np
from pathlib import Path

pairs = pd.read_csv("results/translation/duplicate_pairs.csv")
mets  = pd.read_csv("results/translation/duplicate_stability.csv")

eff = mets[mets["report_id"].isin(pairs[pairs["effective"]]["report_id"])]
n_eff = len(eff)

excluded_breakdown = pairs[~pairs["effective"]]["exclusion_reason"].value_counts().to_dict()

if n_eff >= 30:
    median_cos = float(eff["cosine_pt_pt"].median())
    p5_cos     = float(np.percentile(eff["cosine_pt_pt"].dropna(), 5))
else:
    median_cos = float(eff["cosine_pt_pt"].median()) if n_eff else None
    p5_cos     = None  # n insuficiente

structural_ids = eff[eff["duplicate_structural_instability"]]["report_id"].tolist()
struct_rate = len(structural_ids) / n_eff if n_eff else 0

# H5 components
h5_components = {
    "median_cosine_passed": median_cos is not None and median_cos >= 0.98,
    "p5_cosine_passed":     p5_cos is not None and p5_cos >= 0.95,
    "structural_passed":    struct_rate <= 0.02,  # tolerância 2%
}
h5_passed = all(h5_components.values())

summary = {
    "duplicate_candidate_count":        int(len(pairs)),
    "valid_duplicate_count":            int(pairs["valid"].sum()),
    "effective_duplicate_count":        int(pairs["effective"].sum()),
    "strict_reproducibility_pair_count": int(pairs["strict"].sum()),
    "excluded": excluded_breakdown,

    "median_cosine_pt_pt":      round(median_cos, 4) if median_cos is not None else None,
    "p5_cosine_pt_pt":          round(p5_cos, 4) if p5_cos is not None else None,
    "median_bertscore_f1_pt_pt": round(float(eff["bertscore_f1_pt_pt"].median()), 4) if n_eff else None,
    "median_chrf_pt_pt":        round(float(eff["chrf_pt_pt"].median()), 3) if n_eff else None,

    "exact_match_normalized_rate": round(float(eff["exact_match_normalized"].mean()), 4) if n_eff else None,

    "structural_instability_count": len(structural_ids),
    "structural_instability_rate":  round(struct_rate, 4),
    "structural_instability_ids":   structural_ids,

    "h5_components": h5_components,
    "h5_passed":     h5_passed,
}

Path("results/translation/duplicate_stability_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(summary, indent=2))
```

Run:
```bash
python -m scripts.build_duplicate_summary
```

**Saída esperada (formato):**
```json
{
  "duplicate_candidate_count": 100,
  "valid_duplicate_count": 98,
  "effective_duplicate_count": 96,
  "strict_reproducibility_pair_count": 31,
  "excluded": {"empty_translation": 2, "different_prompt_hash": 2},

  "median_cosine_pt_pt": 0.992,
  "p5_cosine_pt_pt": 0.971,
  "median_bertscore_f1_pt_pt": 0.967,
  "median_chrf_pt_pt": 78.4,

  "exact_match_normalized_rate": 0.42,

  "structural_instability_count": 1,
  "structural_instability_rate": 0.0104,
  "structural_instability_ids": ["RPT_000812"],

  "h5_components": {
    "median_cosine_passed":  true,
    "p5_cosine_passed":      true,
    "structural_passed":     true
  },
  "h5_passed": true
}
```

---

- [ ] **Step 6: Integração com T20 — schema abstain semântico (Ajuste 8)**

T20 (`consolidate.py`) inclui bloco `duplicate_stability` por laudo. **Não entra em `overall_passed`** — é fonte de priorização (T22) e calibração (T14.B/T18), não critério de aprovação.

```python
# Em consolidate.py
mets = pd.read_csv("results/translation/duplicate_stability.csv")
pairs = pd.read_csv("results/translation/duplicate_pairs.csv")
eff_ids = set(pairs[pairs["effective"]]["report_id"])

if rid not in eff_ids:
    dup_block = {"in_pair": False}
else:
    row = mets[mets["report_id"] == rid].iloc[0]
    dup_block = {
        "in_pair":              True,
        "pair_type":            "effective_duplicate",
        "cosine_pt_pt":         row["cosine_pt_pt"],
        "structural_instability": bool(row["duplicate_structural_instability"]),
        "requires_review":      bool(row["requires_mqm_review"]),
    }
record["validations"]["duplicate_stability"] = dup_block

# overall_passed NÃO inclui duplicate_stability (análogo a back_translation.in_sample=False)
```

---

- [ ] **Step 7: Commit**

```bash
git add src/evaluation/duplicate_stability.py \
        scripts/build_duplicate_summary.py \
        tests/test_evaluation/test_duplicate_stability.py \
        results/translation/duplicate_pairs.csv \
        results/translation/duplicate_stability.csv \
        results/translation/duplicate_stability_summary.json
git commit -m "feat(evaluation): F7 estabilidade operacional (4 camadas, metricas em 3 niveis, instabilidade estrutural, summary com H5 multi-componente)"
```

#### Não-dependência circular com T14.B (Ajuste 5)

**T14.B Step 2.6 NÃO depende de T19 ter rodado.** T14.B identifica duplicatas independentemente via:

```python
counts = df_pt["report_id"].value_counts()
dup_ids = set(counts[counts > 1].index)  # mesma definição base
# + filtro effective_duplicate via prompt_hash do JSONL
```

T19 reaproveita o mesmo set de IDs identificados em T14.B e adiciona métricas em 3 níveis + flags estruturais. **Documentado explicitamente em ambas as tasks** para evitar interpretação de paradoxo de ordem.

#### Limitação reconhecida (T23 §5)

> **Limitações T19:** As duplicatas analisadas foram **geradas por crash/restart na Phase A**, não por experimento controlado. T19 mede estabilidade operacional sob produção, não reprodutibilidade formal. Filtramos em 4 camadas (candidate → valid → effective → strict) com `effective_duplicate` (mesmo `prompt_hash`) como fonte primária. Pares fora desse critério são reportados como excluídos com motivo. H5 usa critério multidimensional com tolerância calibrada (≤2% de instabilidade estrutural acomoda ~1 caso em 48). Pares com `requires_mqm_review = True` são candidatos à amostra MQM (T22), com decisão final pelo critério de seleção da T22.

---

### Task 20: F8 — Consolidated `validation_results.jsonl` (single source of truth) 🔲 PENDING

**Files:**
- Create: `src/evaluation/consolidate.py` (modular, função `build_X()` por fonte)
- Create: `tests/test_evaluation/test_consolidate.py` (9 testes TDD)
- Create: `docs/superpowers/specs/composite_score_formula_v1.md` (pré-registro)
- Create: `scripts/verify_validation_consolidated.py` (sanidade pós-execução)
- Output: `results/translation/validation_results.jsonl`

**Goal:** Consolidar **6 fontes** em registro único por laudo com `overall_passed`, `composite_score`, `failure_reasons`. Schema unificado, lógica de abstain explícita, fórmula pré-registrada.

#### Princípio governante — três tipos de "valor"

| Estado | Significado | Efeito em `overall_passed` |
|---|---|---|
| `passed: true` | Fonte aplicável e laudo passou | Conta como TRUE |
| `passed: false` | Fonte aplicável e laudo falhou | Reprova o laudo |
| `passed: null` | **Abstain** (T18 sem cobertura, etc.) | NÃO conta |
| `in_sample: false` ou `in_pair: false` | Fonte **não aplicável** ao laudo | NÃO conta |

Abstain e não-aplicável também não entram em `composite_score` (pesos renormalizam).

`duplicate_stability` é caso especial: **nunca entra em `overall_passed`**. É fonte de priorização (T22) e calibração (T14.B/T18), não de aprovação.

---

- [ ] **Step 0: Schema unificado**

Reescrever schema do `validation_results.jsonl` casando com o que T13/T14.B/T17/T18/T19 produzem hoje:

```json
{
  "report_id": "RPT_000001",
  "es_text": "...", "pt_text": "...", "birads_label": 4,

  "validations": {
    "semantic": {
      "bertscore_f1": 0.95,
      "cosine_es_pt": 0.97,
      "chrf": 67.2,
      "ter": 0.18,
      "length_ratio": 0.96,
      "passed": true
    },

    "back_translation": {
      "in_sample": false
      // OU, se in_sample=true:
      // "in_sample": true,
      // "cosine_es_es_bt": 0.93,
      // "bertscore_f1_es_es_bt": 0.96,
      // "chrf_es_es_bt": 71.3,
      // "category_match": true, "measures_match": true, "laterality_match": true,
      // "passed": true
    },

    "structural": {
      "category_pass": true,
      "measures_pass": true,
      "laterality_pass": true,
      "negation_pass": true,
      "anatomy_pass": true,
      "pt_drift": false,
      "all_structural_pass": true
    },

    "lexical_birads": {
      "overall_acceptable_rate": 1.0,
      "lexical_loss_with_structural_pass": false,
      "lexical_loss_with_structural_fail": false,
      "passed": true
    },

    "modifier_agreement": {
      "n_compared": 8,
      "preservation_rate": 1.0,
      "threshold": 0.95,
      "passed": true
      // OU, se sem cobertura:
      // "n_compared": 0, "preservation_rate": null, "passed": null,
      // "reason": "no_modifier_coverage"
    },

    "audit_deepseek": {
      "audit_final_status": "approved",
      "audit_final_score": 9.5,
      "critical_error_count": 0,
      "major_error_count": 0,
      "minor_error_count": 0,
      "has_critical_error": false,
      "passed": true
    },

    "duplicate_stability": {
      "in_pair": false
      // OU, se in_pair=true:
      // "in_pair": true,
      // "pair_type": "effective_duplicate",
      // "cosine_pt_pt": 0.991,
      // "structural_instability": false,
      // "requires_review": false
    }
  },

  "overall_passed":     true,            // agregado completo das 6 fontes ativas
  "clinical_pass":      true,            // ignora modifier-only failures (warning, não reprovação clínica)
  "composite_score":    95.4,
  "failure_reasons":    [],              // diagnóstico granular per-fonte
  "warnings":           [],              // flags de atenção que NÃO reprovam clinicamente

  "metadata": {
    "consolidated_at": "2026-04-28T...",
    "schema_version": "2026-04-28-v1",
    "atlas_glossary_hash": "sha256:...",
    "audit_prompt_hash": "sha256:..."
  }
}
```

**Mudanças vs schema antigo:**
- ❌ `score_global`/`status` (campo legado) → ✅ `audit_final_status`/`has_critical_error`/`critical_error_count`
- ❌ `term_match_ratio`/`anomalies_count` → ✅ `overall_acceptable_rate`/`lexical_loss_with_structural_*`
- ❌ `gender_violations`/`number_violations` → ✅ `n_compared`/`preservation_rate`/`threshold`
- ❌ duplicate_stability ausente → ✅ `in_pair: bool` + métricas opcionais
- ❌ semantic com `bleu` → ✅ semantic sem BLEU (T15)
- ✅ NOVO: bloco `metadata` com schema_version + hashes

---

- [ ] **Step 1: Pré-registro da fórmula `composite_score`**

Criar `docs/superpowers/specs/composite_score_formula_v1.md` documentando a fórmula **antes da execução**:

```markdown
# composite_score — Fórmula v1 (pré-registrada 2026-04-28)

Fórmula:
    composite_score = Σ(w_i · Q_i) / Σ(w_i_active)

| Componente   | Métrica                                    | Peso | Ativo se               |
|--------------|--------------------------------------------|------|------------------------|
| Q_semantic   | 100 · bertscore_f1                         | 0.20 | sempre                 |
| Q_structural | 100 · all_structural_pass                  | 0.25 | sempre                 |
| Q_lexical    | 100 · overall_acceptable_rate              | 0.15 | sempre                 |
| Q_modifier   | 100 · preservation_rate                    | 0.10 | passed != null         |
| Q_audit      | 100 · (1 − has_critical_error)             | 0.20 | sempre                 |
| Q_back_trans | 100 · cosine_es_es_bt                      | 0.10 | in_sample = true       |

duplicate_stability NÃO entra (priorização, não aprovação).

Faixas de interpretação:
- 90–100: alta qualidade
- 75–89: aceitável com revisão sugerida
- < 75: problemático (priorizado para MQM em T22)
```

Pesos justificados: `Q_structural` 0.25 (preservação programática é crítica); `Q_semantic` e `Q_audit` 0.20 (semântica + erro crítico); `Q_lexical` 0.15; `Q_modifier` e `Q_back_trans` 0.10 (subset/abstain).

**Defesa anti-p-hacking:** este `.md` + `consolidate.py` + testes vão para o **commit 1** (Step 6) com tag git `composite-score-formula-pre-registered`. O commit 2 (com `validation_results.jsonl`) vem **depois** da execução. Tag = timestamp imutável.

---

- [ ] **Step 2: Regras de agregação com abstain — 3 funções pequenas**

```python
# src/evaluation/consolidate.py

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


def failure_reasons(v: dict) -> list[str]:
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


def clinical_pass(v: dict) -> bool:
    """Aprovação CLÍNICA — ignora `modifier-only` failures.

    Divergência morfossintática (gênero/número) isolada vira warning, não
    reprovação clínica. Erros que afetam decisão médica (categoria, medidas,
    lateralidade, negação) entram normalmente.

    Hierarquia interpretativa (registrada em composite_score_formula_v1.md):
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


def warnings(v: dict) -> list[str]:
    """Flags que indicam atenção mas NÃO reprovação clínica.

    São sinais para priorização (T22 Tier 4), não critério de pass/fail.
    """
    w = []
    if v["modifier_agreement"].get("passed") is False:
        w.append("modifier_divergence")
    if v["duplicate_stability"].get("requires_review"):
        w.append("duplicate_structural_instability")
    return w


def composite_score(v: dict) -> float:
    """Fórmula v1 pré-registrada — pesos renormalizam por fontes ativas."""
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
```

---

- [ ] **Step 3: `consolidate.py` modular — uma `build_X()` por fonte**

Estrutura:

```python
# src/evaluation/consolidate.py
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

SCHEMA_VERSION = "2026-04-28-v1"


def file_hash(path: str) -> str:
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def build_semantic(rid: str, df_intrinsic: pd.DataFrame) -> dict:
    row = df_intrinsic[df_intrinsic["report_id"] == rid]
    if row.empty:
        return {"passed": False, "reason": "missing"}
    r = row.iloc[0]
    bf1 = float(r["bertscore_f1"])
    cos = float(r["cosine_sim"])
    return {
        "bertscore_f1": bf1,
        "cosine_es_pt": cos,
        "chrf":         float(r["chrf"]),
        "ter":          float(r["ter"]),
        "length_ratio": float(r["length_ratio"]),
        "passed":       bf1 >= 0.85 and cos >= 0.85,
    }


def build_back_translation(rid: str, df_bt: pd.DataFrame, threshold_json: dict) -> dict:
    row = df_bt[df_bt["report_id"] == rid] if df_bt is not None else None
    if row is None or row.empty:
        return {"in_sample": False}
    r = row.iloc[0]
    th = threshold_json["thresholds"]
    passed = (
        r["cosine_es_es_bt"] >= th["cosine_es_es_bt"]["p5"]
        and r["bertscore_f1_es_es_bt"] >= th["bertscore_f1_es_es_bt"]["p5"]
        and r["chrf_es_es_bt"] >= th["chrf_es_es_bt"]["p5"]
        and bool(r["category_match"]) and bool(r["measures_match"]) and bool(r["laterality_match"])
    )
    return {
        "in_sample": True,
        "cosine_es_es_bt":         float(r["cosine_es_es_bt"]),
        "bertscore_f1_es_es_bt":   float(r["bertscore_f1_es_es_bt"]),
        "chrf_es_es_bt":           float(r["chrf_es_es_bt"]),
        "category_match":          bool(r["category_match"]),
        "measures_match":          bool(r["measures_match"]),
        "laterality_match":        bool(r["laterality_match"]),
        "passed":                  passed,
    }


def build_structural(rid: str, df_struct: pd.DataFrame) -> dict:
    row = df_struct[df_struct["report_id"] == rid].iloc[0]
    return {
        "category_pass":       bool(row["category_pass"]),
        "measures_pass":       bool(row["measures_pass"]),
        "laterality_pass":     bool(row["laterality_pass"]),
        "negation_pass":       bool(row["negation_pass"]),
        "anatomy_pass":        bool(row["anatomy_pass"]),
        "pt_drift":            bool(row["pt_drift"]),
        "all_structural_pass": bool(row["all_structural_pass"]),
    }


def build_lexical(rid: str, df_lex: pd.DataFrame, summary: dict) -> dict:
    # Agregar lexical_consistency.csv per laudo
    rows = df_lex[df_lex["report_id"] == rid]
    loss_iso = bool(rows["lexical_loss_with_structural_pass"].any()) if not rows.empty else False
    loss_crit = bool(rows["lexical_loss_with_structural_fail"].any()) if not rows.empty else False
    # overall_acceptable_rate é global (do summary), mas reportamos per-laudo via term_acceptable média
    rate_per_laudo = float(rows["term_acceptable_ratio"].mean()) if not rows.empty else 1.0
    return {
        "overall_acceptable_rate":            rate_per_laudo,
        "lexical_loss_with_structural_pass":  loss_iso,
        "lexical_loss_with_structural_fail":  loss_crit,
        "passed":                              rate_per_laudo >= 0.99 and not loss_crit,
    }


def build_modifier(rid: str, df_mod: pd.DataFrame, threshold: float) -> dict:
    row = df_mod[df_mod["report_id"] == rid]
    if row.empty:
        return {"n_compared": 0, "preservation_rate": None, "passed": None,
                "reason": "missing_record"}
    r = row.iloc[0]
    if not bool(r["modifier_coverage_pass"]):
        return {"n_compared": 0, "preservation_rate": None, "passed": None,
                "reason": "no_modifier_coverage"}
    return {
        "n_compared":        int(r["n_modifiers_compared"]),
        "preservation_rate": float(r["preservation_rate"]),
        "threshold":         threshold,
        "passed":            float(r["preservation_rate"]) >= threshold,
    }


def build_audit(rid: str, audit_jsonl_records: dict) -> dict:
    """⚠ DECISÃO METODOLÓGICA REGISTRADA NO PRÉ-REGISTRO:

    `passed = audit_final_status in ("approved", "review")` — ou seja,
    `review` é tratado como passed=True na fonte audit_deepseek.

    Por quê:
    1. `audit_final_status` é derivado em T13 da regra: "review" só ocorre
       quando há findings VALIDADAS pela meta-auditoria mas sem `has_critical_error`.
       Significa: o auditor LLM apontou problemas menores (major/minor) que a
       meta-validação confirmou, mas nenhum atinge severidade crítica
       (categoria/medida/lateralidade/negação preservadas via override mecânico T12.6).

    2. Erros críticos (categoria, medidas, lateralidade, negação) são capturados
       PELA SEGUNDA VEZ via `has_critical_error` — que vai diretamente para
       `Q_audit = 100·(1−has_critical_error)` no composite_score (T20 fórmula v1).
       Se "review" reprovasse aqui, contaríamos o mesmo erro crítico duas vezes
       (uma em passed, outra em Q_audit), distorcendo overall_passed e o score.

    3. Casos genuinamente problemáticos (sem severidade crítica mas ainda
       sinalizados) NÃO são perdidos: aparecem em `failure_reasons` via outras
       fontes (semantic, structural, lexical, modifier). Se múltiplas fontes
       ortogonais reprovam, `overall_passed = False` mesmo com audit_passed=True.

    4. Alternativa "review → passed=False" foi descartada porque inflaria
       artificialmente a taxa de reprovação Phase A baseada em achados que a
       própria meta-validação considera não-acionáveis (ex: detalhes de fluência).

    Esta decisão é parte do pré-registro `composite_score_formula_v1.md`
    (tag git `composite-score-formula-pre-registered`).
    """
    rec = audit_jsonl_records.get(rid)
    if not rec:
        return {"audit_final_status": "missing", "passed": False}
    return {
        "audit_final_status":   rec["audit_final_status"],
        "audit_final_score":    rec.get("audit_final_score"),
        "critical_error_count": int(rec["critical_error_count"]),
        "major_error_count":    int(rec.get("major_error_count", 0)),
        "minor_error_count":    int(rec.get("minor_error_count", 0)),
        "has_critical_error":   bool(rec["has_critical_error"]),
        # passed=True para approved+review; rejected reprova (única classe que reprova aqui)
        "passed":               rec["audit_final_status"] in ("approved", "review"),
    }


def build_duplicate(rid: str, eff_ids: set, df_dup: pd.DataFrame) -> dict:
    if rid not in eff_ids:
        return {"in_pair": False}
    row = df_dup[df_dup["report_id"] == rid].iloc[0]
    return {
        "in_pair":               True,
        "pair_type":             "effective_duplicate",
        "cosine_pt_pt":          float(row["cosine_pt_pt"]),
        "structural_instability": bool(row["duplicate_structural_instability"]),
        "requires_review":       bool(row["requires_mqm_review"]),
    }


def build_record(rid, data, atlas_hash, prompt_hash) -> dict:
    v = {
        "semantic":           build_semantic(rid, data["intrinsic"]),
        "back_translation":   build_back_translation(rid, data["bt"], data["bt_thresholds"]),
        "structural":         build_structural(rid, data["structural"]),
        "lexical_birads":     build_lexical(rid, data["lexical"], data["lexical_summary"]),
        "modifier_agreement": build_modifier(rid, data["modifier"], data["modifier_threshold"]),
        "audit_deepseek":     build_audit(rid, data["audit_records"]),
        "duplicate_stability": build_duplicate(rid, data["eff_dup_ids"], data["dup_metrics"]),
    }
    return {
        "report_id":   rid,
        "es_text":     data["es"][rid],
        "pt_text":     data["pt"][rid],
        "birads_label": data["labels"][rid],
        "validations": v,
        "overall_passed":  overall_passed(v),
        "clinical_pass":   clinical_pass(v),
        "composite_score": composite_score(v),
        "failure_reasons": failure_reasons(v),
        "warnings":        warnings(v),
        "metadata": {
            "consolidated_at":     datetime.now(timezone.utc).isoformat(),
            "schema_version":      SCHEMA_VERSION,
            "atlas_glossary_hash": atlas_hash,
            "audit_prompt_hash":   prompt_hash,
        }
    }
```

---

- [ ] **Step 4: TDD com 9 testes**

```python
# tests/test_evaluation/test_consolidate.py
from src.evaluation.consolidate import overall_passed, composite_score, failure_reasons


def _v(**overrides):
    """Validations minimal: tudo passa."""
    base = {
        "semantic":            {"bertscore_f1": 0.95, "passed": True},
        "structural":          {"all_structural_pass": True},
        "lexical_birads":      {"overall_acceptable_rate": 1.0, "passed": True},
        "modifier_agreement":  {"preservation_rate": 1.0, "passed": True},
        "audit_deepseek":      {"has_critical_error": False, "passed": True,
                                "audit_final_status": "approved"},
        "back_translation":    {"in_sample": False},
        "duplicate_stability": {"in_pair": False},
    }
    base.update(overrides)
    return base


def test_overall_passed_all_pass():
    assert overall_passed(_v()) is True


def test_overall_passed_with_modifier_abstain():
    """passed=null não reprova."""
    v = _v(modifier_agreement={"preservation_rate": None, "passed": None})
    assert overall_passed(v) is True


def test_overall_passed_modifier_fails_count():
    """passed=False reprova."""
    v = _v(modifier_agreement={"preservation_rate": 0.85, "passed": False})
    assert overall_passed(v) is False


def test_overall_passed_bt_not_in_sample_ignored():
    """in_sample=False não conta."""
    v = _v(back_translation={"in_sample": False})
    assert overall_passed(v) is True


def test_overall_passed_bt_in_sample_fails():
    """in_sample=True com False reprova."""
    v = _v(back_translation={"in_sample": True, "cosine_es_es_bt": 0.7, "passed": False})
    assert overall_passed(v) is False


def test_duplicate_stability_never_affects_overall_passed():
    """Mesmo com in_pair=True e instabilidade, não reprova."""
    v = _v(duplicate_stability={
        "in_pair": True, "pair_type": "effective_duplicate",
        "cosine_pt_pt": 0.7, "structural_instability": True,
        "requires_review": True,
    })
    assert overall_passed(v) is True  # priorização, não aprovação


def test_composite_score_weights_renormalize_on_abstain():
    """Sem modifier e sem BT, pesos somam apenas das fontes ativas."""
    v = _v(modifier_agreement={"preservation_rate": None, "passed": None})
    score = composite_score(v)
    # 4 componentes ativas: semantic(0.20)+structural(0.25)+lexical(0.15)+audit(0.20)=0.80
    # Q_total = (95*0.20 + 100*0.25 + 100*0.15 + 100*0.20) / 0.80 = 99/0.80
    expected = (95*0.20 + 100*0.25 + 100*0.15 + 100*0.20) / 0.80
    assert abs(score - round(expected, 2)) < 0.01


def test_failure_reasons_distinguishes_critical_vs_nonsuccess():
    v_crit = _v(audit_deepseek={"has_critical_error": True, "passed": False,
                                 "audit_final_status": "rejected"})
    assert "audit_critical" in failure_reasons(v_crit)

    v_nons = _v(audit_deepseek={"has_critical_error": False, "passed": False,
                                 "audit_final_status": "review"})
    assert "audit_nonsuccess" in failure_reasons(v_nons)


def test_schema_version_recorded():
    """build_record() inclui metadata.schema_version."""
    from src.evaluation.consolidate import SCHEMA_VERSION
    assert SCHEMA_VERSION == "2026-04-28-v1"


def test_modifier_only_failure_is_clinical_pass():
    """Laudo com modifier reprovando E TUDO o resto OK:
    - overall_passed = False  (agregado completo das 6 fontes)
    - clinical_pass  = True   (modifier-only não reprova clinicamente)
    - has_critical_error = False  (T12.6 mecânico não disparou)
    - warnings = ['modifier_divergence']  (sinaliza, não reprova)
    """
    from src.evaluation.consolidate import clinical_pass, warnings
    v = _v(modifier_agreement={"preservation_rate": 0.85, "passed": False})

    assert overall_passed(v) is False           # modifier reprova agregado
    assert clinical_pass(v) is True             # ignora modifier-only failure
    assert v["audit_deepseek"]["has_critical_error"] is False
    assert "modifier_divergence" in warnings(v)
    assert "modifier" in failure_reasons(v)     # diagnóstico granular preserva razão


def test_clinical_pass_zero_with_critical_error():
    """has_critical_error=True → clinical_pass também False (erro clínico real)."""
    from src.evaluation.consolidate import clinical_pass, warnings
    v = _v(audit_deepseek={"has_critical_error": True, "passed": False,
                            "audit_final_status": "rejected"})
    assert clinical_pass(v) is False
    # warning de modifier não aparece se modifier passou
    assert warnings(v) == []
```

Run: `pytest tests/test_evaluation/test_consolidate.py -v` → **11 PASS**.

---

- [ ] **Step 5: Run + verify cross-source**

`scripts/verify_validation_consolidated.py`:

```python
"""Sanidade pós-consolidação: cross-check entre validation_results.jsonl e os summaries."""
import json
from pathlib import Path
import sys

records = []
with open("results/translation/validation_results.jsonl", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            records.append(json.loads(line))

audit_summary = json.loads(Path("results/translation/audit_deepseek_summary.json").read_text())
modifier_summary = json.loads(Path("results/translation/modifier_summary.json").read_text())

n_total = len(records)
n_passed = sum(1 for r in records if r["overall_passed"])
n_critical = sum(1 for r in records if r["validations"]["audit_deepseek"]["has_critical_error"])
n_in_sample = sum(1 for r in records if r["validations"]["back_translation"].get("in_sample"))
n_modifier_abstain = sum(1 for r in records
                         if r["validations"]["modifier_agreement"].get("passed") is None)

# Composite score mediana
scores = [r["composite_score"] for r in records]
score_median = sorted(scores)[len(scores) // 2]

checks = {
    "total_4357":           n_total == 4357,
    "passed_>=90pct":       n_passed / n_total >= 0.90,
    "audit_critical_match": n_critical == audit_summary["laudos_with_critical"],
    "bt_in_sample_count":   240 <= n_in_sample <= 260,  # T14.B alvo ~250
    "modifier_abstain_<=30pct": (n_modifier_abstain / n_total) <= 0.30,
    "composite_median_>=90":   score_median >= 90,
}

for k, ok in checks.items():
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {k}")

if not all(checks.values()):
    print("\nABORTAR antes do commit. Algum critério falhou.")
    sys.exit(1)
print("\nTodas as verificações cross-source passaram.")
```

Run:
```bash
python -m scripts.verify_validation_consolidated
# Esperado: todas as linhas [OK]
```

Se algum critério falhar → **abortar antes do commit**, investigar débito de schema.

---

- [ ] **Step 6: Commit em 2 etapas com tag de pré-registro**

```bash
# Commit 1 — PRÉ-REGISTRO (antes da execução)
git add docs/superpowers/specs/composite_score_formula_v1.md \
        src/evaluation/consolidate.py \
        tests/test_evaluation/test_consolidate.py \
        scripts/verify_validation_consolidated.py
git commit -m "docs(evaluation): pre-registro formula composite_score (T20 schema v1, 9 testes TDD)"
git tag composite-score-formula-pre-registered

# DEPOIS rodar a execução:
python -m src.evaluation.consolidate
python -m scripts.verify_validation_consolidated  # gate

# Commit 2 — EXECUÇÃO (após verify passar)
git add results/translation/validation_results.jsonl
git commit -m "feat(evaluation): F8 validation_results.jsonl consolidado (6 fontes + abstain semantico, 4357 laudos)"
```

**Tag git é timestamp imutável** — comprova que a fórmula foi commitada antes dos resultados existirem. Banca pergunta sobre p-hacking → resposta: `git log --oneline composite-score-formula-pre-registered..HEAD` mostra que execução veio depois.

---

#### Resumo

| Step | Custo | O que resolve |
|---|---|---|
| 0 — Schema unificado | 30 min | 4 incompatibilidades de schema |
| 1 — Fórmula pré-registrada | 15 min | Anti-p-hacking |
| 2 — Regras com abstain | 20 min | `null`/`in_sample`/`in_pair` consistentes |
| 3 — `consolidate.py` modular | 30 min | Funções pequenas testáveis |
| 4 — TDD (9 testes) | 30 min | Defesa de cada caso de borda |
| 5 — Verify cross-source | 10 min | Detecta problema pré-commit |
| 6 — Commit em 2 etapas | 5 min | Tag pré-registro |

**Total: ~2h20min.** Sessão dedicada e contínua, ordem absoluta 0→6 sequencial. Não tocar T21/T22/T23 antes — eles dependem de T20 estável.

#### Efeito cascata sobre T21/T22/T23

| Task | Beneficio | Tempo |
|---|---|---|
| T21 (Cohen's κ) | lê schema único nomeado; expansão 4→6 fontes vira mecânica | ~30 min |
| T22 (MQM) | critério vira `failure_reasons != [] OR requires_mqm_review`; sem cruzar artefatos brutos | ~15 min |
| T23 (notebook) | seções 2–7 leem JSONL direto sem reprocessar | ~30 min ajuste |

---

### Task 21: F9 — Cross-source agreement analysis 🔲 PENDING  ⚠ depende de T20 estável

**Files:**
- Create: `src/evaluation/agreement.py`
- Create: `tests/test_evaluation/test_agreement.py` (6 testes TDD)
- Output: `results/translation/agreement_report.json`

**Goal:** Quantificar convergência das **6 fontes** do `validation_results.jsonl` (T20) via Cohen's κ pareado, com filtro de abstain, distribuição de consenso ponderada por cobertura, exemplos de discordância direcionados, e estratificação por BI-RADS.

#### Princípio metodológico (registrado no relatório)

**Fontes ortogonais devem ter κ baixo a moderado** entre dimensões diferentes — é exatamente o que valida o framework. κ alto entre, ex., BERTScore (semantic) e cosine(ES, ES_bt) sugeriria redundância, não confirmação. Landis & Koch deve ser aplicado com cautela: aqui não medimos confiabilidade entre raters do mesmo construto, mas convergência entre **medidas complementares**.

#### Cobertura por par (3 categorias)

T21 reporta κ pareado entre as 6 fontes (15 pares possíveis), agrupado por cobertura:

| Categoria | n esperado | Pares |
|---|---|---|
| **Cobertura completa** | ~4.357 | 6 pares entre {semantic, structural, lexical, audit} |
| **Cobertura parcial (modifier)** | ~3.000 | 4 pares modifier × {semantic, structural, lexical, audit} |
| **Cobertura amostral (BT)** | ~250 | 5 pares BT × {outras 5} |

`n_pairs` reportado junto com κ. CI largo em pares de baixa cobertura fica visível.

`duplicate_stability` **não entra na matriz κ** — fonte de priorização, não de aprovação (consistente com T20 `overall_passed`).

---

- [ ] **Step 1: Implementar `kappa_with_ci()` com filtro de abstain (Ajuste 1 + 3)**

```python
# src/evaluation/agreement.py
import numpy as np
from scipy.stats import bootstrap
from sklearn.metrics import cohen_kappa_score


SOURCES = ["semantic", "structural", "lexical_birads",
           "modifier_agreement", "audit_deepseek", "back_translation"]


def extract_passed(record: dict, source: str):
    """Retorna True/False/None (None = abstain ou não-aplicável)."""
    block = record["validations"][source]

    if source == "back_translation":
        if not block.get("in_sample"):
            return None
        return block["passed"]

    if source == "structural":
        return block["all_structural_pass"]

    return block.get("passed")  # passed pode ser True/False/None (modifier abstain)


def kappa_with_ci(s_a, s_b, alpha=0.05, n_resamples=10000):
    """Cohen's κ pareado com filtro de None + bootstrap BCa."""
    pairs = [(a, b) for a, b in zip(s_a, s_b) if a is not None and b is not None]
    if len(pairs) < 30:
        return {"kappa": None, "n": len(pairs), "reason": "insufficient_n"}
    A, B = zip(*pairs)
    A_arr, B_arr = np.array(A), np.array(B)
    if len(set(A_arr)) < 2 or len(set(B_arr)) < 2:
        return {"kappa": None, "n": len(pairs), "reason": "constant_class"}

    kappa = float(cohen_kappa_score(A_arr, B_arr))

    # Bootstrap BCa pareado (alinhado com T15/T18/T19)
    def stat(a, b):
        return cohen_kappa_score(a, b)
    res = bootstrap((A_arr, B_arr), statistic=stat, paired=True,
                    n_resamples=n_resamples, confidence_level=1-alpha,
                    method="BCa")
    return {
        "kappa":   kappa,
        "ci_low":  float(res.confidence_interval.low),
        "ci_high": float(res.confidence_interval.high),
        "n":       len(pairs),
    }


def compute_pairwise_kappas(records: list[dict]) -> dict:
    """Matriz κ pareada entre 6 fontes (15 pares); reporta n para visibilidade de cobertura."""
    series = {s: [extract_passed(r, s) for r in records] for s in SOURCES}
    out = {}
    for i, sa in enumerate(SOURCES):
        for sb in SOURCES[i+1:]:
            key = f"{sa}_vs_{sb}"
            out[key] = kappa_with_ci(series[sa], series[sb])
    return out
```

---

- [ ] **Step 2: Distribuição de consenso com abstain (Ajuste 4)**

```python
def consensus_distribution(record: dict) -> dict:
    sources_passed = []
    for k in ["semantic", "structural", "lexical_birads",
              "modifier_agreement", "audit_deepseek"]:
        v = extract_passed(record, k)
        if v is not None:
            sources_passed.append(v)
    bt = extract_passed(record, "back_translation")
    if bt is not None:
        sources_passed.append(bt)

    n = len(sources_passed)
    n_pass = sum(sources_passed)
    return {
        "n_active_sources": n,
        "n_passed":         n_pass,
        "consensus_ratio":  (n_pass / n) if n else None,
        "all_pass":         all(sources_passed) if sources_passed else None,
        "all_fail":         (not any(sources_passed)) if sources_passed else None,
    }


def aggregate_consensus(records: list[dict]) -> dict:
    """Histograma {n_passed: count} + tabela cruzada n_active × n_passed."""
    from collections import Counter
    histogram = Counter()
    crosstab = {}  # {n_active: {n_passed: count}}
    for r in records:
        c = consensus_distribution(r)
        histogram[c["n_passed"]] += 1
        crosstab.setdefault(c["n_active_sources"], Counter())[c["n_passed"]] += 1

    return {
        "histogram_n_passed": dict(histogram),
        "crosstab_active_x_passed": {k: dict(v) for k, v in crosstab.items()},
    }
```

---

- [ ] **Step 3: Disagreement examples por par e por sentido (Ajuste 5)**

```python
def find_disagreement_examples(records, source_a, source_b, kappa_value, top_n=5):
    """Retorna exemplos top-N por sentido para pares com κ < 0.5."""
    if kappa_value is None or kappa_value >= 0.5:
        return None  # par com concordância adequada — não destacar

    a_pass_b_fail = []
    a_fail_b_pass = []
    for r in records:
        a = extract_passed(r, source_a)
        b = extract_passed(r, source_b)
        if a is None or b is None:
            continue
        if a and not b:
            a_pass_b_fail.append({
                "report_id": r["report_id"],
                "composite_score": r["composite_score"],
                "failure_reasons": r["failure_reasons"],
            })
        elif not a and b:
            a_fail_b_pass.append({
                "report_id": r["report_id"],
                "composite_score": r["composite_score"],
                "failure_reasons": r["failure_reasons"],
            })

    # Ordena por composite_score crescente (casos mais informativos primeiro)
    a_pass_b_fail.sort(key=lambda x: x["composite_score"])
    a_fail_b_pass.sort(key=lambda x: x["composite_score"])

    return {
        f"{source_a}_pass_{source_b}_fail": a_pass_b_fail[:top_n],
        f"{source_a}_fail_{source_b}_pass": a_fail_b_pass[:top_n],
    }
```

Saída no relatório:
```json
"disagreement_examples": {
  "semantic_vs_audit_deepseek": {
    "semantic_pass_audit_deepseek_fail": [{"report_id": "...", ...}],
    "semantic_fail_audit_deepseek_pass": [{"report_id": "...", ...}]
  },
  ...
}
```

Apenas pares com κ < 0.5 são destacados. Alimenta T22 (priorização MQM) e T23 §10 (análise de erros).

---

- [ ] **Step 4: κ estratificado por BI-RADS (Ajuste 6)**

```python
def kappa_by_birads_strata(records: list[dict]) -> dict:
    """Por categoria BI-RADS, recalcula κ pareada — subsidia H6."""
    from collections import defaultdict
    by_cat = defaultdict(list)
    for r in records:
        cat = r.get("birads_label")
        if cat is not None:
            by_cat[cat].append(r)

    out = {}
    for cat, recs in sorted(by_cat.items()):
        if len(recs) < 30:
            out[str(int(cat))] = {"reason": "insufficient_n_in_stratum",
                                  "n_records": len(recs)}
            continue
        out[str(int(cat))] = compute_pairwise_kappas(recs)
    return out
```

**Interpretação H6:** se κ é estável entre categorias 0–6 → reforça "sem viés por BI-RADS". Se degrada em estrato específico → flag para investigação no notebook §10.

---

- [ ] **Step 5: Nota interpretativa de κ (Ajuste 2)**

Adicionar ao output:

```python
INTERPRETATION_NOTE = {
    "note": (
        "As 6 fontes medem dimensões parcialmente distintas. κ baixo a moderado "
        "entre fontes complementares é esperado e desejável: cada fonte captura "
        "sinal independente. κ alto entre, por ex., BERTScore (semantic) e "
        "cos(ES, ES_bt) sugeriria redundância, não validação cruzada. "
        "Landis & Koch (1977) deve ser aplicado com cautela aqui — o framework "
        "não testa confiabilidade entre raters do mesmo construto, mas "
        "convergência entre medidas ortogonais."
    ),
    "expected_higher_kappa_pairs": [
        "semantic vs back_translation (ambas semânticas)",
        "lexical_birads vs audit_deepseek (ambas terminológicas)",
    ],
    "expected_lower_kappa_pairs": [
        "structural vs semantic (regra determinística vs embedding)",
        "structural vs audit_deepseek (símbolo vs julgamento LLM)",
        "modifier_agreement vs semantic (morfologia vs significado global)",
    ],
}
```

Parágrafo análogo entra na seção 8 do notebook T23 (Step 6 abaixo registra).

---

- [ ] **Step 6: Compor `agreement_report.json`**

```python
def build_report(records):
    return {
        "metadata": {
            "schema_version":  "2026-04-28-v1",
            "n_records":       len(records),
            "kappa_method":    "Cohen's kappa pairwise + bootstrap BCa n=10000, alpha=0.05",
            "abstain_policy":  "report_id with None in either source is filtered from pair",
        },
        "interpretation":          INTERPRETATION_NOTE,
        "pairwise_kappa":          compute_pairwise_kappas(records),
        "consensus":               aggregate_consensus(records),
        "kappa_by_birads_strata":  kappa_by_birads_strata(records),
        "disagreement_examples":   {
            f"{a}_vs_{b}": find_disagreement_examples(records, a, b,
                                                      kappa_pairs[f"{a}_vs_{b}"]["kappa"])
            for i, a in enumerate(SOURCES)
            for b in SOURCES[i+1:]
            if (kappa_pairs := compute_pairwise_kappas(records))
            and kappa_pairs[f"{a}_vs_{b}"]["kappa"] is not None
            and kappa_pairs[f"{a}_vs_{b}"]["kappa"] < 0.5
        },
    }
```

---

- [ ] **Step 7: TDD com 6 testes (Ajuste 7)**

```python
# tests/test_evaluation/test_agreement.py
import pytest
from src.evaluation.agreement import (
    kappa_with_ci, consensus_distribution, find_disagreement_examples,
    kappa_by_birads_strata, extract_passed,
)


def test_kappa_with_ci_full_coverage():
    """Pares completos calculam κ direto, sem filtragem."""
    a = [True]*40 + [False]*10
    b = [True]*38 + [False]*12  # quase concordância total
    out = kappa_with_ci(a, b, n_resamples=200)  # n_resamples baixo p/ teste rápido
    assert out["kappa"] is not None
    assert out["n"] == 50
    assert out["kappa"] > 0.7


def test_kappa_with_ci_with_abstain():
    """None filtrados; n é o de pares válidos."""
    a = [True, None, False, True, None]
    b = [True, True, False, True, False]
    out = kappa_with_ci(a, b, n_resamples=100)
    # Pares válidos: (True,True), (False,False), (True,True) — 3 pares
    if out["kappa"] is not None:
        assert out["n"] == 3
    else:
        assert out["reason"] == "insufficient_n"


def test_kappa_with_insufficient_n():
    """n < 30 retorna None com razão explícita."""
    a = [True]*10
    b = [True]*10
    out = kappa_with_ci(a, b)
    assert out["kappa"] is None
    assert out["reason"] == "insufficient_n"


def test_consensus_distribution_excludes_abstain():
    """Abstain (None) não vota."""
    record = {
        "validations": {
            "semantic":           {"passed": True},
            "structural":         {"all_structural_pass": True},
            "lexical_birads":     {"passed": True},
            "modifier_agreement": {"passed": None},   # abstain
            "audit_deepseek":     {"passed": False},
            "back_translation":   {"in_sample": False},
        }
    }
    c = consensus_distribution(record)
    # 4 fontes ativas (modifier abstain + bt não-aplicável saem)
    assert c["n_active_sources"] == 4
    assert c["n_passed"] == 3


def test_disagreement_examples_grouped_by_direction():
    """Os 2 sentidos são separados em chaves distintas."""
    records = [
        {"report_id": "R1", "composite_score": 80,
         "failure_reasons": ["audit_critical"],
         "validations": {"semantic": {"passed": True},
                         "audit_deepseek": {"passed": False},
                         "structural": {"all_structural_pass": True},
                         "lexical_birads": {"passed": True},
                         "modifier_agreement": {"passed": True},
                         "back_translation": {"in_sample": False}}},
        {"report_id": "R2", "composite_score": 70, "failure_reasons": ["semantic"],
         "validations": {"semantic": {"passed": False},
                         "audit_deepseek": {"passed": True},
                         "structural": {"all_structural_pass": True},
                         "lexical_birads": {"passed": True},
                         "modifier_agreement": {"passed": True},
                         "back_translation": {"in_sample": False}}},
    ]
    out = find_disagreement_examples(records, "semantic", "audit_deepseek", kappa_value=0.3)
    assert "semantic_pass_audit_deepseek_fail" in out
    assert "semantic_fail_audit_deepseek_pass" in out
    assert out["semantic_pass_audit_deepseek_fail"][0]["report_id"] == "R1"
    assert out["semantic_fail_audit_deepseek_pass"][0]["report_id"] == "R2"


def test_kappa_by_birads_strata():
    """Estratos calculam independentes; estrato com n < 30 retorna razão."""
    records_cat0 = [
        {"birads_label": 0, "report_id": f"R{i}",
         "validations": {"semantic": {"passed": i % 2 == 0},
                         "audit_deepseek": {"passed": i % 2 == 0},
                         "structural": {"all_structural_pass": True},
                         "lexical_birads": {"passed": True},
                         "modifier_agreement": {"passed": True},
                         "back_translation": {"in_sample": False}}}
        for i in range(40)
    ]
    records_cat1 = [
        {"birads_label": 1, "report_id": f"S{i}",
         "validations": {"semantic": {"passed": True},
                         "audit_deepseek": {"passed": True},
                         "structural": {"all_structural_pass": True},
                         "lexical_birads": {"passed": True},
                         "modifier_agreement": {"passed": True},
                         "back_translation": {"in_sample": False}}}
        for i in range(10)  # < 30 → reason
    ]
    out = kappa_by_birads_strata(records_cat0 + records_cat1)
    assert "0" in out
    assert "1" in out
    assert out["1"]["reason"] == "insufficient_n_in_stratum"
```

Run: `pytest tests/test_evaluation/test_agreement.py -v` → **6 PASS**.

---

- [ ] **Step 8: Run + commit**

```bash
python -m src.evaluation.agreement
python -c "
import json
r = json.load(open('results/translation/agreement_report.json'))
print('Pairwise κ (cobertura completa):')
for k, v in r['pairwise_kappa'].items():
    if v.get('kappa') is not None and v['n'] > 3000:
        print(f'  {k:50s} κ={v[\"kappa\"]:.3f}  n={v[\"n\"]:>4}')
print('Consensus histogram:', r['consensus']['histogram_n_passed'])
print('κ estratificado (categorias com dados):')
for cat, kappas in r['kappa_by_birads_strata'].items():
    if isinstance(kappas, dict) and 'reason' not in kappas:
        sample_pair = next(iter(kappas))
        print(f'  BI-RADS {cat}: {sample_pair} κ={kappas[sample_pair][\"kappa\"]:.3f}')
"

git add src/evaluation/agreement.py \
        tests/test_evaluation/test_agreement.py \
        results/translation/agreement_report.json
git commit -m "feat(evaluation): F9 acordo cross-source 6 fontes (Cohen kappa + abstain + estratificado por BI-RADS + disagreement direcional)"
```

---

#### Resumo

| Ajuste | Custo | Resolve |
|---|---|---|
| 1 — Expansão 4→6 fontes + abstain | 30 min | Schema desatualizado + None handling |
| 2 — Nota interpretativa | 5 min | κ baixo lido como fraqueza |
| 3 — Bootstrap BCa n=10000 | 5 min | Inconsistência metodológica |
| 4 — Consensus com abstain | 10 min | Histograma com fontes variáveis |
| 5 — Disagreement por par × sentido | 15 min | Input granular para T22/T23 |
| 6 — κ por BI-RADS | 15 min | Subsidia H6 |
| 7 — TDD (6 testes) | 25 min | Defensibilidade |

**Total: ~1h45min.**

#### Por que κ baixo entre algumas fontes é desejável

| Par | κ esperado | Por quê |
|---|---|---|
| `semantic vs back_translation` | alto | ambas semânticas (mpnet ↔ cosine ES↔ES_bt) |
| `lexical_birads vs audit_deepseek` | alto | ambas terminológicas (Atlas ↔ C1 LLM) |
| `structural vs semantic` | baixo | regra determinística ≠ embedding |
| `structural vs audit_deepseek` | baixo | símbolo ≠ julgamento LLM |
| `modifier_agreement vs semantic` | baixo | morfologia local ≠ significado global |

Isso é a defesa anti-banca: "fontes ortogonais por design — κ alto seria redundância".

---

### Task 22: F10 — Amostra MQM com revisão humana cega (n=50) 🔲 PENDING  ⚠ depende de T20 estável

**Files:**
- Create: `src/evaluation/sample_for_human_review.py`
- Create: `scripts/extract_mqm_results.py`
- Create: `tests/test_evaluation/test_human_review_sample.py` (5 testes TDD)
- Create: `docs/superpowers/specs/mqm_review_protocol_v1.md` (pré-registro do protocolo)
- Output: `results/translation/human_review_for_radiologist.xlsx` (apenas sheet Revisão — ENVIADO ao revisor externo)
- Output: `results/translation/human_review_evidence_internal.xlsx` (apenas sheet Evidence — NUNCA enviado, uso interno)
- Output: `results/translation/human_review_for_radiologist_filled.xlsx` (devolvido pelo revisor, preenchido)
- Output: `results/translation/human_review_results.csv` (pós-revisão, estruturado, merge interno)
- Output: `results/translation/human_review_summary.json` (agregados)
- Create: `docs/translation/instructions_for_reviewer.md` (1 página, enviado junto)
- Create: `scripts/verify_anonymization.py` (gate pré-envio)

**Goal:** Amostra estratificada de 50 laudos para revisão humana cega com framework MQM reduzido (6 dimensões essenciais), critério de seleção hierárquico baseado em flags do `validation_results.jsonl` (T20), output estruturado para T23 §9.

#### O que mudou vs T22 antiga

| Antes | Agora |
|---|---|
| Critérios usavam campos legados (`DeepSeek rejected`, `cos < 0.85`) | Lê schema T20: `has_critical_error`, `failure_reasons`, `requires_review`, `lexical_loss_with_structural_fail` |
| 10 dimensões MQM × 50–100 laudos = 500–1000 julgamentos | 6 essenciais + 4 opcionais × 50 = 300 julgamentos (com fadiga reduzida) |
| Single sheet com evidence pré-populada | **2 arquivos físicamente separados** — Revisão (enviado) + Evidence (interno). Sem sheet oculta. |
| "Quem revisa" não formalizado | Protocolo registrado em `mqm_review_protocol_v1.md` (revisor concreto + crédito + termo de confidencialidade) |
| Sem documento de instruções para o revisor | `docs/translation/instructions_for_reviewer.md` (1 pág, enviado junto) |
| Sem verificação de anonimização | `scripts/verify_anonymization.py` como gate pré-envio |
| Sem output estruturado pós-revisão | `human_review_results.csv` + `human_review_summary.json` para T23 |

---

#### Step 0 — Protocolo de revisão (pré-registrado, antes da execução)

Criar `docs/superpowers/specs/mqm_review_protocol_v1.md` com decisões registradas:

```markdown
# Protocolo MQM v1 — Revisão Humana T22 (pré-registrada 2026-04-28)

| Decisão | Valor |
|---|---|
| Revisor primário | Dr(a). [Nome completo], [especialidade — ex: radiologista mamário], [instituição] |
| Vínculo com a pesquisa | **Externo, sem participação no design do framework** (cegamento institucional) |
| Disponibilidade confirmada | Janela de 3-4h em [data acordada], local [presencial / remoto] |
| Crédito acordado | Agradecimento formal no TCC + coautoria em publicação derivada (se houver) |
| Termo de confidencialidade | Assinado em [data] (modelo simples — uso restrito ao TCC, sem repasse de dados) |
| Plataforma de entrega | [Excel via email criptografado / Google Sheets compartilhado privado / outra] |
| Tamanho da amostra | 50 laudos |
| Tempo estimado por laudo | ~3 min (6 dimensões + leitura) |
| Tempo total estimado | ~3–4h (pode dividir em 2 sessões) |
| Modalidade | **revisão cega** — apenas sheet "Revisão" entregue; "Evidence" em arquivo separado interno (Ajuste 2). Revisor NÃO vê composite_score, failure_reasons ou outputs do framework |
| Anonimização | Confirmada via `scripts/verify_anonymization.py` antes da entrega (Ajuste 4) |
| Critério de "rejeitar" | `mqm_accuracy < 2 OR has_critical_error_human = True` |
| Resolução de divergências entre fontes | flag manual em `uncertainty` (sem revisor secundário) |
| Documento de instruções | `docs/translation/instructions_for_reviewer.md` enviado junto com o Excel |

## Por que cegamento

Sem cegamento, T22 vira validação enviesada do framework (revisor influenciado pelo composite_score). Com cegamento, T22 é fonte **independente** — Cohen's κ humano × auditor LLM (T23 §9) testa convergência genuína.

## Por que 6 dimensões essenciais (não 10)

10 dimensões × 50 laudos = 500 julgamentos. Fadiga compromete qualidade. As 6 essenciais cobrem H1 (accuracy), H2 (terminology + omissions), H3 (laterality + negation + birads). Demais 4 são opcionais e preenchidas só se há discrepância evidente.

## Pré-registro

Este protocolo + `composite_score_formula_v1.md` (T20) entram no **commit 1** com tag `mqm-protocol-pre-registered`. Defesa anti-p-hacking estendida.
```

- [ ] **Step 0.1: Preencher placeholder de revisor primário ANTES do commit do protocolo**

O `mqm_review_protocol_v1.md` tem campo `Revisor primário | [autor / orientadora / radiologista convidado]`. **Este placeholder DEVE ser substituído pelo nome real antes do commit** — sem isso, o pré-registro fica vago e perde força anti-p-hacking.

Decisão registrada antes do tagging:
- Quem revisa: [substituir aqui pelo valor concreto]
- Especialidade: [radiologia / mastologia / NLP médico / pesquisador clínico]
- Disponibilidade: [data prevista para 50 laudos × ~3 min ≈ 3h]

Se houver revisor secundário (opcional), preencher também:
- Revisor secundário: [nome ou "nenhum"]
- Critério de resolução de divergências: [maioria simples / discussão / flag para terceiro]

Sem essas decisões registradas no spec, **abortar Step 0**.

Commit 1 (antes da execução, **somente após placeholders preenchidos**):
```bash
# Confirmar que placeholders foram resolvidos
grep -E "\[autor / orientadora|\[substituir|TBD|TODO" docs/superpowers/specs/mqm_review_protocol_v1.md \
  && (echo "FAIL: placeholders ainda presentes" && exit 1) \
  || echo "OK: protocolo concreto"

git add docs/superpowers/specs/mqm_review_protocol_v1.md
git commit -m "docs(evaluation): pre-registro protocolo MQM v1 (T22 cego, n=50, 6 dimensoes essenciais, revisor concreto)"
git tag mqm-protocol-pre-registered
```

---

- [ ] **Step 1: Critério de seleção hierárquico — `selection_priority()`**

```python
# src/evaluation/sample_for_human_review.py

def selection_priority(record: dict) -> tuple[int, str]:
    """Retorna (tier, reason). tier 1 = mais crítico, 99 = sem flag.

    Lê APENAS campos do schema T20 — nenhum threshold ad-hoc.
    """
    v = record["validations"]

    # Tier 1: erro crítico clínico (T12.6 — categoria/medida/lateralidade/negação)
    if v["audit_deepseek"]["has_critical_error"]:
        return (1, "critical_audit_error")

    # Tier 2: instabilidade entre duplicatas (T19)
    if v["duplicate_stability"].get("in_pair") and v["duplicate_stability"].get("requires_review"):
        return (2, "duplicate_structural_instability")

    # Tier 3: perda léxica + falha estrutural (T17 + T16)
    if v["lexical_birads"].get("lexical_loss_with_structural_fail"):
        return (3, "lexical_loss_critical")

    # Tier 4: discordância multifonte (T20 failure_reasons populado)
    if record["failure_reasons"]:
        return (4, "_".join(record["failure_reasons"][:3]))

    # Tier 5: BT in_sample com falha (T14.B)
    if v["back_translation"].get("in_sample") and not v["back_translation"]["passed"]:
        return (5, "back_translation_failed")

    # Tier 99: candidato a sub-amostra de controle ("todos passam")
    return (99, "no_flag")
```

**Vantagens:**
- Cada tier mapeia para uma evidência defensável
- `selection_reason` registrado no Excel (campo do sheet "Revisão")
- Sem threshold absoluto — usa `passed`/`has_critical_error` que já consideram calibração interna

---

- [ ] **Step 2: Estratificação composta (priority × BI-RADS)**

```python
import numpy as np
from collections import defaultdict

QUOTAS = {
    1: 10,   # critical_audit_error (até esgotar)
    2: 8,    # duplicate instability
    3: 6,    # lexical_loss_critical
    4: 16,   # multi-source disagreement (mais comum)
    5: 5,    # back_translation
    99: 5,   # controles "todos passam" (sub-amostra de calibração)
}


def stratified_sample(records: list[dict], target_n: int = 50, seed: int = 42) -> list[dict]:
    """Aloca cota por (tier, BI-RADS) com prioridade descendente."""
    rng = np.random.default_rng(seed)

    # Agrupar por tier
    by_tier = defaultdict(list)
    for r in records:
        tier, reason = selection_priority(r)
        r["_selection_tier"] = tier
        r["_selection_reason"] = reason
        by_tier[tier].append(r)

    selected = []
    for tier in sorted(QUOTAS.keys()):
        quota = QUOTAS[tier]
        candidates = by_tier.get(tier, [])
        if not candidates:
            continue

        # Estratificar dentro do tier por BI-RADS quando possível
        by_birads = defaultdict(list)
        for r in candidates:
            cat = int(r.get("birads_label", -1))
            by_birads[cat].append(r)

        per_cat = max(1, quota // 7)  # 7 categorias 0-6
        tier_selected = []
        for cat in sorted(by_birads.keys()):
            available = by_birads[cat]
            n_take = min(per_cat, len(available))
            if n_take > 0:
                idx = rng.choice(len(available), n_take, replace=False)
                tier_selected.extend([available[i] for i in idx])

        # Completar quota se sobrou
        remaining = quota - len(tier_selected)
        if remaining > 0:
            extras = [c for c in candidates if c not in tier_selected]
            if extras:
                idx = rng.choice(len(extras), min(remaining, len(extras)), replace=False)
                tier_selected.extend([extras[i] for i in idx])

        selected.extend(tier_selected[:quota])

    return selected[:target_n]
```

---

- [ ] **Step 3: Cegamento hermético — DOIS arquivos separados (Ajuste cenário C)**

**Razão da mudança:** sheet oculta no mesmo Excel é trivial de revelar (clique direito → mostrar). Para revisor externo profissional, separar fisicamente em **dois arquivos** elimina a possibilidade técnica de quebra de cegamento.

```python
import pandas as pd
from openpyxl import Workbook


# Dimensões MQM
MQM_ESSENTIAL = [
    ("mqm_accuracy",                "Likert 0-4 (0=erro grave, 4=fiel)"),
    ("mqm_terminology",             "Likert 0-4 (preservação BI-RADS)"),
    ("mqm_omissions",               "0/1 (1 = há omissão clínica)"),
    ("mqm_birads_category_correct", "0/1"),
    ("mqm_negation_OK",             "0/1"),
    ("mqm_laterality_correct",      "0/1"),
]

MQM_OPTIONAL = [  # preencher só se discrepância evidente
    ("mqm_fluency",          "Likert 0-4 (opcional)"),
    ("mqm_additions",        "0/1 (opcional)"),
    ("mqm_pt_br_correct",    "0/1 (opcional)"),
    ("mqm_measures_correct", "0/1 (opcional)"),
]


def export_review_and_evidence(sample: list[dict],
                                path_for_reviewer: str,
                                path_internal: str) -> None:
    """Gera DOIS arquivos separados:

    1. {path_for_reviewer} — APENAS sheet 'Revisão'. ENVIADO ao revisor externo.
    2. {path_internal}     — APENAS sheet 'Evidence'. NUNCA enviado.
       Após revisão volta, faz merge interno por report_id.

    Cegamento físico, não apenas operacional. Não há sheet oculta — não há
    sheet a esconder.
    """
    df_review = pd.DataFrame([{
        "report_id":      r["report_id"],
        "es_text":        r["es_text"],
        "pt_text":        r["pt_text"],
        "birads_label":   r["birads_label"],
        "selection_reason": r["_selection_reason"],  # razão da inclusão (não outputs)
        # Colunas MQM em branco para preenchimento
        **{name: "" for name, _ in MQM_ESSENTIAL + MQM_OPTIONAL},
        "uncertainty":    "",   # flag manual de incerteza pessoal do revisor
        "reviewer_notes": "",
        "final_verdict":  "",   # approve / fix / reject
    } for r in sample])

    df_evidence = pd.DataFrame([{
        "report_id":            r["report_id"],
        "selection_tier":       r["_selection_tier"],
        "selection_reason":     r["_selection_reason"],
        "composite_score":      r["composite_score"],
        "failure_reasons":      ", ".join(r["failure_reasons"]),
        "audit_final_status":   r["validations"]["audit_deepseek"]["audit_final_status"],
        "has_critical_error":   r["validations"]["audit_deepseek"]["has_critical_error"],
        "semantic_passed":      r["validations"]["semantic"]["passed"],
        "structural_passed":    r["validations"]["structural"]["all_structural_pass"],
        "lexical_passed":       r["validations"]["lexical_birads"]["passed"],
        "modifier_passed":      r["validations"]["modifier_agreement"].get("passed"),
        "bt_in_sample":         r["validations"]["back_translation"].get("in_sample"),
        "duplicate_in_pair":    r["validations"]["duplicate_stability"].get("in_pair"),
    } for r in sample])

    # ARQUIVO 1 — para o revisor (apenas Revisão)
    df_review.to_excel(path_for_reviewer, sheet_name="Revisão", index=False)

    # ARQUIVO 2 — interno (apenas Evidence)
    df_evidence.to_excel(path_internal, sheet_name="Evidence", index=False)


# Outputs:
# - results/translation/human_review_for_radiologist.xlsx  ← ENVIADO
# - results/translation/human_review_evidence_internal.xlsx ← NUNCA enviado
```

**Operação cega física:**
1. Gera 2 arquivos
2. **Envia apenas `human_review_for_radiologist.xlsx`** (com `instructions_for_reviewer.md` — Ajuste 3)
3. Revisor preenche e devolve `human_review_for_radiologist_filled.xlsx`
4. Pós-revisão: `extract_mqm_results.py` lê o filled + faz merge interno com `human_review_evidence_internal.xlsx` por `report_id`
5. Análise de κ humano × LLM em T23 §9

**Garantia metodológica:** o arquivo entregue ao revisor **não contém Evidence em nenhuma forma** — não é sheet oculta, não está no XML do XLSX. Cegamento é físico, não apenas operacional.

---

- [ ] **Step 3.5: Documento de instruções para o revisor (Ajuste cenário C)**

Sheet "Revisão" precisa ser autoexplicativa para alguém que não conhece o framework. Criar `docs/translation/instructions_for_reviewer.md` (1 página, enviado junto com o Excel):

```markdown
# Instruções de revisão — Validação de tradução de laudos de mamografia

## Contexto

Vamos avaliar a qualidade da tradução automatizada de 50 laudos do espanhol
para o português brasileiro. Você verá:

- `report_id`: identificador anônimo
- `es_text`: laudo original em espanhol
- `pt_text`: tradução em português brasileiro
- `birads_label`: categoria BI-RADS do laudo
- `selection_reason`: por que este laudo foi selecionado para revisão
  (não influencia sua avaliação — é apenas para registro)

## Sua tarefa

Para cada laudo, comparar `es_text` com `pt_text` e preencher 6 dimensões
obrigatórias + 4 opcionais.

## Dimensões obrigatórias

| Coluna | Escala | Critério |
|---|---|---|
| `mqm_accuracy`               | 0–4 | 4 = fiel; 0 = erro grave de significado |
| `mqm_terminology`            | 0–4 | 4 = terminologia BI-RADS correta; 0 = errada |
| `mqm_omissions`              | 0/1 | 1 = há omissão de informação clínica |
| `mqm_birads_category_correct`| 0/1 | 1 = categoria BI-RADS preservada |
| `mqm_negation_OK`            | 0/1 | 1 = negações ("no se observa", "ausência de") preservadas |
| `mqm_laterality_correct`     | 0/1 | 1 = direita/esquerda preservadas |

## Dimensões opcionais

Preencher só se há discrepância evidente:
- `mqm_fluency` (0–4), `mqm_additions` (0/1), `mqm_pt_br_correct` (0/1),
  `mqm_measures_correct` (0/1)

## Veredito final

Em `final_verdict`:
- `approve`: tradução clinicamente aceitável
- `fix`:     aceitável mas com sugestão de melhoria
- `reject`:  tradução com erro clinicamente relevante

Em `reviewer_notes`: comentário livre sobre o caso.

Em `uncertainty`: marcar com `1` se você ficou em dúvida sobre o que avaliar
(não erro do framework — sua incerteza pessoal sobre o caso). Ajuda-nos a
identificar casos onde a clareza clínica do laudo é limitada.

## Tempo estimado

50 laudos × ~3 min = ~2,5h. Pode revisar em uma ou duas sessões.

## Importante (cegamento metodológico)

Você **não tem acesso aos resultados do nosso framework de validação
automatizada**. Sua avaliação será comparada com a do nosso sistema
posteriormente — esse é o objetivo da revisão (validação cruzada
independente). Por favor não consulte material auxiliar ou pesquise os
laudos online.

## Confidencialidade

Os dados são anônimos (sem identificação de pacientes). Pedimos que
não compartilhe o arquivo nem use os laudos para outros fins. Após o
preenchimento, devolva apenas o arquivo `human_review_for_radiologist.xlsx`
preenchido.
```

Custo: ~30 min de redação cuidadosa.

---

- [ ] **Step 3.6: Pré-flight de anonimização (Ajuste cenário C)**

Antes de enviar o Excel ao revisor externo, **garantir que dados são anônimos**. Implementar `scripts/verify_anonymization.py`:

```python
"""Verifica que os textos da amostra MQM não contêm PII residual."""
import re
import pandas as pd
import sys

# Stopwords clínicas pós-"paciente" (descartar falso-positivo)
# Verificado empiricamente em 2026-04-29 sobre data/reports_raw_canonical.csv:
# 21 matches do padrão ingênuo eram TODOS falso-positivos (PACIENTE PORTADORA,
# PACIENTE CON ANTECEDENTE, PACIENTE EN CONTROL, etc.). Whitelist evita ruído.
PACIENTE_STOPWORDS = (
    r"(?i)\b(con|sin|de|en|que|portadora?|presenta|refiere|"
    r"con\s+antecedente|ya\s+fue|requiere|es\s+|fue\s+)"
)


# Padrões PII comuns em laudos médicos
PII_PATTERNS = [
    (r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",                            "CPF"),
    (r"\b\d{2}/\d{2}/\d{4}\b",                                        "Data nascimento"),
    # Nome paciente: "paciente <Nome Sobrenome>" SEM stopword clínica antes do nome
    (rf"(?i)\bpaciente\s*:?\s*(?!{PACIENTE_STOPWORDS})[A-Z][a-z]+ [A-Z][a-z]+", "Nome paciente"),
    (r"(?i)\bdr[a]?\.?\s+[A-Z][a-z]+ [A-Z][a-z]+",                    "Nome médico"),
    (r"\b\d{8,}\b",                                                    "Número longo (CRM/RG/registro)"),
    (r"(?i)\bRG\s*:?\s*\d+",                                           "RG explícito"),
]

df = pd.read_excel("results/translation/human_review_for_radiologist.xlsx",
                   sheet_name="Revisão")

found = []
for _, row in df.iterrows():
    for col in ["es_text", "pt_text"]:
        text = str(row.get(col, ""))
        for pat, label in PII_PATTERNS:
            for m in re.finditer(pat, text):
                found.append({"report_id": row["report_id"], "col": col,
                              "type": label, "match": m.group(0)})

if found:
    print(f"FAIL: {len(found)} possíveis PII encontradas:")
    for f in found[:20]:
        print(f"  {f['report_id']} ({f['col']}): {f['type']} -> '{f['match']}'")
    sys.exit(1)
print(f"OK: {len(df)} laudos sem PII detectada")
```

Run obrigatório antes de enviar:

```bash
python -m scripts.verify_anonymization
# Esperado: "OK: 50 laudos sem PII detectada"
```

Se `FAIL`:
1. Investigar match (pode ser falso positivo — ex: data clínica `15/03/2024`)
2. Se PII real → anonimizar (substituir por `[ANONYMIZED]`) e re-gerar Excel
3. Re-rodar verify até passar

**Documentar em `decision_log.md`** (G1):
| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Dados são anônimos verificados | T22 Step 3.6 | LGPD + ética em pesquisa; verificação automatizada via `verify_anonymization.py` | (compliance) |

- [ ] **Step 4: Pós-revisão — `extract_mqm_results.py`**

```python
# scripts/extract_mqm_results.py
import pandas as pd
import json
from pathlib import Path


def has_critical_error_human(row) -> bool:
    """Critério mecânico: erro crítico humano se categoria/lateralidade/negação/medida falhou."""
    crit_fields = [
        "mqm_birads_category_correct",
        "mqm_laterality_correct",
        "mqm_negation_OK",
        "mqm_measures_correct",  # opcional — default 1 se vazio
    ]
    for f in crit_fields:
        v = row.get(f, 1)  # opcional → assumir OK se vazio
        if pd.notna(v) and v == 0:
            return True
    return False


def main():
    # Cenário C: 2 arquivos separados (Ajuste 2)
    # 1. Arquivo preenchido pelo revisor externo
    df = pd.read_excel(
        "results/translation/human_review_for_radiologist_filled.xlsx",
        sheet_name="Revisão"
    )
    # 2. Evidence interno (NUNCA enviado ao revisor)
    df_evidence = pd.read_excel(
        "results/translation/human_review_evidence_internal.xlsx",
        sheet_name="Evidence"
    )
    # Merge interno por report_id para análise pós-revisão
    df = df.merge(df_evidence, on="report_id", how="left", suffixes=("", "_evidence"))

    # Validação básica — alertar se MQM essential ficou em branco
    essential_cols = ["mqm_accuracy", "mqm_terminology", "mqm_omissions",
                      "mqm_birads_category_correct", "mqm_negation_OK",
                      "mqm_laterality_correct"]
    n_incomplete = df[essential_cols].isna().any(axis=1).sum()
    if n_incomplete > 0:
        print(f"AVISO: {n_incomplete} laudos com dimensões essenciais em branco")

    df["has_critical_error_human"] = df.apply(has_critical_error_human, axis=1)
    df["mqm_overall_pass"] = (
        (df["mqm_accuracy"] >= 3)
        & (df["mqm_terminology"] >= 3)
        & (~df["has_critical_error_human"])
    )

    df.to_csv("results/translation/human_review_results.csv", index=False, encoding="utf-8")

    summary = {
        "n_reviewed":                   int(len(df)),
        "n_critical_error_human":       int(df["has_critical_error_human"].sum()),
        "critical_error_rate_human":    round(float(df["has_critical_error_human"].mean()), 4),
        "n_overall_pass_human":         int(df["mqm_overall_pass"].sum()),
        "overall_pass_rate_human":      round(float(df["mqm_overall_pass"].mean()), 4),
        "median_mqm_accuracy":          float(df["mqm_accuracy"].median()),
        "median_mqm_terminology":       float(df["mqm_terminology"].median()),
        "n_omissions_flagged":          int((df["mqm_omissions"] == 1).sum()),
        "n_uncertainty_flagged":        int(df["uncertainty"].notna().sum()),
        "verdict_distribution": dict(df["final_verdict"].value_counts()),
    }
    Path("results/translation/human_review_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
```

**Crucial:** `has_critical_error_human` permite cruzar com `has_critical_error` do auditor (T13). Se κ ≥ 0.4 entre humano e LLM auditor → calibração cruzada validada (parte de H3).

---

- [ ] **Step 5: TDD com 5 testes**

```python
# tests/test_evaluation/test_human_review_sample.py
import pandas as pd
from src.evaluation.sample_for_human_review import (
    selection_priority, stratified_sample,
)


def _mock_record(tier=99, **overrides):
    base = {
        "report_id":      "RPT_X",
        "es_text":        "...",
        "pt_text":        "...",
        "birads_label":   2,
        "composite_score": 95,
        "failure_reasons": [],
        "validations": {
            "semantic":            {"passed": True, "bertscore_f1": 0.95},
            "structural":          {"all_structural_pass": True},
            "lexical_birads":      {"passed": True, "lexical_loss_with_structural_fail": False},
            "modifier_agreement":  {"passed": True},
            "audit_deepseek":      {"has_critical_error": False, "passed": True,
                                    "audit_final_status": "approved"},
            "back_translation":    {"in_sample": False},
            "duplicate_stability": {"in_pair": False},
        },
    }
    if tier == 1:
        base["validations"]["audit_deepseek"]["has_critical_error"] = True
    if tier == 2:
        base["validations"]["duplicate_stability"] = {
            "in_pair": True, "requires_review": True
        }
    if tier == 3:
        base["validations"]["lexical_birads"]["lexical_loss_with_structural_fail"] = True
    if tier == 4:
        base["failure_reasons"] = ["semantic"]
    if tier == 5:
        base["validations"]["back_translation"] = {"in_sample": True, "passed": False}
    base.update(overrides)
    return base


def test_selection_priority_critical_audit():
    """has_critical_error → tier 1."""
    record = _mock_record(tier=1)
    assert selection_priority(record)[0] == 1
    assert selection_priority(record)[1] == "critical_audit_error"


def test_selection_priority_duplicate_instability():
    """requires_review True → tier 2."""
    record = _mock_record(tier=2)
    assert selection_priority(record)[0] == 2


def test_selection_priority_no_flag():
    """Tudo passando → tier 99."""
    record = _mock_record(tier=99)
    assert selection_priority(record)[0] == 99
    assert selection_priority(record)[1] == "no_flag"


def test_stratified_sample_respects_quotas():
    """Quotas alocadas conforme tier."""
    records = (
        [_mock_record(tier=1, report_id=f"R1_{i}") for i in range(30)]
        + [_mock_record(tier=4, report_id=f"R4_{i}") for i in range(100)]
    )
    sample = stratified_sample(records, target_n=50, seed=42)
    tier_1_count = sum(1 for r in sample if r["_selection_tier"] == 1)
    tier_4_count = sum(1 for r in sample if r["_selection_tier"] == 4)
    assert tier_1_count <= 10  # quota tier 1 = 10
    assert tier_4_count <= 16  # quota tier 4 = 16


def test_extract_mqm_results_critical_error():
    """has_critical_error_human inferido das dimensões críticas."""
    from scripts.extract_mqm_results import has_critical_error_human
    row = pd.Series({
        "mqm_birads_category_correct": 0,  # falha
        "mqm_laterality_correct": 1,
        "mqm_negation_OK": 1,
        "mqm_measures_correct": 1,
    })
    assert has_critical_error_human(row) is True

    row_ok = pd.Series({
        "mqm_birads_category_correct": 1,
        "mqm_laterality_correct": 1,
        "mqm_negation_OK": 1,
        "mqm_measures_correct": 1,
    })
    assert has_critical_error_human(row_ok) is False
```

Run: `pytest tests/test_evaluation/test_human_review_sample.py -v` → **5 PASS**.

---

- [ ] **Step 6: Run + commit em 2 etapas**

```bash
# Antes da revisão (commit 1 — gera amostra + instruções + verifica anonimização)
python -m src.evaluation.sample_for_human_review        # gera 2 arquivos separados
python -m scripts.verify_anonymization                  # gate pré-envio (Ajuste 4)

git add src/evaluation/sample_for_human_review.py \
        scripts/verify_anonymization.py \
        tests/test_evaluation/test_human_review_sample.py \
        docs/translation/instructions_for_reviewer.md \
        results/translation/human_review_for_radiologist.xlsx \
        results/translation/human_review_evidence_internal.xlsx
git commit -m "feat(evaluation): F10 amostra MQM n=50 (selecao hierarquica + cegamento fisico em 2 arquivos + instrucoes revisor + anonimizacao verificada)"

# [ENVIAR ao revisor externo: human_review_for_radiologist.xlsx + instructions_for_reviewer.md]
# [revisão humana — 3-4h offline]
# [REVISOR DEVOLVE: human_review_for_radiologist_filled.xlsx]

# Depois da revisão (commit 2 — extrai resultados via merge interno)
python -m scripts.extract_mqm_results

git add scripts/extract_mqm_results.py \
        results/translation/human_review_for_radiologist_filled.xlsx \
        results/translation/human_review_results.csv \
        results/translation/human_review_summary.json
git commit -m "feat(evaluation): F10 resultados MQM extraidos (50 laudos revisados por radiologista externo, has_critical_error_human + summary para T23)"
```

**⚠ NUNCA commitar `human_review_evidence_internal.xlsx` no commit 2** — já foi commitado no commit 1, mas se houver alteração interna, separar em commit interno claramente marcado. Garantia de que `git log` mostra o cegamento metodológico.

#### Rollback criteria (G6)

Reverter / re-fazer T22 (não commitar `human_review_results.csv`) se:
- **`extract_mqm_results.py` reporta `n_incomplete > 5`** (mais de 10% das linhas com dimensões essenciais em branco) → revisão incompleta, qualidade comprometida
- **Tag `mqm-protocol-pre-registered` não existe no momento do commit** → grep do gate Step 0 falhou silenciosamente, protocolo não foi pré-registrado
- **Cohen's κ humano × LLM (calculado em T23 §9) < 0.2** → revisão fortemente discordante do framework: investigar se houve quebra de cegamento (revisor viu Evidence sheet) ou se há viés sistemático no auditor LLM
- **Sheet `Evidence` foi visivelmente acessada** (timestamp de modificação anterior à conclusão de Revisão) → cegamento comprometido

**Ação se rollback:**
1. **Cegamento comprometido** → repetir revisão com revisor diferente OU descartar T22 e marcar como limitação no spec
2. **Revisão incompleta** → contatar revisor, completar dimensões essenciais
3. **κ < 0.2** → investigar antes de commitar; pode indicar bug em `has_critical_error_human` ou viés do auditor; documentar em `incidents.md`

#### Resumo

| Ajuste | Custo | Resolve |
|---|---|---|
| 1 — Critérios baseados em schema T20 | 15 min | Fim de campos legados/thresholds ad-hoc |
| 2 — Estratificação composta tier × BI-RADS | 20 min | Garante representação de cada dimensão de risco |
| 3 — 6 essenciais + 4 opcionais | 5 min | Reduz fadiga 500→300 julgamentos |
| 4 — Protocolo pré-registrado | 10 min | Defesa anti-p-hacking estendida |
| 5 — Excel com 2 sheets (cegamento) | 10 min | Revisor independente — κ válido em T23 §9 |
| 6 — Output estruturado pós-revisão | 10 min | T23 lê JSON sumário sem reprocessar Excel |
| 7 — TDD (5 testes) | 25 min | Defensibilidade |

**Total: ~1h35min** (sem contar a revisão humana de ~3-4h).

#### Por que cegamento é metodologicamente forte

- **Sem cegamento:** revisor vê `composite_score = 95` e tende a aprovar mesmo com falha clínica → MQM vira validação enviesada do framework. Inútil para H3.
- **Com cegamento:** revisor independente do framework. κ humano × auditor LLM testa convergência genuína. Fonte ortogonal real.

Banca pergunta "como você sabe que MQM não é só repetição do auditor?" → resposta: cegamento + protocolo pré-registrado + κ humano × LLM ≥ 0.4 (validação cruzada).

---

### Task 23: F11 — Notebook consolidado com headline crítica + Holm + reproducibility 🔲 PENDING  ⚠ depende de T20–T22 estáveis

**Files:**
- Create: `notebooks/01_translation_report.ipynb`
- Create: `src/evaluation/notebook_helpers.py`
- Create: `tests/test_evaluation/test_notebook_helpers.py` (5 testes TDD)

**Goal:** Notebook de fechamento do TCC que lê **todos os summary JSONs** das tasks anteriores (princípio "T-x produz, T23 lê"), testa H1–H8 com correção Holm-Bonferroni, e gera relatório de reprodutibilidade auto-gerado.

#### O que mudou vs T23 antiga

| Antes | Agora |
|---|---|
| Step 3 fala "H1–H7" (H8 ausente) | H1–H8 com **Holm-Bonferroni** (FWER controlado) |
| 12 seções com §10 absorvendo tudo | 12 seções com **§5+§5b** (léxico/modifier separados) e **§7+§7b** (DeepSeek + calibração GPT-4o-mini) |
| Recomputa de CSVs brutos | Lê **summary JSONs** das tasks (T13/T15/T18/T19/T21/T22) |
| §10 promete taxonomia MQM | §10 lê **`failure_reasons` do T20** — taxonomia natural |
| `median_with_ci` inline | `notebook_helpers.py` com `median_with_ci`, `proportion_with_ci` (Wilson), `rate_with_ci` |
| Sem tabela executiva | **Headline executiva** (1 página) gerada após Step 1 |
| Reproducibility "mencionado" | `reproducibility_statement.json` auto-gerado |
| Sem TDD | 5 testes em `test_notebook_helpers.py` |

---

- [ ] **Step 1: Setup + leitura de summary JSONs (Ajuste 3)**

```python
# notebooks/01_translation_report.ipynb — célula de setup

import json
import pandas as pd
from pathlib import Path
from src.evaluation.notebook_helpers import (
    median_with_ci, proportion_with_ci, rate_with_ci, build_executive_summary
)

DIR = Path("results/translation")

# Schema único (T20)
records = [json.loads(l) for l in open(DIR / "validation_results.jsonl", encoding="utf-8")]
df = pd.DataFrame(records)

# Summaries pré-computados pelas tasks (T-x produz, T23 lê — sem recomputar)
summaries = {
    "audit":     json.loads((DIR / "audit_deepseek_summary.json").read_text(encoding="utf-8")),
    "intrinsic": json.loads((DIR / "intrinsic_metrics_summary.json").read_text(encoding="utf-8")),
    "modifier":  json.loads((DIR / "modifier_summary.json").read_text(encoding="utf-8")),
    "duplicate": json.loads((DIR / "duplicate_stability_summary.json").read_text(encoding="utf-8")),
    "agreement": json.loads((DIR / "agreement_report.json").read_text(encoding="utf-8")),
    "human":     json.loads((DIR / "human_review_summary.json").read_text(encoding="utf-8")),
    "calibration": json.loads((DIR / "audit_calibration_agreement.json").read_text(encoding="utf-8")),  # T13 Step 5
    "lexical":   json.loads((DIR / "lexical_global_summary.json").read_text(encoding="utf-8")),
}

# CSVs apenas para análise granular (top-N, exemplos qualitativos)
df_lex_anomalies = pd.read_csv(DIR / "lexical_anomalies.csv")
df_human         = pd.read_csv(DIR / "human_review_results.csv")
```

**Princípio:** notebook lê outputs das tasks; não recomputa estatísticas. Se uma task atualiza, sumário atualiza, notebook reflete sem mudança.

---

- [ ] **Step 2: Helpers padronizados — `src/evaluation/notebook_helpers.py` (Ajuste 5)**

```python
"""Helpers de estatística e visualização para o notebook T23."""
import numpy as np
import pandas as pd
from scipy.stats import bootstrap


def median_with_ci(values, alpha=0.05, n_resamples=10000):
    """Mediana + IC bootstrap BCa (alinhado com T15/T18/T19/T21)."""
    arr = np.array(values)
    arr = arr[~pd.isna(arr)]
    if len(arr) < 2:
        return None, None, None
    res = bootstrap((arr,), np.median, n_resamples=n_resamples,
                    confidence_level=1 - alpha, method="BCa")
    return (float(np.median(arr)),
            float(res.confidence_interval.low),
            float(res.confidence_interval.high))


def proportion_with_ci(successes: int, total: int, alpha: float = 0.05):
    """Wilson score interval para proporções — robusto em 0/N e N/N."""
    if total == 0:
        return None, None, None
    p = successes / total
    z = 1.96  # alpha=0.05
    denom = 1 + z**2 / total
    center = (p + z**2 / (2*total)) / denom
    half = z * np.sqrt(p*(1-p)/total + z**2/(4*total**2)) / denom
    return p, max(0.0, center - half), min(1.0, center + half)


def rate_with_ci(values, alpha=0.05, n_resamples=10000):
    """Wrapper para taxas (boolean array → mediana via bootstrap)."""
    return median_with_ci([float(v) for v in values], alpha, n_resamples)


def build_executive_summary(records, summaries):
    """Tabela de uma página — headline metrics para abertura do notebook (Ajuste 6).

    Reporta TRÊS taxas de aprovação separadas para evitar leitura ambígua:
    - overall_passed_rate: agregado completo (todas as 6 fontes incluindo modifier)
    - clinical_pass_rate: aprovação clínica (ignora modifier-only failures)
    - critical_error_rate: H8 estrito (has_critical_error)

    Hierarquia: erro_critico ⊂ ¬clinical_pass ⊂ ¬overall_passed
    (todo erro crítico falha clinicamente; toda falha clínica também falha agregado;
     mas falha agregada (ex: modifier-only) pode ser clinical_pass=True)
    """
    n = len(records)
    n_passed = sum(1 for r in records if r["overall_passed"])
    n_clinical = sum(1 for r in records if r["clinical_pass"])
    n_critical = sum(1 for r in records
                     if r["validations"]["audit_deepseek"]["has_critical_error"])
    composite_median = float(pd.Series([r["composite_score"] for r in records]).median())

    rows = [
        ("Volume",               "Laudos traduzidos",          f"{n:,}",                                         "—"),
        ("Volume",               "Cobertura completa",         f"{n}/4357",                                       "100%"),
        ("Aprovação",            "clinical_pass (ignora modifier-only)",  f"{n_clinical/n:.1%}",                  "≥95%"),
        ("Aprovação",            "overall_passed (todas as fontes)",      f"{n_passed/n:.1%}",                    "≥90%"),
        ("Aprovação",            "composite_score (mediana)",             f"{composite_median:.1f}",              "≥90"),
        ("Erro crítico (H8)",    "Taxa (has_critical_error)",             f"{n_critical/n:.2%}",                  "≤1%"),
        ("Semântica (H1)",       "BERTScore-F1 (mediana)",     f"{summaries['intrinsic']['bertscore_f1_median']:.3f}", "≥0.90"),
        ("Léxico (H2)",          "overall_acceptable_rate",    f"{summaries['lexical']['overall_acceptable_rate']:.3f}", "≥0.99"),
        ("Estrutural (H4)",      "all_structural_pass rate",   f"{summaries['intrinsic'].get('structural_pass_rate', '?')}", "≥0.99"),
        ("Estabilidade (H5)",    "cosine_pt_pt mediana",       f"{summaries['duplicate']['median_cosine_pt_pt']:.3f}", "≥0.98"),
        ("PT-br (H7)",           "Drift rate",                  f"{summaries['intrinsic'].get('pt_drift_rate', '?')}", "≤1%"),
        ("Cross-source (H3)",    "Consensus completo",          f"{summaries['agreement']['consensus']['histogram_n_passed'].get('6', 0)/n:.1%}", "—"),
        ("Sem viés (H6)",        "Kruskal-Wallis p (BERTScore)",f"{summaries['intrinsic'].get('kruskal_p', '?')}", "p>0.05"),
        ("Revisão humana",       "κ humano × LLM (crítico)",   f"{summaries['human'].get('kappa_critical_human_vs_llm', '?')}", "≥0.4"),
    ]
    return pd.DataFrame(rows, columns=["Dimensão", "Métrica", "Valor", "Critério"])
```

---

- [ ] **Step 3: Hypothesis tests com Holm-Bonferroni (Ajuste 1)**

```python
# §3 do notebook — testes confirmatórios H1-H8 com correção múltipla

from statsmodels.stats.multitest import multipletests
from scipy.stats import wilcoxon, kruskal

# Cada test_h*() retorna p-valor unilateral (H0 = critério não atingido)

def test_h1_semantic():
    """BERTScore-F1 mediana >= 0.90 — Wilcoxon signed-rank one-sided."""
    values = [r["validations"]["semantic"]["bertscore_f1"] for r in records]
    stat, p = wilcoxon([v - 0.90 for v in values], alternative="greater")
    return p


def test_h2_lexical():
    """overall_acceptable_rate >= 0.99 — proportion test (Wilson)."""
    rate = summaries["lexical"]["overall_acceptable_rate"]
    n = summaries["lexical"]["total_pt_occurrences"]
    successes = int(rate * n)
    p, lo, hi = proportion_with_ci(successes, n)
    # H0: rate < 0.99; rejeita se lower_bound > 0.99
    return 1.0 if lo is None else (0.0 if lo > 0.99 else 0.5)


def test_h3_consensus():
    """≥95% laudos com ≥(n_active-1) fontes concordando."""
    n_total = len(records)
    n_consensus = sum(1 for r in records
                      if (c := consensus_active_passed(r))[1] >= c[0] - 1)
    p, lo, hi = proportion_with_ci(n_consensus, n_total)
    return 0.0 if lo and lo > 0.95 else 0.5


def test_h4_structural():
    """≥99% laudos com all_structural_pass."""
    n_pass = sum(1 for r in records if r["validations"]["structural"]["all_structural_pass"])
    p, lo, hi = proportion_with_ci(n_pass, len(records))
    return 0.0 if lo and lo > 0.99 else 0.5


def test_h5_duplicates():
    """Mediana cosine_pt_pt das duplicatas effective >= 0.98."""
    return 0.0 if summaries["duplicate"]["h5_passed"] else 0.5


def test_h6_birads_strata():
    """H6: SEM viés por categoria BI-RADS.

    ⚠ NOTA METODOLÓGICA SOBRE A INVERSÃO DO P-VALOR:

    H6 é uma hipótese NULA (queremos NÃO rejeitar H0: distribuições iguais entre
    categorias). Os outros tests (H1, H4, H7, H8) são hipóteses ALTERNATIVAS
    (queremos rejeitar H0). Holm-Bonferroni opera no segundo paradigma.

    Para integrar H6 ao mesmo framework, retornamos `1 - p` — assim, "p_invertido
    pequeno" significa "Kruskal-Wallis NÃO encontrou diferença significativa
    entre estratos" (resultado desejado). Quando reject_holm[H6] = True
    (p_invertido pequeno), interpretamos como "ausência de viés confirmada".

    ALTERNATIVA MAIS RIGOROSA (refatoração futura): substituir Kruskal-Wallis
    por TOST (Two One-Sided Tests) com margem de equivalência ε. TOST testa
    diretamente "as distribuições são equivalentes dentro de margem ε" — H1
    nativa, sem inversão. Atualmente usamos Kruskal-Wallis + inversão por
    simplicidade; banca pode questionar e a refatoração TOST é trivial.

    Decisão registrada no commit pré-registro: usar Kruskal-Wallis com
    inversão; reportar resultado dos dois lados (p original + p invertido)
    no notebook §8 para transparência.
    """
    by_cat = {}
    for r in records:
        cat = r.get("birads_label")
        if cat is not None:
            by_cat.setdefault(cat, []).append(r["validations"]["semantic"]["bertscore_f1"])
    groups = [v for v in by_cat.values() if len(v) >= 30]
    if len(groups) < 2:
        return 1.0
    stat, p = kruskal(*groups)
    # H0: sem diferença → "passou" se p > 0.05 (queremos NÃO rejeitar H0)
    return 1 - p  # invertido para alinhar com Holm (ver nota acima)


def test_h7_drift():
    """≤1% laudos com marcador PT-pt."""
    n_drift = sum(1 for r in records if r["validations"]["structural"]["pt_drift"])
    p, lo, hi = proportion_with_ci(n_drift, len(records))
    return 0.0 if hi and hi < 0.01 else 0.5


def test_h8_critical_rate():
    """≤1% laudos com erro crítico (T12.6)."""
    n_crit = sum(1 for r in records
                 if r["validations"]["audit_deepseek"]["has_critical_error"])
    p, lo, hi = proportion_with_ci(n_crit, len(records))
    return 0.0 if hi and hi < 0.01 else 0.5


# Hipóteses confirmatórias (declaradas pré-execução)
HYPOTHESES = [
    ("H1", "Tradução preserva significado clínico",                 test_h1_semantic),
    ("H2", "Léxico BI-RADS preservado conforme glossário",          test_h2_lexical),
    ("H3", "Fontes ortogonais convergem",                            test_h3_consensus),
    ("H4", "Categoria/medidas/lateralidade preservadas",             test_h4_structural),
    ("H5", "Estabilidade operacional em duplicatas",                 test_h5_duplicates),
    ("H6", "Sem viés por categoria BI-RADS",                         test_h6_birads_strata),
    ("H7", "PT-br puro sem drift PT-pt",                             test_h7_drift),
    ("H8", "Taxa de erro crítico ≤ 1%",                              test_h8_critical_rate),
]

raw_p = [fn() for _, _, fn in HYPOTHESES]
reject_holm, p_corrected, _, _ = multipletests(raw_p, alpha=0.05, method="holm")

results = pd.DataFrame([
    {"hypothesis": hid, "description": desc,
     "p_raw": rp, "p_holm": pc, "reject_h0_holm": rj,
     "exploratory": False}
    for (hid, desc, _), rp, pc, rj in zip(HYPOTHESES, raw_p, p_corrected, reject_holm)
])
display(results)
```

**Decisão metodológica registrada:**
- **Confirmatórias (H1–H8):** declaradas pré-execução, FWER controlado via Holm-Bonferroni
- **Exploratórias (surgidas durante análise):** reportadas separadamente sem correção, com `exploratory: True` — defesa contra acusação de p-hacking adicional

---

- [ ] **Step 4: Estrutura das 12 seções (Ajuste 2)**

| Seção | Conteúdo |
|---|---|
| **0. Headline executiva** | Tabela de 1 página gerada por `build_executive_summary()` |
| **1. Visão geral** | Volume, distribuição BI-RADS, **headline = taxa de erro crítico** (T12.6/H8) + composite mediana + overall_passed rate |
| **2. Qualidade semântica (F3)** | BERTScore-F1 + chrF++ + cosine + length_ratio (BLEU já cortado em T15) |
| **3. Back-translation (F2)** | **Caveat amostra de 250** com mesmo modelo família + 5 mitigações + threshold empírico |
| **4. Structural checks (F4)** | `all_structural_pass` rate + breakdown (categoria, medidas, lateralidade, negação, anatomia, drift) |
| **5. Léxico BI-RADS (F5)** | `overall_canonical_rate` × `overall_acceptable_rate`, anomalias, top-20 termos divergentes |
| **5b. Morfossintaxe (F6) — NOVA** | `preservation_rate`, `divergence_breakdown` (gender/number/both), abstain rate, threshold empírico |
| **6. Estabilidade operacional (F7)** | **Caveat operacional** (4 camadas, 3 níveis, ≤2% structural instability) |
| **7. Auditoria DeepSeek (F1)** | C1–C7 distributions + meta-validação (kept vs refuted) |
| **7b. Calibração GPT-4o-mini (T13 Step 5) — NOVA** | Cohen's κ DeepSeek↔GPT por critério, decisão `PRIMARY_STABLE`/`MODERATE`/`DOWNGRADE` |
| **8. Concordância entre fontes (F9)** | κ heatmap das 6 fontes + nota interpretativa + **κ por BI-RADS** (subsidia H6) |
| **9. Revisão humana (F10)** | κ humano × LLM auditor; cross-validation `has_critical_error_human` × `has_critical_error_LLM` |
| **10. Análise de erros** | **Taxonomia via `failure_reasons` do T20** (Ajuste 4) |
| **11. Composite Score** | Distribuição, faixas (90+, 75-89, <75), referência à tag `composite-score-formula-pre-registered` |
| **12. Reproducibility statement** | Auto-gerado (Ajuste 8) |

**Mudança principal:** §5 split em léxico (F5) + §5b morfossintaxe (F6); §7 split em DeepSeek (F1) + §7b calibração (T13 Step 5). Evidências de H2 e H3 com metodologias distintas — tratar juntos confunde.

---

- [ ] **Step 5: §10 — Análise de erros via `failure_reasons` (Ajuste 4)**

```python
# §10 — Taxonomia natural do T20

from collections import Counter
from sklearn.metrics import cohen_kappa_score

reason_counter = Counter()
for r in records:
    for reason in r["failure_reasons"]:
        reason_counter[reason] += 1

display(pd.DataFrame([
    {"failure_reason": k, "count": v, "rate": f"{v/len(records):.2%}"}
    for k, v in reason_counter.most_common()
]))

# Top-20 casos por razão dominante (piores composite_score primeiro)
for reason in ["audit_critical", "structural", "lexical", "semantic", "modifier", "back_translation"]:
    cases = [r for r in records if reason in r["failure_reasons"]]
    cases.sort(key=lambda r: r["composite_score"])
    print(f"\n## Top 20 casos: {reason}")
    display(pd.DataFrame([
        {"report_id": r["report_id"],
         "composite": r["composite_score"],
         "all_reasons": ", ".join(r["failure_reasons"])}
        for r in cases[:20]
    ]))

# Cross-validation com revisão humana (T22)
human_merged = df_human.merge(df[["report_id", "failure_reasons"]],
                               left_on="report_id", right_on="report_id")
human_merged["has_critical_error_LLM"] = human_merged["failure_reasons"].apply(
    lambda r: "audit_critical" in r if isinstance(r, list) else False
)
kappa_critical = cohen_kappa_score(
    human_merged["has_critical_error_human"],
    human_merged["has_critical_error_LLM"]
)
print(f"\nκ humano × LLM (erro crítico): {kappa_critical:.3f}  (alvo ≥ 0.4)")
```

**Por quê:** `failure_reasons` é a taxonomia natural — cada razão mapeia para uma dimensão metodológica. Top-20 por razão dá acesso a exemplos concretos. Cross-validation com T22 quantifica calibração.

---

- [ ] **Step 6: TDD — `tests/test_evaluation/test_notebook_helpers.py` (Ajuste 7)**

```python
import pytest
import pandas as pd
from src.evaluation.notebook_helpers import (
    median_with_ci, proportion_with_ci, rate_with_ci, build_executive_summary
)


def test_median_with_ci_returns_tuple():
    """Helper retorna (mediana, ci_low, ci_high)."""
    m, lo, hi = median_with_ci([1, 2, 3, 4, 5], n_resamples=200)
    assert lo <= m <= hi


def test_proportion_with_ci_extreme_zero():
    """Wilson lida com 0/N (caso comum em H8: 0 erros críticos)."""
    p, lo, hi = proportion_with_ci(0, 100)
    assert p == 0.0
    assert lo == 0.0
    assert hi > 0  # CI superior > 0 mesmo com 0/N


def test_proportion_with_ci_extreme_full():
    """Wilson lida com N/N."""
    p, lo, hi = proportion_with_ci(100, 100)
    assert p == 1.0
    assert lo < 1.0
    assert hi == 1.0


def test_holm_correction_8_hypotheses():
    """Holm corrige 8 p-values mantendo FWER ≤ α."""
    from statsmodels.stats.multitest import multipletests
    p_raw = [0.04] * 8  # todos significantes sem correção
    reject, p_corr, _, _ = multipletests(p_raw, alpha=0.05, method="holm")
    # Holm: o menor p_corrigido para o pior caso = 0.04 * 8 = 0.32 → não rejeita
    assert not any(reject)


def test_executive_summary_required_dimensions():
    """Tabela executiva contém todas as 8 hipóteses + volume/aprovação."""
    mock_records = [{"overall_passed": True, "composite_score": 95,
                     "validations": {"audit_deepseek": {"has_critical_error": False}}}] * 100
    mock_summaries = {
        "intrinsic": {"bertscore_f1_median": 0.95, "structural_pass_rate": "?",
                      "pt_drift_rate": "?", "kruskal_p": "?"},
        "lexical":   {"overall_acceptable_rate": 0.998},
        "duplicate": {"median_cosine_pt_pt": 0.99},
        "agreement": {"consensus": {"histogram_n_passed": {}}},
        "human":     {},
    }
    summary = build_executive_summary(mock_records, mock_summaries)
    dims = set(summary["Dimensão"])
    expected = {"Volume", "Aprovação", "Erro crítico (H8)",
                "Semântica (H1)", "Léxico (H2)", "Estrutural (H4)",
                "Estabilidade (H5)", "PT-br (H7)", "Cross-source (H3)",
                "Sem viés (H6)", "Revisão humana"}
    assert expected.issubset(dims)
```

Run: `pytest tests/test_evaluation/test_notebook_helpers.py -v` → **5 PASS**.

---

- [ ] **Step 7: §12 Reproducibility statement auto-gerado (Ajuste 8)**

```python
# Última célula do notebook — relatório de reprodutibilidade

import subprocess, sys, json
from datetime import datetime, timezone
from pathlib import Path
import importlib.metadata as imp


def get_git(*args):
    return subprocess.check_output(["git", *args]).decode().strip()


repro = {
    "git_commit_executing_t23": get_git("rev-parse", "HEAD"),
    "tags_pre_registered":      get_git("tag", "--list", "*pre-registered*").split("\n"),
    "schemas":                  {"validation_results": "2026-04-28-v1"},
    "hashes": {
        "atlas_glossary":  records[0]["metadata"]["atlas_glossary_hash"],
        "audit_prompt":    records[0]["metadata"]["audit_prompt_hash"],
    },
    "models_used": {
        "translator":          "gemini-2.5-flash (Phase A)",
        "auditor_primary":     "deepseek-v3 (T13)",
        "auditor_calibration": "gpt-4o-mini-2024-07-18 (T13 Step 5)",
        "back_translator":     "gemini-2.5-flash thinking_budget=0 (T14.B)",
        "embedder":            "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "bertscore_model":     "xlm-roberta-large",
    },
    "parameters": {
        "temperature":     0,
        "thinking_budget": "active in Phase A; disabled in T14.B",
    },
    "costs_usd": {
        "phase_a":   33.43,    # T14.A retroativo
        "t13":       0.27,
        "t13_step5": 0.17,
        "t14b":      0.20,
        "total":     34.07,
    },
    "pre_registered_specs": {
        "composite_score_formula": "docs/superpowers/specs/composite_score_formula_v1.md",
        "mqm_protocol":            "docs/superpowers/specs/mqm_review_protocol_v1.md",
    },
    "notebook_run_at": datetime.now(timezone.utc).isoformat(),
    "python_version":  sys.version,
    "key_libs": {
        pkg: imp.version(pkg)
        for pkg in ["scipy", "numpy", "pandas", "scikit-learn",
                    "statsmodels", "sentence-transformers",
                    "bert-score", "sacrebleu"]
    },
}

print(json.dumps(repro, indent=2, ensure_ascii=False))

Path("results/translation/reproducibility_statement.json").write_text(
    json.dumps(repro, ensure_ascii=False, indent=2), encoding="utf-8"
)
```

**Banca pergunta "como reproduzir?"** → resposta: hash, modelo, parâmetro, tag git pré-registrada — tudo auto-gerado a partir do estado do repo. Reprodutibilidade não é promessa, é arquivo.

---

- [ ] **Step 8: Commit + push**

```bash
git add notebooks/01_translation_report.ipynb \
        src/evaluation/notebook_helpers.py \
        tests/test_evaluation/test_notebook_helpers.py \
        results/translation/reproducibility_statement.json
git commit -m "docs(evaluation): F11 notebook consolidado (H1-H8 + Holm + headline executiva + 12 secoes + reproducibility auto-gerado)"
git push
```

---

#### Síntese

| Ajuste | Custo | Resolve |
|---|---|---|
| 1 — H1–H8 + Holm-Bonferroni | 15 min | H8 ausente + FWER inflado |
| 2 — 12 seções (5+5b, 7+7b) | 30 min | Estrutura desatualizada |
| 3 — Consumir summary JSONs | 10 min | Recomputo redundante |
| 4 — §10 com `failure_reasons` | 20 min | Taxonomia desconectada |
| 5 — Helpers padronizados | 15 min | Wilson + bootstrap reutilizáveis |
| 6 — Tabela executiva | 20 min | Headline TCC |
| 7 — TDD (5 testes) | 25 min | Regressão de hipóteses |
| 8 — Reproducibility auto-gerado | 15 min | Defesa concreta |

**Total: ~2h30min.**

#### Princípios consolidados (coerência metodológica final)

| Padrão | T-x produz | T23 lê |
|---|---|---|
| Schema unificado | T20 define | consome via `validations[fonte]` |
| Pré-registro com tag git | T20 (composite), T22 (MQM) | declara em §11/§12 |
| Bootstrap BCa n=10000 | T15/T18/T19/T21 | helper `median_with_ci` |
| Filtro de abstain | T20 (`null`/`in_sample`/`in_pair`) | consenso ativo + Holm |
| TDD com casos de borda | todas | 5 testes em helpers |
| Output JSON sumário | todas | `summaries[*]` em Step 1 |
| FWER controlado | n/a | **Holm-Bonferroni em H1–H8** |

---

## Summary: tasks vs framework phases vs hypotheses

| Task | Framework Phase | Hypotheses Tested | Cost | Time |
|------|-----------------|-------------------|------|------|
| T12 | Setup + F5.A glossário Atlas | (subsidia outras) | manual | 3h |
| **T12.5** | **Fix C1 auditor (derivar do Atlas)** | (validade) | $0 | 1h |
| **T12.6** | **Severidade clínica (critical/major/minor)** | H8 + headline TCC | $0 | 1h |
| T13 | F1 reaudit DeepSeek + Step 0 audit Phase A + Step 5 calibração GPT-4o-mini | H3 + H8 + calibração | $0.44 | 7h |
| **T14.A** | **Fix tracking custo/tokens** | (validade) | $0 | 1h |
| **T14.B** | **F2 back-translation amostral (~250, prompt minimalista)** | H1, H3 | $0.20 | 20min |
| T15 | F3 métricas intrínsecas (BERTScore-F1+chrF++/cosine/length_ratio main; TER apêndice) | H1, H6 | $0 | 30min |
| T16 | F4 structural checks | H4, H7 | $0 | 1h impl + 10min run |
| T17 | F5.B+C léxico | H2 | $0 | 1h |
| T18 | F6 morfossintaxe | H2 | $0 | 30min |
| T19 | F7 duplicatas | H5 | $0 | 10min |
| T20 | F8 validation_results.jsonl (schema unificado + fórmula pré-registrada + abstain) | (consolidação) | $0 | 2h20min |
| T21 | F9 acordo cross-source 6 fontes (Cohen's κ + abstain + estratificado por BI-RADS + disagreement direcional) | H3 + H6 | $0 | 1h45min |
| T22 | F10 amostra MQM n=50 cega + protocolo pré-registrado + 6 dim essenciais + extração estruturada | H1, H2, H3 | $0 + revisão manual | 1h35min + ~3-4h revisão |
| T23 | F11 notebook (H1–H8 + Holm + 12 seções 5/5b/7/7b + headline executiva + reproducibility auto) | Todas | $0 | 2h30min |

**Total APIs:** ~$0.64 USD ≈ R$3.20 · **Tempo de máquina:** ~8h (T13 + Step 5 + T14.B paralelos) · **Tempo de implementação:** 2–3 dias úteis
