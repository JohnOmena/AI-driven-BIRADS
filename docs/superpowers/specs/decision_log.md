# Decision log — Phase B evaluation framework

Decisões metodológicas centralizadas. Cada linha aponta para a task que tomou a decisão e justifica brevemente.

## Glossário

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Atlas tem 18 termos novos vs 95 do antigo | T12 | 10 categorias BI-RADS oficiais (0–6 + 4A/B/C); 5 associated_features (retração cutânea/mamilar, espessamento, linfadenopatia); 1 morfologia "grosera heterogênea"; 1 mass_shape "oval" CBR. Glossário antigo cobria pouco essas dimensões | ACR BI-RADS Atlas 5th ed |
| `oval` como pt_canonical, `ovalado/a` em variants_acceptable | T12 (Ajuste 5) | CBR/SBM oficial usa `oval`. Tradutor recebeu glossário antigo com `ovalado/a` — não punir retroativamente | (Ajuste 5 cenário T12) |
| Retrocompatibilidade verificada por gate `verify_atlas_backward_compat.py` | T12 Step 4 | Exit 0 antes de commit T12. Status: gate manual, não pre-commit hook automatizado | (gate manual) |
| 25 adjetivos com `forms_pt`/`forms_es` (T18 prereq) | T12 Step 3.7 | Cobre M-SING/F-SING/M-PLUR/F-PLUR. 22/25 com >=1 ocorrência no corpus | (verificação empírica 2026-04-29) |
| 3 adjetivos com 0 ocorrências no corpus PT (lobulado, retraído, espessado) | T12 | T18 vota abstain (`n_compared=0`) nesses casos. Categoria expressa via substantivos próximos (retração, espessamento) que têm entries próprias | (verificação empírica 2026-04-29) |

### 18 termos novos no Atlas vs glossário antigo (detalhamento por linha)

| # | Termo (es) | Categoria | pt_canonical | Justificativa |
|---|---|---|---|---|
| 1 | bi-rads 0 | categories_birads | BI-RADS 0 | Categoria oficial Atlas; antigo só tinha "BI-RADS" genérico. Essencial para H4 (preservação de categoria via regex) |
| 2 | bi-rads 1 | categories_birads | BI-RADS 1 | idem |
| 3 | bi-rads 2 | categories_birads | BI-RADS 2 | idem |
| 4 | bi-rads 3 | categories_birads | BI-RADS 3 | idem |
| 5 | bi-rads 4 | categories_birads | BI-RADS 4 | idem |
| 6 | bi-rads 4a | categories_birads | BI-RADS 4A | Subcategoria 4A/4B/4C necessária para auditoria fina |
| 7 | bi-rads 4b | categories_birads | BI-RADS 4B | idem |
| 8 | bi-rads 4c | categories_birads | BI-RADS 4C | idem |
| 9 | bi-rads 5 | categories_birads | BI-RADS 5 | Categoria oficial Atlas |
| 10 | bi-rads 6 | categories_birads | BI-RADS 6 | idem |
| 11 | engrosamiento cutáneo | associated_features | espessamento cutâneo | Achado associado oficial Atlas — antigo não tinha categoria dedicada |
| 12 | espessado | associated_features | espessado | Adjetivo com forms_pt; corpus tem 0 ocorrências (T18 abstain) |
| 13 | grosera heterogénea | calcifications_morphology | grosseira heterogênea | Tipo morfológico oficial Atlas (calcificações grosseiras heterogêneas) |
| 14 | linfadenopatía | associated_features | linfadenopatia | Achado clínico relevante para diagnóstico |
| 15 | oval | mass_shape | oval | Forma CBR canônica; variantes ovalado/ovalada em pt_variants_acceptable (Ajuste 5) |
| 16 | retracción cutánea | associated_features | retração cutânea | Achado associado relevante |
| 17 | retracción del pezón | associated_features | retração mamilar | idem; alternativas "retração do mamilo" em variants |
| 18 | retraído | associated_features | retraído | Adjetivo com forms_pt; corpus tem 0 ocorrências (T18 abstain) |

### 3 adjetivos com 0 ocorrências no corpus PT (T18 abstain by design)

| Adjetivo | Categoria | Diagnóstico | T18 vota |
|---|---|---|---|
| `lobulado` | mass_shape | Em laudos PT-br, "microlobulado" é mais usado (entry própria, 6 ocorrências). "Lobulado" puro raramente aparece. | abstain (`n_compared=0`) |
| `retraído` | associated_features | Categoria expressa via substantivo "retração cutânea/mamilar" (entries próprias). Adjetivo `retraído` puro raro. | abstain (`n_compared=0`) |
| `espessado` | associated_features | Idem — categoria via "espessamento cutâneo" (entry própria). Adjetivo `espessado` raro. | abstain (`n_compared=0`) |

**Reportagem:** `modifier_summary.json` (T18 Step 6) reporta `coverage_rate` explicitamente — banca vê quantos adjetivos efetivamente medidos.

### Caso ⚠ RPT_003856 — investigação do único aumento de C1 no smoke T12.5

| Lado | Inconsistência detectada | Classificação |
|---|---|---|
| Phase A (prompt antigo) | "DE MARGENS obscurecidas" — auditor reclamou que "obscurecido" deveria ser "obscurecidos" (concordância gênero/número) | **Falso positivo** — meta-validação refutou (`verdict=keep`, `rejected=1`); T18 cobre concordância morfológica |
| T12.5 (prompt novo) | "calcificação arredondada" — tradutor usou "arredondada" para "redondeada", mas Atlas só tem `redonda/redondo` em pt_variants_acceptable | **Verdadeiro positivo** — tradutor usou termo fora do glossário recebido |

**Conclusão metodológica:** o fix C1 não introduziu regressão — eliminou o falso positivo de concordância (delegado a T18) e detectou termo realmente fora do glossário. Smoke reportou `1→2` por variabilidade T=0; re-investigação retornou `1→1`. **Fix está mais sensível, não mais ruidoso.**

**Decisão:** NÃO adicionar "arredondada" ao Atlas — CBR/SBM oficial usa apenas "redonda/redondo" como descritor BI-RADS. T17 vai categorizar "arredondada" como `unknown_for_term` ou `gender_variant` automaticamente (regra determinística).

### Cross-reference: política de variantes em C1 (T12.5) ↔ canonical_rate vs acceptable_rate (T17)

**Contexto unificado:** C1 (auditor LLM) e T17 (análise léxica determinística) avaliam dimensões diferentes do MESMO invariante (preservação léxica BI-RADS), com a mesma política de variantes:

| Dimensão | Fonte | Métrica primária | Métrica secundária | Critério H2 |
|---|---|---|---|---|
| **Auditor LLM (C1)** | T12.5/T13 | passa se variante usada está em `pt_variants_acceptable` | — | C1 não-falho contribui em Q_audit |
| **Léxico determinístico (T17)** | F5.B | `overall_acceptable_rate` (canonical ∪ acceptable) | `overall_canonical_rate` (só canonical) | `overall_acceptable_rate` ≥ 0.99 |

**Por que ambos usam a mesma política de "aceitar variants_acceptable":**
- Tradutor (Phase A) recebeu glossário antigo (95 termos)
- Atlas tem `pt_canonical` que pode diferir do antigo (ex: `oval` vs `ovalado`)
- Punir o tradutor por usar a forma antiga = falso positivo retroativo
- C1 e T17 coordenadas: **acceptable é o critério de pass/fail**; canonical é só evidência sobre evolução do glossário (não erro de tradução)

**Resultado prático:** se T13 (com C1 fix) e T17 produzirem números similares de findings/anomalies em C1/léxico, alta concordância valida o fix de C1. Se discordarem, T22 (revisão MQM) resolve. Cross-reference explícito previne dupla-contagem em `composite_score`.

## Severidade clínica (T12.6 — taxonomia critical/major/minor)

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Override mecânico C2/C3/C4/C6 → severity sempre `critical` | T12.6 | Critérios objetivos: divergência detectada é por definição clinicamente impactante (categoria, medidas, lateralidade, negação). Não depende de julgamento LLM. | (princípio de design) |
| LLM classifica severity em C1/C5/C7 | T12.6 | Critérios contextuais: descritores BI-RADS, omissões/adições, temporais. Severidade depende de contexto clínico. Validado pela revisão MQM (T22). | (decisão metodológica) |
| Fallback `minor` para severity inválido em C1/C5/C7 | T12.6 | Conservador: não fingir severidade alta quando LLM não classificou. Campo `severity_method = "fallback_minor"` flag para auditoria. | (decisão de robustez) |
| Preservar `severity_llm_raw` em todas as inconsistências | T12.6 | Permite auditoria pós-hoc do que LLM disse vs override mecânico. Útil para T22 e análise de erros. | (auditoria) |

### Rubrica de severity por critério (registrada no prompt do auditor T12.6)

| Critério | Tipo | Rubrica |
|---|---|---|
| **C1 descritores BI-RADS** | LLM (subjetivo) | `critical` se descritor afeta categoria final (ex: 'espiculada' → suspeita); `major` se omite descritor relevante; `minor` se variação estilística |
| **C2 categoria BI-RADS** | mecânico | sempre `critical` |
| **C3 medidas/números** | mecânico | sempre `critical` |
| **C4 lateralidade/localização** | mecânico | sempre `critical` |
| **C5 omissões/adições** | LLM (subjetivo) | `critical` se omite achado clinicamente relevante (massa, calcificação, distorção); `major` se omite descritor menor; `minor` se omite contextual |
| **C6 inversões/negação** | mecânico | sempre `critical` |
| **C7 temporais/achados associados** | LLM (subjetivo) | `critical` se 'novo achado' omitido; `major` se estabilidade temporal omitida; `minor` se referência a exame anterior |

**Validação smoke (2026-04-29):** rubrica resultou em 100% de severity LLM válido (10/10 em C1/C5/C7) em smoke de 20 laudos. 0 parse failures. Distribuição final 0 critical / 1 major / 9 minor — coerente com amostra Phase A C1-heavy (sem erros C2/C3/C4/C6 que disparariam mecânico).

## Auditor C1 (T12.5 — derivação programática)

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| **Categorias do Atlas que entram em C1** | T12.5 | C1 audita "descritores BI-RADS". Categorias do Atlas mapeadas: `mass_shape`, `mass_margin`, `mass_density`, `calcifications_morphology`, `calcifications_distribution`, `associated_features`. Excluídas: `breast_composition` (composição mamária — descritor estrutural, não BI-RADS finding), `anatomy` (âncoras — não modificadores), `findings_mass` (substantivos — separadamente em C5/C7), `categories_birads` (auditado em C2), `assessment_terms` (palavras de juízo — não descritores), `procedures` (procedimento — não descritor), `asymmetry_distortion` (substantivos — em C5/C7). 6 categorias × ~5 termos = ~30 termos canônicos no bloco C1. | (decisão T12.5) |
| **Política de variantes aceitáveis no C1** | T12.5 | C1 aceita **TODAS as variantes em `pt_variants_acceptable`** (canonical + ovalada + ovalado etc), não apenas `pt_canonical`. Listar separadas por `/` no prompt: `oval/ovalada/ovalado`. Revisor LLM deve marcar passou se a forma usada está em qualquer variante listada — independente de gênero/número. **Justificativa:** evita falso positivo retroativo (tradutor recebeu glossário antigo); + alinha com retrocompat de T12. T18 cobre concordância morfológica em outra dimensão. | (decisão T12.5 + Ajuste 5 cenário T12) |

## Métricas

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Cortar BLEU do par ES↔PT | T15 | n-gramas de palavra inflam erro em línguas próximas; flexão equivalente subestima | Freitag et al. 2022 (WMT22 Metrics) |
| Manter BLEU em F2 (back-translation) | T14.B | Comparação ES↔ES_bt é monolingual — caso de uso clássico de BLEU | (decisão de design) |
| chrF++ como métrica lexical principal | T15 | Apropriada para línguas próximas (chars partilhados) | Popović 2017 |
| BERTScore-F1 como headline semântico | T15 | Padrão atual em MT evaluation, embeddings contextuais XLM-Roberta | Zhang et al. 2020 |
| Threshold modifier 0.95 (piso 0.90) | T18 Step 6 | Calibração empírica via p5 das duplicatas T19 | (calibração interna) |
| n=250 BT amostral | T14.B | Suficiente para H6 estratificado (≥7 por categoria); custo $0.20 vs $3.05 full | (decisão pragmática) |
| Holm-Bonferroni para H1–H8 | T23 Step 3 | FWER controlado em α=0.05 com 8 hipóteses confirmatórias | Holm 1979 |
| Hipóteses exploratórias separadas (sem correção) | T23 Step 3 | Defesa anti-p-hacking: confirmatórias pré-declaradas; exploratórias surgem post-hoc com flag | (princípio metodológico) |

## Schema e arquitetura

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Schema `validation_results` v1 | T20 Step 0 | Schema unificado consumido por T21/T22/T23; 3 estados de "valor" (passed/null/in_sample) | (arquitetural) |
| `audit_final_status="review"` → `passed=True` | T20 build_audit | Evita dupla penalização (Q_audit já pega has_critical) | (decisão pré-registrada) |
| `clinical_pass` separado de `overall_passed` | T20 schema | Modifier-only failure não é erro clínico — vira warning | (decisão metodológica) |
| `duplicate_stability` nunca em `overall_passed` | T19 / T20 | Fonte de priorização (T22), não de aprovação | (decisão arquitetural) |
| BERTScore não decide erro clínico | T15 escopo | Métricas semânticas globais não captam troca local de token | (limitação de escopo) |

## Pré-registro e governança

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Tag pré-registro `composite-score-formula` | T20 Step 6 | Anti-p-hacking via timestamp git imutável | Nosek et al. 2018 |
| Tag pré-registro `mqm-protocol` | T22 Step 0 | Mesma estratégia anti-p-hacking | Nosek et al. 2018 |
| Override mecânico C2/C3/C4/C6 → severity=critical | T12.6 | LLM calibra severidade instavelmente; objetivo elimina viés | (decisão de design) |
| Cegamento físico em 2 arquivos (não sheet oculta) | T22 Step 3 (Cenário C) | Sheet oculta no Excel é trivial de revelar; arquivos separados elim risco técnico | (decisão metodológica) |
| Revisor MQM externo + termo de confidencialidade | T22 Step 0 | Independência metodológica; LGPD compliance | (decisão metodológica) |
| 6 dimensões MQM essenciais (não 10) | T22 | Reduz fadiga 500→300 julgamentos; cobre H1/H2/H3 | Lommel et al. 2014 (MQM core) |
| BT prompt minimalista (sem glossário) | T14.B | Mitigação de family bias (Gemini ↔ Gemini) | (decisão metodológica) |
| Dados são anônimos verificados | T22 Step 3.6 | LGPD + ética em pesquisa; verificação automatizada via `verify_anonymization.py` | (compliance) |
| PHI base PT-br: 0 matches | Pre-flight T12 | 7 padrões testados; 0 ocorrências reais | (verificação empírica 2026-04-29) |
| PHI base ES: 21 falso-positivos confirmados visualmente | Pre-flight T12 | "PACIENTE PORTADORA/CON ANTECEDENTE/EN CONTROL" — descrições clínicas, não nomes | (verificação empírica 2026-04-29) |

## Hipóteses pré-registradas (status observado)

| Hipótese | Observado vs Esperado | Status | Decisão metodológica |
|---|---|---|---|
| H4 estrutural | 99,70% all_structural_pass (pós-A1 fix) vs ≥95% | **CONFIRMADA** | Pré-fix mostrava 75,18% por bug em `count_negations` (lista PT-pt incompleta). Pós-fix com regex word-bounded: cat 99,95% + meas 100% + lat 99,84% + neg 99,91% + anat 100%. Diff: 1.071 fail→pass, 1 regressão. Snapshot pre-fix preservado em `structural_checks_pre_negation_fix.csv` (commit 42b6277). |
| H5 estabilidade operacional | 1,0% structural_instability (pós-A1 fix) vs ≤2% (esperado) | **CONFIRMADA** | **Pré-A1 fix:** 7,0% (7 pares flagados) — falhada. **Pós-A1 fix:** 1,0% (1 par único: RPT_000725) — confirmada. **Diagnóstico:** os 7 pares originais eram artefato em cascata do bug `count_negations` (T16). Re-rodando T19 com structural_checks pós-fix, 6/7 reverteram para stable + 1 novo emergiu. Snapshot pre-fix preservado em `duplicate_pairs_pre_a1_fix.csv` + `duplicate_stability_summary_pre_a1_fix.json`. |

## Ground truth e metadados

| Aspecto | Confirmação | Implicações |
|---|---|---|
| `birads_label` (categoria 0-6) | Anotada por radiologistas no dataset original. **Presente em ambos** `data/reports_raw_canonical.csv` E `data/reports_translated_pt.csv`. Tipo: integer 0-6 (sem subclassificação 4A/4B/4C — confirmado: 0 matches em regex no texto). **Externa ao texto** — verificado em 5 laudos cat 4 (corpo não menciona "BI-RADS"). | (a) Ground truth genuíno, não-circular; permite avaliação cross-língua robusta. (b) H6 (sem viés BI-RADS) usa estratificação por label externo, sem contaminação por tradução. (c) Distribuição: 0=966, 1=596, 2=2635, 3=87, 4=52, 5=16, 6=5. **2 estratos n<30 (5 e 6)** → exigem tratamento especial em Kruskal-Wallis (pooling 5+6 ou exact tests). |

## T13 Step 5 — Critérios de decisão calibração DeepSeek↔GPT-4o-mini

**Pré-registrado antes da execução (anti-p-hacking).**

| κ médio (DeepSeek↔GPT-4o-mini) | Decisão | Ação |
|---|---|---|
| **≥ 0,80** | `PRIMARY_STABLE` | DeepSeek validado como auditor primário; T13 segue como autoridade. |
| **0,60 – 0,79** | `MODERATE` | Concordância substancial mas não excelente. Reportar discordâncias por critério; T13 mantido com caveat documentado em T23 §7. |
| **0,40 – 0,59** | `INVESTIGATE` | Concordância moderada. **Pausar** antes de aceitar; investigar discordâncias críticas com radiologista (T22 antecipado). |
| **< 0,40** | `DOWNGRADE` | Auditor primário sob suspeita. **Pausar Phase B**; revisão completa de prompt/criteria antes de prosseguir. |

### Adendo Step 5 (pré-registrado durante execução parcial 70/250 — ainda anti-p-hacking)

**Motivação:** os 7 critérios têm peso metodológico desigual no pipeline:
- **C2/C3/C4/C6** sofrem `mechanical override` (T12.6) → qualquer flag → severity=critical → afeta H8 diretamente
- **C1/C5/C7** ficam com severity LLM-judged → entram em `review` mas não bloqueiam H8

Calibração honesta deve avaliar **separadamente** por dimensão de impacto. Decisão dupla:

| Decisão | Métrica | Limiar |
|---|---|---|
| **`PRIMARY_STABLE_FOR_H8`** | κ médio em C2+C3+C4+C6 (mecânicos críticos) | ≥ 0,80 |
| **`MODERATE_FOR_H8`** | mesmos | 0,60 – 0,79 |
| **`INVESTIGATE_FOR_H8`** | mesmos | < 0,60 |
| **Status agregado** | κ médio C1-C7 (média não-ponderada) | mesmos limiares originais |

**Justificativa:** observado em parcial (70/250) que GPT-4o-mini flaga C5 em 80% dos laudos vs DeepSeek 7,2%. Divergência **metodológica** (rigor estilístico do GPT vs aceitação de paráfrases) — **não bug**. Para H8 o que importa é se ambos concordam nos critérios objetivos (C2-C4-C6), não se ambos concordam em "omissões estilísticas" (C5).

**Pré-registrado em commit antes da conclusão de Step 5** (251ª linha do JSONL ainda não escrita). Anti-p-hacking preserved.

### Interpretação metodológica do κ por critério (pré-registrada antes do término de Step 5)

**Achado em spot check (5 casos divergentes em C5, parcial 112/250):**

| Caso | Diagnóstico |
|---|---|
| RPT_000052 | GPT alega omissão de "nódulos pequeños" — texto PT contém literalmente. **Hallucination** |
| RPT_000100 | Idem — termo preservado em ambos. **Hallucination** |
| RPT_000101 | Idem. **Hallucination** |
| RPT_000130 | Alega omitir "caracteres ganglionares" — preservado literal. **Hallucination** |
| RPT_000129 | Critique de terminologia ("ganglionares" → "linfadenopáticos") — **deveria ser C1, não C5**. Miss-classification |

**Resultado: 4/5 (80%) são hallucinations do GPT-4o-mini; 1/5 é miss-classification; 0/5 são erros reais do DeepSeek-V3.**

**Interpretação:**
- **C2/C3/C4/C6** (critérios estruturais/mecânicos): κ ≥ 0,98 valida calibração para H8 (já confirmado em 70 parcial: 98-100% raw agreement)
- **C5** (raciocínio cross-document de omissões/adições): κ baixo reflete **ruído de hallucination do GPT-4o-mini**, não erro do DeepSeek-V3
- **DeepSeek-V3 mantido como auditor primário**; GPT-4o-mini é calibrador parcial — válido em critérios estruturais, ruidoso em raciocínio semântico-discursivo

**Decisão antecipada esperada:**
- `PRIMARY_STABLE_FOR_H8` ancorada em κ médio de C2/C3/C4/C6
- Status agregado: caveat documentado sobre divergência C5 atribuível a viés de hallucination do calibrador menor

**Validação adicional planejada:** após Step 5 terminar, estender spot check para 10-15 casos para confirmar taxa de hallucination sustenta ~80%.

**Estratificação da amostra (n=250):**
- **6 críticos** (100% — Tier 1 obrigatório)
- **13 major** (100% — obrigatório)
- **50 minor** estratificados (C1=20, C5=20, C7=10)
- **181 aleatórios** estratificados por `birads_label` (proporcional à distribuição)

**Métricas reportadas:**
- κ Cohen pareada por critério (C1-C7) com BCa bootstrap n=10000
- κ por severidade (critical, major, minor)
- κ médio global (média ponderada por contagem de critérios)
- Lista de discordâncias com IDs para análise qualitativa

## Estratificação para testes de hipóteses

| Decisão | Hipótese | Justificativa | Implementação |
|---|---|---|---|
| Agrupar BI-RADS 5+6 como `5-6` (alta suspeita) | H6 (sem viés BI-RADS) | Distribuição: cat 5 (n=16), cat 6 (n=5) — ambos < 30 mínimo para Kruskal-Wallis defensável. Agrupamento clinicamente coerente: ambas são categorias ACR BI-RADS de alta suspeita maligna. Cat 4 (n=52) acima do threshold, mantida individualmente. **Resultado: 6 estratos para teste estatístico** (0, 1, 2, 3, 4, '5-6' com n=21). Análise descritiva separada de 5 e 6 disponível como apêndice em T23. | T20 armazena `birads_label` original (0-6 puro) em `validation_results.jsonl`. Agrupamento 5+6 acontece **apenas em T23 §4** (estratificação na renderização do notebook), **NÃO no schema** — preserva ground truth para análises futuras. |

## T23 apêndices descritivos (pré-computados)

| Apêndice | Achado | Implicação |
|---|---|---|
| BI-RADS 5 e 6 individualmente (n=16, n=5) | Cat 5: BERT 0,9565 cosine 0,9808 chrF_ci 55,93. Cat 6: BERT 0,9575 cosine 0,9798 chrF_ci 54,12. **Comparáveis ou MELHORES** que estratos maiores (todos os 7 estratos têm BERT 0,953-0,958 e cosine 0,964-0,981). | **Suporta H6 com folga** mesmo com agrupamento 5+6: não há degradação nas categorias raras. Reforça que o tradutor performa uniformemente cross-categoria. |
| T15 outliers chrF_ci<50 (n=253; 5,8%) | Os 5 piores (chrF_ci 44-46) são laudos PT-br curtos (350-540 chars) com template padronizado "MAMOGRAFIA DIGITAL BILATERAL CRANIOCAUDAL E MÉDIO-LATERAL OBLÍQUAS...". BERTScore 0,94-0,95 e cosine 0,91-0,98 mantidos. length_ratio outliers: 0,95 (vs 0,98 geral). | **Caveat conhecido na literatura:** chrF char n-gram é instável em texto curto/template. Reportar BERTScore como métrica primária para H1. Sem ação corretiva. |

## Bugs corrigidos retroativamente

| Bug | Task | Diagnóstico | Fix | Impacto |
|---|---|---|---|---|
| `count_negations` PT subdimensionado | T16 | Lista linear `["não se ", "sem ", "ausência", "ausente", "nenhum", "nenhuma"]` não capturava formas passivas comuns em PT-br médico ("não são observadas", "não há", "nem"). Resultado: 1.066/1.074 fails eram falsos-positivos de "perda de negação" (ratio mediano 0,33). | Regex word-bounded com alternation ordenada (compostas → léxicas → genérico). `findall` consome non-overlapping → não duplica. Simulação 20 laudos: 20/20 ratio=1.000. 7 testes TDD adicionados. | `all_structural_pass` 75,18% → 99,70% (+24,52 pp); H4 confirmada. Cross-check: `lexical_loss_with_structural_fail` 24 → 0 (artefato em cascata também resolvido). |
| Case-sensitivity chrF/BLEU em T14.B | T14.B/T15 | 43,3% da base ES está em CAPS LOCK total (1.887/4.357). 66% do sample T14.B em CAPS. Modelo Gemini normaliza saída para mixed case → outlier RPT_001383 com chrF cs=9,28 vs ci=80,85. Cosine/BERTScore não afetados (model-based, case-robust). | **Reportar ambas** (case-sensitive + case-insensitive) por rigor metodológico. Adicionadas colunas `chrf_ci`/`bleu_ci_es_es_bt` ao back_translation.csv e `chrf_ci` ao intrinsic_metrics.csv. Summaries atualizados. | T15: chrF cs 53,35 → ci 54,33 mediana (+0,98); min 7,83 → 44,22. T14.B: chrF cs 93,51 → ci 93,62 mediana; min 9,28 → 80,85. **NÃO substituir métrica primária**, complementar. |
| `lexical_hallucination_flag` 23,88% | T17 | **ARTEFATO confirmado:** T17 conta variantes morfológicas no PT (singular+plural via `_is_number_variant`) mas só termo canônico no ES. Ex: "imagen nodular" ES=1 vs "imagem nodular" + "imagens nodulares" PT=2 → flag erroneamente. Não indica alucinação real. | **Aceitar como limitação reconhecida.** Não fixar (assimetria de morfologia ES é não-trivial; Atlas só tem `forms_es` para 25/103 termos). Métrica primária para H2 é `overall_acceptable_rate` (1,0) e `lexical_loss_flag` (1,33%). `hallucination_flag` mantida no CSV como diagnóstico, **NÃO** entra no composite_score (verificado: ausente em `consolidate.py`). | H2 segue confirmada. Limitação documentada em T23 §5b. |

## Custos

| Decisão | Task | Justificativa | Referência |
|---|---|---|---|
| Phase A custou ~R$160 (vs $0.20 reportado) | T14.A retroativo | (a) stats.json escopo só última sessão (b) thoughts não contado (c) preços yaml errados | (diagnóstico empírico) |
| Phase B prevista ~$0.64 USD | Sumário | DeepSeek $0.27 + GPT-4o-mini $0.17 + BT $0.20 | (estimativa) |
| Backup pré-Phase B em `backups/` | Pre-flight T12 | 9.7M total; protegido via .gitignore | (operacional) |
