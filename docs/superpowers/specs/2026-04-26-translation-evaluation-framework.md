# Framework de Avaliação da Tradução ES→PT-br
## Pipeline BI-RADS — P1-T12

**Data:** 2026-04-26
**Contexto:** TCC — replicação Lung-RADS → BI-RADS
**Autores:** John Omena (orientado)
**Tradução avaliada:** 4.357 laudos de mamografia ES → PT-br via Gemini 2.5 Flash + DeepSeek V3 (auditor)

---

## 1. Resumo executivo

Este documento define o framework metodológico para avaliar a qualidade da tradução automática de 4.357 laudos de mamografia do espanhol para o português brasileiro, com foco em:

1. **Preservação semântica** (significado clínico mantido)
2. **Preservação léxica BI-RADS** (terminologia canônica PT-br)
3. **Preservação programática estrutural** (categoria BI-RADS, medidas, lateralidade, negação)
4. **Reprodutibilidade** (tradução determinística em T=0)
5. **Adequação para tarefas downstream** (extração de informação e classificação BI-RADS)

A avaliação adota **triangulação de fontes ortogonais**: métricas automáticas + back-translation independente + auditoria LLM + revisão humana estratificada. Testa 7 hipóteses operacionais com testes estatísticos formais. Toda evidência é persistida num único arquivo `validation_results.jsonl` (fonte única de verdade por laudo).

---

## 2. Premissas metodológicas

### 2.1 Triangulação de evidências

Avaliação de tradução automática **sem corpus de referência humano gold-standard** é problema clássico em NLP. A literatura estabelecida (WMT shared tasks, Lommel et al. 2014 — MQM; Freitag et al. 2021) recomenda triangulação metodológica.

```
                     ┌─────────────────────────────┐
                     │   QUALIDADE DA TRADUÇÃO     │
                     │      (construto latente)    │
                     └──────────────┬──────────────┘
                                    │
       ┌───────────────┬────────────┼────────────┬─────────────────┐
       │               │            │            │                 │
       ▼               ▼            ▼            ▼                 ▼
 ┌──────────┐  ┌─────────────┐ ┌─────────┐ ┌──────────┐  ┌──────────────┐
 │ AUTOMATIC│  │ PROGRAMMATIC│ │ BACK-   │ │ LLM-AS-  │  │   HUMAN       │
 │ METRICS  │  │ STRUCTURAL  │ │ TRANSL. │ │ JUDGE    │  │   EVALUATION  │
 │          │  │ CHECKS      │ │         │ │          │  │               │
 │ cos/chrF │  │ categoria   │ │ PT→ES   │ │DeepSeek  │  │ MQM 50-100    │
 │ BERTScore│  │ medidas     │ │ Gemini  │ │ V3       │  │ amostra       │
 │ chrF++   │  │ lateralidade│ │ 2.5     │ │ C1-C7    │  │ estratificada │
 │ TER      │  │ negação     │ │ Flash   │ │ + meta-  │  │ por           │
 │ length   │  │ PT-pt drift │ │ thinking│ │ valid.   │  │ discordância  │
 │          │  │             │ │ off     │ │          │  │               │
 └──────────┘  └─────────────┘ └─────────┘ └──────────┘  └──────────────┘
       │               │            │            │                 │
       └───────────────┴── convergência ─────────┴─────────────────┘
                                    │
                                    ▼
            Construto validado quando ≥3 fontes convergem em
            veredito (validade convergente — Campbell & Fiske 1959)
```

**Cinco fontes ortogonais** — cada uma usa um mecanismo de evidência diferente:

| Fonte | Mecanismo | Independência |
|-------|-----------|---------------|
| Métricas automáticas | embeddings + n-gramas | independente de LLMs |
| Checks programáticos | regex determinístico | 100% reproduzível, sem ML |
| Back-translation | round-trip semântico (PT→ES) | direção inversa + thinking off + temperature=0 + prompt distinto (mitiga overlap de família com tradutor original) |
| LLM-as-judge | DeepSeek auditor + meta-validador | terceira família LLM |
| Humano | radiologista/orientado MQM | não-LLM |

**Vantagem científica:** quando 4 ou 5 fontes convergem em "tradução boa para o laudo X", a evidência sobrevive a qualquer crítica de viés de método único.

### 2.2 Princípios de rigor

1. **Pré-registro de métricas:** todas as métricas planejadas neste documento serão reportadas, não apenas as favoráveis (proteção contra cherry-picking).
2. **Determinismo:** todos os modelos LLM operam em `temperature=0`. Sementes registradas.
3. **Reprodutibilidade total:** todo artefato (JSONL/CSV) versionado em git; prompts, modelos e versões registrados em metadata.
4. **Audit trail:** cada chamada de API registra timestamp UTC, modelo, tokens, custo.
5. **Estatística inferencial:** nunca relatamos só média; sempre com intervalos de confiança bootstrap (n=10.000) e/ou testes de hipótese formais.
6. **Persistência integral:** `validation_results.jsonl` consolida TODOS os checks por laudo numa única estrutura — fonte de verdade única para o notebook.

### 2.3 Confirmação: tradução em PT-br

Verificado nos artefatos:
- `src/translation/prompt.py:16, 45, 103` — prompt explicita "português do Brasil" três vezes
- `configs/birads_glossary_es_pt.json` — usa ortografia PT-br (`arquitetural`, `ducto`, `mamilo`)

---

## 3. Hipóteses operacionais

| ID | Hipótese | Operacionalização | Critério de aceitação |
|----|----------|-------------------|------------------------|
| **H1** | A tradução preserva significado clínico | similarity (mpnet), BERTScore-F1, **chrF++** (ES↔PT) + **BLEU(ES,ES_bt)** apenas no F2 monolingual | mediana BERTScore-F1 ≥ 0.90; cosine ES↔PT ≥ 0.90; cos(ES,ES_bt) ≥ 0.85 |
| **H2** | A tradução preserva léxico BI-RADS **conforme glossário recebido** (variante + flexão) | (a) `overall_acceptable_rate` (F5.B — qual variante; canonical ∪ acceptable) **E** (b) `preservation_rate` (F6 — qual flexão; mapa morfológico do Atlas) | `overall_acceptable_rate` ≥ 0.99 **E** `preservation_rate` ≥ 0.95 agregado. `overall_canonical_rate` em paralelo como evidência sobre evolução do glossário. |
| **H3** | Fontes ortogonais de evidência convergem | concordância automática + BT (amostral) + LLM + humano | **Amostra BT (~250):** ≥ 4 das 5 fontes "approved" em ≥ 95% dos laudos. **Fora da amostra:** ≥ 3 das 4 fontes em ≥ 95% |
| **H4** | A tradução preserva categoria BI-RADS, medidas e lateralidade | checks programáticos F4 | ≥ 99% laudos passam categoria; ≥ 99% medidas; ≥ 99% lateralidade |
| **H5** | Estabilidade operacional em duplicatas `effective_duplicate` (geradas por crash/restart, mesmo `prompt_hash`) | métricas em 3 níveis (textual/semântico/estrutural) | (a) mediana `cosine_pt_pt` ≥ 0.98 (IC 95% bootstrap BCa); (b) p5 `cosine_pt_pt` ≥ 0.95; (c) `structural_instability_rate` ≤ 0.02. Pares com `requires_mqm_review = True` (divergência estrutural) automaticamente flagados para T22. **Caveat:** análise observacional de produção, não experimento controlado. |
| **H6** | Não há viés sistemático por categoria BI-RADS | qualidade estratificada por `birads_label` | Kruskal-Wallis p > 0.05 sobre BERTScore-F1 |
| **H7** | A tradução é PT-br puro (sem drift PT-pt) | regex de cognatos diagnósticos | ≤ 1% laudos com marcador PT-pt |
| **H8** | **Taxa de erro crítico clinicamente impactante é mínima** | severidade `critical` por inconsistência (T12.6 — override mecânico em C2/C3/C4/C6, LLM em C1/C5/C7) | ≤ 1% laudos com ≥1 inconsistência `critical` |

Cada fase do pipeline existe para alimentar pelo menos uma destas hipóteses.

---

## 4. Pipeline em 11 fases

### Visão geral

| Fase | Saída | Custo | Tempo | Hipóteses |
|------|-------|-------|-------|-----------|
| **F1** Reaudit DeepSeek (3.840 faltantes) + Step 0 (audit Phase A correções) + Step 5 (calibração GPT-4o-mini sobre subset ~250) | `audit_deepseek.jsonl` + `audit_gpt4omini_subset.jsonl` + `audit_calibration_agreement.json` + `c1_correction_audit.json` | ~$0.44 | ~7h | H3 + calibração |
| **F2** Back-translation amostral (~250 laudos, Gemini 2.5 Flash thinking OFF, prompt minimalista) | `back_translation.csv` + `bt_sample_ids.json` + `bt_thresholds_empirical.json` | ~$0.20 | ~20min | H1, H3 |
| **F3** Métricas intrínsecas MT (BERTScore-F1 + chrF++ + cosine + length_ratio principais; TER apêndice) — BLEU **excluído** por não ser defensável em ES↔PT | `intrinsic_metrics.csv` | $0 | ~30min | H1, H6 |
| **F4** Checks programáticos estruturais | `structural_checks.csv` | $0 | ~10min | H4, H7 |
| **F5.A** Construção glossário Atlas CBR/SBM | `birads_glossary_atlas_es_pt.json` | manual | ~3h | (subsidia F5.B/C) |
| **F5.B** Consistência léxica global | `lexical_consistency.csv` | $0 | ~30min | H2 |
| **F5.C** Anomalias léxicas | `lexical_anomalies.csv` | $0 | ~30min | H2 |
| **F6** Concordância morfossintática | `modifier_preservation.csv` | $0 | ~30min | H2 |
| **F7** Estabilidade duplicatas | `duplicate_stability.csv` | $0 | ~10min | H5 |
| **F8** Persistência consolidada de validação | `validation_results.jsonl` | $0 | ~15min | Todas |
| **F9** Concordância entre fontes (cross-source) | `agreement_report.json` | $0 | ~15min | H3 |
| **F10** Amostra MQM (50–100, discordância multifonte) | `human_review_sample.xlsx` | manual | ~10min + revisão | H1, H2, H3 |
| **F11** Notebook consolidado + análise de erros | `01_translation_report.ipynb` | $0 | ~3h | Todas |

**Custo total estimado:** ~$0.64 USD em APIs (R$ ~3.20). Quebra: DeepSeek reaudit $0.27 + GPT-4o-mini calibration $0.17 + BT amostral $0.20.
**Tempo total de máquina:** ~10h (F1+F2 paralelos).
**Tempo de implementação:** 2–3 dias úteis.

---

### F1 — Reauditoria DeepSeek (3.840 laudos faltantes)

**Pré-requisito (T12.5):** o prompt de auditoria foi corrigido para derivar a lista C1 programaticamente do glossário Atlas (com `pt_variants_acceptable`). **Smoke test confirmado em 2026-04-29 com 78.6% de redução** em FP C1 (28→6 em 20 laudos da Phase A) — acima do threshold ≥70%. Sem este fix, T13 reproduziria os falsos positivos C1 em escala (4.357 laudos).

**Objetivo:** reproduzir auditoria completa C1–C7 + meta-validação para os laudos que perderam o detalhe granular nos restarts.

**Input:**
- `results/translation/translations.csv` (texto PT final)
- `data/reports_raw_canonical.csv` (texto ES original)
- `configs/birads_glossary_es_pt.json`

**Algoritmo por laudo:**
1. Pega par (ES, PT) do CSV
2. Monta prompt de auditoria (mesmo template de `src/translation/translate.py`: `audit_translation` + `validate_findings`)
3. Chama DeepSeek V3 → JSON com `score_global`, score por critério C1–C7, lista de inconsistências
4. Chama meta-validador → cada inconsistência recebe `verdict: correct|keep`
5. Classifica status: `approved` / `review` / `rejected`
6. Escreve linha JSONL + `flush` + `os.fsync`

**Output: `results/translation/audit_deepseek.jsonl`** (uma linha por laudo):
```json
{
  "report_id": "RPT_000001",
  "audit": {
    "score_global": 9,
    "C1": {"score": 8, "passou": false, "notas": "..."},
    "C2": {"score": 10, "passou": true},
    "...": "..."
  },
  "inconsistencias": [
    {"criterio":"C1","original":"...","traducao":"...","problema":"..."}
  ],
  "audit_validation": {"verdict":"keep", "confirmed":0, "rejected":1},
  "terms_check": {"total_es":12, "matched":12, "ratio":1.0},
  "similarity": 0.9612,
  "status": "approved",
  "audited_at":"2026-04-27T14:22:31Z",
  "auditor":"deepseek-v3",
  "prompt_hash":"sha256:..."
}
```

**Restart-safety:**
- Lê JSONL existente, coleta `report_id`s válidos (descarta última linha se corrompida)
- `pending = laudos_csv − ids_ja_auditados`
- Append mode (`"a"`) com `flush + os.fsync` por linha
- Sobrevive `kill -9` e reboot

**Sem re-tradução, sem postprocessing, sem correção** — apenas audit + meta-val sobre o texto final do CSV.

---

### F2 — Back-translation PT→ES via Gemini 2.5 Flash (thinking OFF)

**Objetivo:** validação de round-trip semântico. Tradução PT→ES com modelo configurado em `thinking_budget=0` + `temperature=0` + prompt distinto, comparando ES_back com ES original.

**Justificativa metodológica:** back-translation é evidência **não-LLM-as-judge**. O modelo não está julgando — está traduzindo. Se PT preservou o significado, o round-trip recupera ES com alta similaridade. Se PT perdeu/distorceu informação, ES_bt diverge mensurável.

**Sobre o overlap de família com tradutor original:** o tradutor original foi Gemini 2.5 Flash. Usar o mesmo modelo para BT introduz risco de **family bias** (mesmo blind spot ida-volta). Mitigações adotadas:

1. **Direção inversa** (PT→ES): tarefa diferente da original (ES→PT)
2. **Thinking OFF** (`thinking_budget=0`): força raciocínio determinístico, evita "compensações criativas" e elimina o gargalo de custo identificado nos R$160 da tradução original
3. **Temperature=0**: zero estocástico
4. **Prompt minimalista** (sem glossário): força tradução direta, sem viés do glossário
5. **Cross-check com structural F4**: regex programático não falha por paráfrase — captura casos onde Gemini "harmoniza" silenciosamente

**Input:**
- `results/translation/translations.csv` (texto PT)
- `data/reports_raw_canonical.csv` (texto ES original para comparação)

**Algoritmo por laudo:**
1. Pega texto PT
2. Prompt minimalista: "Traduza o seguinte laudo de mamografia do português para o espanhol fielmente, preservando terminologia médica BI-RADS"
3. Chama Gemini 2.5 Flash com `thinking_budget=0`, `temperature=0` → texto ES_bt
4. Calcula sobre (ES_orig, ES_bt):
   - **Cosine similarity** (mpnet multilingual)
   - **BLEU** (sacrebleu, com ES_orig como referência única)
   - **chrF++** (sacrebleu)
   - **BERTScore-F1** (xlm-roberta-large)
   - **TER** (sacrebleu)
5. Escreve linha CSV + flush
6. Registra `total_token_count` da resposta (não apenas `candidates_token_count`) para custo correto

**Output: `results/translation/back_translation.csv`:**
```
report_id, es_back_translated, cos_es_es_bt, bleu_es_es_bt,
chrf_es_es_bt, bertscore_f1_es_es_bt, ter_es_es_bt,
tokens_input, tokens_output, cost_usd, translated_at
```

**Restart-safety:** lê CSV existente, continua de onde parou. Append mode com flush.

**Critério de qualidade (H1):**
- `cos(ES, ES_bt) ≥ 0.85` → ✓ semântica preservada
- `BLEU ≥ 30` → ✓ lexical razoável (BLEU ES↔ES tende a ser alto)
- `chrF ≥ 50` → ✓ caractere n-gramas robustos

Laudos com cos < 0.85 vão para o pool de candidatos da F10 (revisão humana).

**Custo estimado** (Gemini 2.5 Flash com thinking OFF, preços corretos $0.30 input / $2.50 output, amostra ~250 laudos):
- Input: 250 × ~250 tokens = 62.5K × $0.30/1M = **$0.02**
- Output: 250 × ~250 tokens = 62.5K × $2.50/1M = **$0.16**
- **Total: ~$0.20 USD ≈ R$1**

(Custo de full-corpus 4.357 laudos seria ~$3.05; amostral reduz 15x sem perder cobertura para H1/H3 graças à estratificação.)

**Cálculo legado (full-corpus, descartado):**
- Input: 4.357 × ~250 = 1.09M × $0.30/1M = **$0.33**
- Output: 4.357 × ~250 = 1.09M × $2.50/1M = **$2.72**
- **Total: ~$3.05 USD ≈ R$15**

**Pré-requisito de implementação:** corrigir `configs/models.yaml` (preços) e `src/translation/client.py` (tracking de `total_token_count`) ANTES de rodar — isso evita repetir o problema dos R$160 da tradução original.

---

### F3 — Métricas intrínsecas de tradução automática

**Objetivo:** aplicar métricas defensáveis sobre o par (ES, PT). Critério de seleção: cada métrica deve ter **interpretação direta** e **literatura recente que a avalize para línguas próximas**.

#### Métricas principais (seção 4.2 do TCC)

| Métrica | Biblioteca | Fórmula | Por que é principal |
|---|---|---|---|
| **BERTScore-F1** | `bert_score` com `xlm-roberta-large` | match de embeddings contextuais | Padrão atual em MT evaluation (Zhang et al. 2020). Headline metric para H1. |
| **chrF++** | `sacrebleu` | F-score char n-grams + word 2-grams | **Apropriada para ES↔PT** (línguas românicas próximas): captura similaridade morfológica que n-gramas de palavra inteira perdem. |
| **Cosine similarity** | sentence-transformers (`paraphrase-multilingual-mpnet-base-v2`) | `cos(emb_es, emb_pt)` | Semântica via embedding multilíngue independente do XLM-Roberta (modelo distinto, evita auto-correlação). Já validada em Phase A (avg 0.9571). |
| **Length ratio** | custom | `len(pt_tokens) / len(es_tokens)` | Sanity check determinístico de omissão/expansão. Razão extrema (≪1) sinaliza tradução truncada. |

#### Métrica complementar (apêndice)

| Métrica | Biblioteca | Por que apêndice |
|---|---|---|
| **TER** | `sacrebleu` | Edit distance normalizada. Útil só se BERTScore/chrF concordarem mas TER divergir — não é evidência primária. |

#### Métrica EXCLUÍDA — justificativa registrada

| Métrica | Razão da exclusão |
|---|---|
| ~~**BLEU**~~ (ES↔PT) | **Não defensável para o par.** Línguas próximas + flexão equivalente (`espiculada`/`espiculado`/`espiculadas`) recebem overlap zero em n-gramas de palavras inteiras mesmo preservando significado. Literatura recente (Freitag et al. 2022 — WMT22 metrics) recomenda chrF++ e BERTScore sobre BLEU. **Antecipamos a crítica da banca retirando.** BLEU permanece **apenas em F2** (ES_orig vs ES_bt, monolingual, onde é apropriado). |
| ~~Type-token ratio PT~~ | Análise sobre o **único texto traduzido** — não compara com a fonte. Não é métrica de qualidade de tradução. Move para análise descritiva no notebook §5. |

**Output: `results/translation/intrinsic_metrics.csv`:**
```
report_id,
cosine_sim, bertscore_p, bertscore_r, bertscore_f1, chrf, length_ratio,   # main
ter                                                                       # apêndice
```

**Sem coluna `bleu`.** Comentário no header do script documenta a decisão metodológica.

**Restart-safety:** lê CSV existente, continua. Flush via `pandas.to_csv(mode='a')` por batch de 50.

**Sanity checks pós-execução:**
- `bertscore_f1` mediana ≥ 0.90 (H1)
- `chrf` mediana ≥ 60 (esperado para tradução fiel ES↔PT)
- `cosine_sim` mediana ≥ 0.95 (Phase A: 0.9571)
- `length_ratio` mediana ∈ [0.92, 1.05] (Phase A: 0.975)
- `ter` mediana ≤ 0.30 (apêndice)

**Análise no notebook:**
- Histogramas das 4 métricas principais
- Correlações cruzadas (métricas independentes concordam?)
- Subanálise por `birads_label` (H6)
- Outliers (bottom 1% de cada métrica)
- TER em apêndice — só se houver divergência relevante com as principais

#### Limitação intencional de escopo (registrada)

F3 mede **similaridade textual e semântica genérica** — não decide erro clínico. Métricas MT podem classificar como "alta similaridade" um laudo que trocou categoria BI-RADS, lateralidade, medida ou negação (substituição local de token clinicamente crítico não move BERTScore/cosine globais).

| Decisão clínica per-laudo | Fonte responsável |
|---|---|
| Categoria BI-RADS, medidas, lateralidade, negação | F4 (regex determinístico) |
| Léxico canônico/aceitável | F5 (Atlas) |
| Preservação morfológica | F6 |
| Erro crítico clínico (H8) | F1 com severidade T12.6 (override mecânico C2/C3/C4/C6) |

F3 contribui no `composite_score` via `Q_semantic` (peso 0.20). Erros clínicos zeram `Q_audit` (peso 0.20), dominando o score independente de Q_semantic. **Defesa anti-banca:** "BERTScore é triagem agregada, não decisor clínico — erros clínicos são detectados por regras determinísticas e auditor com severidade."

---

### F4 — Checks programáticos estruturais (eixo central)

**Objetivo:** validações determinísticas regex-based sobre elementos clinicamente críticos. **Esta fase é central na evidência** — substitui o 2º LLM auditor com checks 100% reproduzíveis e auditáveis.

#### F4.1 Preservação de categoria BI-RADS

**Algoritmo:**
- Regex ES: `BI[\s\-]?RADS\s*[:\.]?\s*(?:categor[íi]a)?\s*([0-6])`
- Regex PT: `BI[\s\-]?RADS\s*[:\.]?\s*(?:categoria)?\s*([0-6])`
- Cross-validation com `birads_label` do `reports_raw_canonical.csv`

**Validações:**
1. `category_es == category_pt` (preservação)
2. `category_pt == birads_label` (consistência com fonte oficial)

**Critério de pass:** ambas TRUE. Se discrepância, classificar:
- `category_missing_pt`: regex não achou no PT
- `category_mismatch`: PT diz categoria diferente do ES
- `label_mismatch`: PT diz categoria diferente do label fonte

#### F4.2 Preservação de medidas

**Algoritmo:**
- Regex normalizada: `(\d+(?:[.,]\d+)?)\s*(mm|cm|m²|%|ml)\b`
- Extrai conjunto `{(value, unit)}` de ES e PT
- **Match exato:** todo elemento do set ES deve aparecer no set PT (mantida a unidade)

**Validações:**
- `measures_count_match`: |set_ES| == |set_PT|
- `measures_full_match`: set_ES == set_PT (após normalização vírgula↔ponto)
- Lista de medidas faltantes / extras

**Critério de pass:** `measures_full_match == True`.

#### F4.3 Preservação de lateralidade

**Algoritmo:**
- Map ES→PT: `{izquierdo:esquerdo, izquierda:esquerda, izquierdos:esquerdos, izquierdas:esquerdas, derecho:direito, derecha:direita, derechos:direitos, derechas:direitas, bilateral:bilateral}`
- Para cada termo de lateralidade no ES, verifica equivalente no PT (com tolerância a posição relativa)

**Validações:**
- `laterality_count_match`: igual número de menções
- `laterality_no_inversion`: nenhum esquerdo↔direito trocado

**Critério de pass:** ambas TRUE.

#### F4.4 Preservação de negação

**Algoritmo:**
- Marcadores ES: `[no se, sin, ausencia de, ausente, no, ningún, ninguna]`
- Marcadores PT: `[não se, sem, ausência de, ausente, não, nenhum, nenhuma]`
- Conta ocorrências em cada texto
- Estrutural: regex `(não|sem)\s+\w+\s+\w+` precedendo substantivo BI-RADS

**Validações:**
- `negation_count_ratio`: |neg_PT| / |neg_ES| ∈ [0.8, 1.2]
- `negation_structural`: estrutura sintática preservada

**Critério de pass:** ambas TRUE.

#### F4.5 Preservação de menções anatômicas

Lista anatômica essencial: `[mama, cuadrante, pezón/mamilo, areola/aréola, axila, linfonodo/ganglio, tejido/tecido]`.

**Validação:** cada menção em ES tem equivalente PT.

#### F4.6 Drift PT-pt (H7)

Cognatos diagnósticos (~25):

| PT-pt (rejeitar) | PT-br (aceitar) |
|---|---|
| arquitectónica | arquitetural |
| facto | fato |
| objecto | objeto |
| acção | ação |
| direcção | direção |
| infecção | infecção (igual) |
| utente | paciente |
| ecrã | tela |
| (... ~25 pares) | |

**Validação:** match `\b<termo>\b`. Se ≥1 marcador PT-pt → `pt_drift = True`.

#### Saída consolidada

**Output: `results/translation/structural_checks.csv`:**
```
report_id,
category_es, category_pt, category_label, category_pass,
measures_es_json, measures_pt_json, measures_pass, measures_missing_json,
laterality_es_json, laterality_pt_json, laterality_pass,
negation_es_count, negation_pt_count, negation_ratio, negation_pass,
anatomy_pass,
pt_drift, pt_drift_terms_json,
all_structural_pass
```

`all_structural_pass = category_pass AND measures_pass AND laterality_pass AND negation_pass AND anatomy_pass AND NOT pt_drift`.

**Restart-safety:** processamento rápido (~10 min total). Lê CSV existente, append.

---

### F5 — Léxico BI-RADS: glossário, consistência e anomalias

#### F5.A — Construção do glossário Atlas CBR/SBM (preparatório)

**Input:**
- BI-RADS Atlas 5ª ed (ACR, 2013) — referência inglesa
- Adaptação CBR (Colégio Brasileiro de Radiologia) e SBM — fonte autoritativa PT-br
- **`configs/birads_glossary_es_pt.json` (95 termos originais)** — referência de retrocompatibilidade

**Processo:**
1. Extrair categorias do Atlas: morfologia de massas, margens, densidade, calcificações (forma + distribuição), distorção, assimetrias, achados associados
2. Mapear ES (vocabulário hispanofalante de mamografia) ↔ PT-br canônico (CBR/SBM)
3. Cotejar com glossário original (95 termos) → identificar gaps
4. **Aplicar restrição de retrocompatibilidade** (ver abaixo)
5. Estruturar com BI-RADS codes

#### ⚠ Restrição de retrocompatibilidade (crítica para validade)

O glossário Atlas (~200 termos) é mais rico que o glossário original (~95) usado durante a tradução em T11. **Se o auditor cobrar termos do Atlas que o tradutor nunca recebeu**, a Phase B gera **falso positivo retroativo** — punindo o tradutor por algo que não foi instruído a fazer.

**Regra invariante:** toda escolha PT presente no glossário original DEVE estar listada em `pt_variants_acceptable` da entrada Atlas correspondente, mesmo quando não for o `pt_canonical`.

**Exemplo concreto:**
- Glossário original: `{"es": "ovalada", "pt": "ovalada"}`, `{"es": "ovalado", "pt": "ovalado"}`
- Atlas oficial CBR/SBM: descritor canônico de forma de massa é `oval`
- Entrada Atlas resultante:
```json
{
  "es": "oval",
  "pt_canonical": "oval",
  "pt_variants_acceptable": ["oval", "ovalada", "ovalado"],
  "bi_rads_code": "MASS_SHAPE_OVAL"
}
```

Consequências práticas:
- ✅ Reauditoria (F1) e auditoria léxica não punem `ovalado/a` (forma que o tradutor recebeu)
- ✅ F5.B reporta `canonical_ratio < 1.0` para esse termo, mas categoriza variantes como `acceptable` em vez de `wrong_term`
- ✅ TCC argumenta cleanly: "tradutor seguiu fielmente o glossário recebido; Atlas oferece referência canônica para futuro pipeline"

**Estrutura final da entrada:**

```json
{
  "es": "<termo origem espanhol>",
  "pt_canonical": "<forma canônica CBR/SBM PT-br>",
  "pt_variants_acceptable": ["<canônica>", "<variantes do glossário antigo>", ...],
  "pt_variants_unacceptable": ["<typos comuns, formas erradas>", ...],
  "bi_rads_code": "<código atlas>"
}
```

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
       "bi_rads_code": "MASS_SHAPE_OVAL"}
    ],
    "mass_margin": [...],
    "calcifications_morphology": [...],
    "calcifications_distribution": [...],
    "associated_features": [...]
  }
}
```

**Verificação automática (gate antes do commit T12):** script `verify_atlas_backward_compat.py` confere que 100% dos termos PT do glossário original aparecem em `pt_variants_acceptable` do Atlas. Se faltar algum, falha o build.

**Princípio de separação de responsabilidades (Ajuste 5):** decisões lexicais (ex: `oval` vs `ovalado` da CBR/SBM) se resolvem **no glossário (F5.A)**, não no prompt do auditor. F5.A inclui ambas em `pt_variants_acceptable` quando ambas aparecem na base traduzida. T12.5 (fix do prompt C1) é puramente mecânico — apenas deriva do JSON.

**Coleta evidence-based de variantes (Step 3.5 de T12):** antes de finalizar o glossário Atlas, escanear `data/reports_translated_pt.csv` para identificar todas as variantes PT que de fato apareceram na base. Toda variante observada → entra em `pt_variants_acceptable`. Garante que nenhuma forma já em produção é punida na avaliação.

**Entregável TCC:** o próprio glossário é artefato acadêmico citável (Atlas + CBR + SBM) com cláusula de retrocompatibilidade + lista de variantes empíricas documentadas.

#### F5.B — Consistência terminológica global (contagem global, sem alinhamento)

**Princípio metodológico:** **contagem global por laudo, não alinhamento posicional.** Para cada termo ES do glossário Atlas, conta-se ocorrências no texto ES e ocorrências de cada variante PT (canonical + acceptable + unacceptable) no texto PT, com tolerância ±10%. Não tentamos parear ocorrências i-ES com i-PT — cross-lingual position alignment é ruidoso e introduz mais erro do que captura.

**Limitação reconhecida:** quando um termo aparece múltiplas vezes no laudo, F5.B não distingue qual ocorrência específica foi traduzida com qual variante. Mitigado por (a) cross-flag com F4 (structural checks) e (b) revisão MQM (F10).

**Categorização léxica determinística:**

| Categoria | Regra |
|---|---|
| `canonical` | variante == `pt_canonical` |
| `acceptable` | ∈ `pt_variants_acceptable` (não canonical) |
| `gender_variant` | difere do canonical apenas em sufixo `-o`/`-a` |
| `number_variant` | difere apenas em `-s`/`-es` final |
| `unacceptable` | ∈ `pt_variants_unacceptable` |
| `unknown_for_term` | não está em nenhuma das listas |

Cada categoria = função pequena, testável (TDD).

**Métricas reportadas — duas escalas:**

*Por termo (distribuição):*
- `term_canonical_ratio = canonical_count / pt_total_count`
- `term_acceptable_ratio = (canonical + acceptable) / pt_total_count`

*Globais na base (magnitude — usado pra H2):*
- `overall_canonical_rate = sum(canonical) / sum(pt_total)`
- `overall_acceptable_rate = sum(canonical + acceptable) / sum(pt_total)` ← **H2 metric**

**`overall_acceptable_rate` é a métrica defensável** — mede fidelidade ao glossário recebido (95 termos), não ao Atlas canônico. `canonical_rate` baixo penalizaria injustamente o tradutor por escolhas de glossário tomadas em T12 (decisão institucional, não erro). Ambos são reportados em paralelo.

**Cross-flag com F4 (Ajuste #4):**
- `lexical_loss_with_structural_pass`: perda léxica isolada (estilística)
- `lexical_loss_with_structural_fail`: perda léxica + estrutura quebrada → **prioridade MQM (F10)**

**Output: `results/translation/lexical_consistency.csv`** — uma linha por (laudo × termo):
```
report_id, es_term, bi_rads_code,
es_count, pt_total_count, ratio_pt_es,
canonical, acceptable, gender_variant, number_variant, unacceptable, unknown_for_term,
term_canonical_ratio, term_acceptable_ratio,
lexical_loss_flag, lexical_hallucination_flag,
lexical_loss_with_structural_pass, lexical_loss_with_structural_fail
```

**Output adicional: `results/translation/lexical_global_summary.json`:**
```json
{
  "overall_canonical_rate": 0.85,
  "overall_acceptable_rate": 0.998,
  "total_es_occurrences": 52431,
  "total_pt_occurrences": 52107,
  "n_terms_analyzed": 198,
  "n_laudos_with_loss_isolated": 142,
  "n_laudos_with_loss_critical": 18
}
```

#### F5.C — Anomalias léxicas

**Output: `results/translation/lexical_anomalies.csv`** — uma linha por anomalia (categoria ∉ {canonical, acceptable}):
```
report_id, es_term, pt_variant_observed, category,
context_pt (±5 tokens), severity_inferred
```

`severity_inferred` segue regra T12.6: `critical` se o termo pertence a categorias mecânicas (medidas, lateralidade, categoria BI-RADS, negação); `minor` caso contrário.

Ordenação: `severity DESC, term_frequency DESC`.

**Restart-safety:** processamento em memória (~5 min total). Salva ao final. Se falhar, reroda.

---

### F6 — Preservação morfossintática (divergências introduzidas pela tradução)

**Pergunta respondida:** a forma flexionada do adjetivo BI-RADS foi **preservada** na tradução ES→PT? (não: a concordância está correta no PT — isso é F10/MQM.)

**Por que essa formulação:** se ES diz "lesión espiculada" (F-SING) e PT diz "lesão espiculado" (M-SING), introduziu-se divergência. Erros morfossintáticos pré-existentes no laudo ES (typos do laudista) NÃO são contabilizados — só medimos divergências **introduzidas pela tradução**. Isso evita confundir erro de fonte com erro de tradução.

**Escopo:** apenas adjetivos BI-RADS canônicos com mapa morfológico explícito no Atlas (~30 entradas em `forms_pt`/`forms_es`). Substantivos âncora (`mama`, `lesão`, `nódulo`) não recebem `forms_*` — sustentam concordância, não a expressam.

**Schema do Atlas (campos novos requeridos por F6):**
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

**Algoritmo:**

```python
def detect_form(text, forms_dict):
    # Plurais antes de singulares (evita match parcial: "espiculadas" ⊃ "espiculada")
    for tag in ["M-PLUR", "F-PLUR", "M-SING", "F-SING"]:
        if regex_word_boundary(forms_dict[tag], text):
            return tag
    return None

def diff(es_text, pt_text, atlas):
    for entry com forms_pt e forms_es:
        es_form = detect_form(es_text, entry["forms_es"])
        pt_form = detect_form(pt_text, entry["forms_pt"])
        if es_form and pt_form and es_form != pt_form:
            registrar divergence (gender / number / both)
```

**Métricas:**
- `n_modifiers_compared` — adjetivos presentes em ES E PT
- `n_divergences` — divergências introduzidas
- `preservation_rate = (n_compared - n_divergences) / n_compared` — **alvo H2(b) ≥ 0.95**

**Output: `results/translation/modifier_preservation.csv`:**
```
report_id, n_modifiers_compared, n_divergences,
divergence_rate, preservation_rate,
gender_divergence_count, number_divergence_count, both_divergence_count,
divergences_json
```

**Pré-requisito:** Atlas com `forms_pt`/`forms_es` em ~30 adjetivos validados pelo gate `verify_atlas_morphology.py` (F5.A).

**Restart-safety:** processamento determinístico, salva de uma vez.

---

### F7 — Estabilidade operacional via duplicatas (H5)

**Reposicionamento metodológico:** as duplicatas foram geradas por **crash/restart na Phase A**, não por experimento controlado. F7 mede estabilidade operacional sob produção e calibra empiricamente os pisos de variação tolerada em F2 (BT) e F6 (modifier preservation). Não é experimento formal de reprodutibilidade — é análise observacional com caveat de pareamento operacional.

**Filtragem em 4 camadas:**

| Camada | Critério | Uso |
|---|---|---|
| `duplicate_candidate` | `report_id` com >1 linha em `translations.csv` | base inicial |
| `valid_duplicate` | candidate AND ambas PT não-vazias | filtro de integridade |
| `effective_duplicate` | valid AND mesmo `prompt_hash` | **fonte primária H5 + calibração** |
| `strict_reproducibility_pair` | effective AND mesma sessão | sub-análise opcional (n ≥ 30) |

Pares fora de `effective` são **excluídos** (motivo registrado em `summary.json`: `empty_translation` ou `different_prompt_hash`).

**Métricas em 3 níveis (Levenshtein cortado por sobreposição com chrF++):**

| Nível | Métricas |
|---|---|
| **Textual** | `exact_match_normalized`, `chrf_pt_pt` |
| **Semântico** | `cosine_pt_pt` (mpnet), `bertscore_f1_pt_pt` (xlm-roberta-large) |
| **Estrutural** | `category_match`, `measures_match`, `laterality_match`, `negation_match` (reusa F4 extractors) |

**Flag de instabilidade estrutural:**
```python
duplicate_structural_instability = not all([category, measures, laterality, negation match])
requires_mqm_review = duplicate_structural_instability  # alimenta F10
```

**Output:** `duplicate_pairs.csv` (classificação 4 camadas) + `duplicate_stability.csv` (métricas 3 níveis para `effective`) + `duplicate_stability_summary.json` (agregados + componentes H5).

**Schema em `validation_results.jsonl` (abstain semântico — Ajuste 8):**
```json
// Singleton
"duplicate_stability": {"in_pair": false}

// Effective duplicate
"duplicate_stability": {
  "in_pair": true,
  "pair_type": "effective_duplicate",
  "cosine_pt_pt": 0.991,
  "structural_instability": false,
  "requires_review": false
}
```

**`duplicate_stability` NÃO entra em `overall_passed`** — é fonte de priorização (F10) e calibração (F2/F6), não critério de aprovação per-laudo. Análogo a `back_translation.in_sample = false`.

**H5 multidimensional:**
- (a) mediana `cosine_pt_pt` ≥ 0.98 (IC 95% bootstrap BCa)
- (b) p5 `cosine_pt_pt` ≥ 0.95
- (c) `structural_instability_rate` ≤ 0.02 (tolerância calibrada — acomoda 1 caso anômalo em 48 sem dar passagem livre a falha sistemática)

Teste estatístico para (a): t-test one-sided contra μ₀=0.95 + bootstrap BCa para CI da mediana.

---

### F8 — Persistência consolidada de validação (`validation_results.jsonl`)

**Objetivo:** **fonte única de verdade por laudo**. Consolida 6 fontes (F1–F7) em registro único com schema unificado, lógica de abstain explícita, fórmula de composite_score pré-registrada.

**Princípio governante — três tipos de "valor":**

| Estado | Significado | Efeito em `overall_passed` |
|---|---|---|
| `passed: true` | Fonte aplicável e laudo passou | Conta TRUE |
| `passed: false` | Fonte aplicável e laudo falhou | Reprova |
| `passed: null` | **Abstain** (T18 sem cobertura) | NÃO conta |
| `in_sample: false` ou `in_pair: false` | Fonte **não aplicável** | NÃO conta |

`duplicate_stability` é caso especial: **nunca entra em `overall_passed`** — fonte de priorização (F10) e calibração (F2/F6), não de aprovação.

**Algoritmo:**
1. Lê: `audit_deepseek.jsonl`, `back_translation.csv` + `bt_thresholds_empirical.json`, `intrinsic_metrics.csv`, `structural_checks.csv`, `lexical_consistency.csv` + `lexical_global_summary.json`, `modifier_preservation.csv` + `modifier_threshold_empirical.json`, `duplicate_pairs.csv` + `duplicate_stability.csv`
2. Para cada `report_id`, função modular `build_X()` por fonte aplica regras de schema unificado e abstain
3. Agrega via `overall_passed()`, `composite_score()`, `failure_reasons()` — três funções pequenas testáveis
4. Grava com `metadata` (schema_version, hashes do Atlas e prompt)

**Schema (válido para todos os laudos):**
```json
{
  "report_id": "...", "es_text": "...", "pt_text": "...", "birads_label": 4,
  "validations": {
    "semantic":           {"bertscore_f1", "cosine_es_pt", "chrf", "ter", "length_ratio", "passed"},
    "back_translation":   {"in_sample": false}  // OU {in_sample: true, ...metrics, passed},
    "structural":         {"category_pass", "measures_pass", "laterality_pass", "negation_pass", "anatomy_pass", "pt_drift", "all_structural_pass"},
    "lexical_birads":     {"overall_acceptable_rate", "lexical_loss_with_structural_pass", "lexical_loss_with_structural_fail", "passed"},
    "modifier_agreement": {"n_compared", "preservation_rate", "threshold", "passed"}  // passed pode ser null se sem cobertura,
    "audit_deepseek":     {"audit_final_status", "audit_final_score", "critical_error_count", "major_error_count", "minor_error_count", "has_critical_error", "passed"},
    "duplicate_stability": {"in_pair": false}  // OU {in_pair: true, ...metrics}
  },
  "overall_passed": true,
  "composite_score": 95.4,
  "failure_reasons": [],
  "metadata": {
    "consolidated_at": "...",
    "schema_version": "2026-04-28-v1",
    "atlas_glossary_hash": "sha256:...",
    "audit_prompt_hash": "sha256:..."
  }
}
```

**Composite score (fórmula v1 pré-registrada — `docs/superpowers/specs/composite_score_formula_v1.md`, tag git `composite-score-formula-pre-registered`):**

```
composite_score = Σ(w_i · Q_i) / Σ(w_i_active)
```

| Componente   | Métrica                          | Peso | Ativo se          |
|--------------|----------------------------------|------|-------------------|
| Q_semantic   | 100 · bertscore_f1               | 0.20 | sempre            |
| Q_structural | 100 · all_structural_pass        | 0.25 | sempre            |
| Q_lexical    | 100 · overall_acceptable_rate    | 0.15 | sempre            |
| Q_modifier   | 100 · preservation_rate          | 0.10 | passed != null    |
| Q_audit      | 100 · (1 − has_critical_error)   | 0.20 | sempre            |
| Q_back_trans | 100 · cosine_es_es_bt            | 0.10 | in_sample = true  |

Pesos renormalizam por fontes ativas (abstain/não-aplicável saem do denominador).

**Faixas de interpretação:**
- 90–100: alta qualidade
- 75–89: aceitável com revisão sugerida
- < 75: problemático (priorizado para MQM em F10)

**Defesa anti-p-hacking:** fórmula commitada com tag git `composite-score-formula-pre-registered` ANTES da execução. `git log` mostra que `validation_results.jsonl` veio depois.

**Decisão pré-registrada — `audit_final_status="review"` mapeia para `passed=True`:**

`review` só ocorre quando há findings validadas pela meta-auditoria SEM erro crítico (override mecânico T12.6 não disparou). Tratar como `passed=True` evita dupla penalização: erros críticos já entram em `Q_audit = 100·(1 − has_critical_error)`. Reprovar `review` aqui contaria o mesmo erro duas vezes. Casos genuinamente problemáticos sem severidade crítica não são perdidos — aparecem em `failure_reasons` via outras fontes (semantic/structural/lexical/modifier); se múltiplas reprovam, `overall_passed = False` mesmo com `audit.passed = True`.

A única classe que reprova em `audit_deepseek.passed` é `rejected`. Decisão registrada no commit pré-registro junto com a fórmula.

**Hierarquia interpretativa de aprovação per-laudo (4 níveis):**

| Nível | Campo | Definição | Uso |
|---|---|---|---|
| 1 | `has_critical_error` | T12.6 mecânico em C2/C3/C4/C6 disparou | **Critério clínico estrito** — alimenta H8 (≤1%) |
| 2 | `clinical_pass` | Todas fontes clinicamente relevantes ✓ (ignora modifier-only) | **Aprovação técnica clinicamente relevante** — headline TCC |
| 3 | `overall_passed` | Todas as 6 fontes ativas ✓ (incluindo modifier) | Agregado completo — FWER controlado |
| 4 | `warnings` | Lista de flags `modifier_divergence`, `duplicate_structural_instability` | **Priorização** (T22 Tier 4), não reprovação |

**Relação de inclusão:**
```
has_critical_error  ⊂  ¬clinical_pass  ⊂  ¬overall_passed
```

Todo erro crítico falha clinicamente; toda falha clínica falha agregado. Mas falha agregada (ex: modifier-only) pode preservar `clinical_pass = True` — divergência morfossintática (gênero/número) **não é erro clínico**, é warning para revisão.

**Por que essa separação importa:** sem `clinical_pass` explícito, banca olha `overall_passed_rate` (que inclui modifier-only failures) e pode interpretar como "X% reprovados clinicamente" quando na verdade muitos são apenas divergência morfológica. T23 §0 reporta as três taxas (clinical_pass, overall_passed, critical_error_rate) lado a lado.

**Verify cross-source obrigatório (gate antes do commit final):**
- `total_audited == 4357`
- `overall_passed True ≥ 90%`
- `audit_critical_count` consistente entre `validation_results` e `audit_deepseek_summary`
- `BT in_sample count` ≈ 250 (T14.B alvo)
- `modifier abstain ≤ 30%` (T18 cobertura ≥ 70%)
- `composite_score mediana ≥ 90`

Se algum falha → abortar antes do commit.

**Restart-safety:** processo idempotente — pode reconstruir do zero a partir dos outros artefatos.

**Valor para o TCC:** notebook lê **um único arquivo**; consistência total entre seções; JSON auditável por laudo; pré-registro defensível na banca.

---

### F9 — Concordância entre fontes (cross-source agreement)

**Objetivo:** quantificar convergência das **6 fontes** do `validation_results.jsonl` (T20) via Cohen's κ pareado, com filtro de abstain, distribuição de consenso ponderada por cobertura, exemplos de discordância direcionados, e estratificação por BI-RADS.

**Princípio metodológico:** fontes ortogonais devem ter κ baixo a moderado entre dimensões diferentes — é exatamente o que valida o framework. κ alto sugeriria redundância, não confirmação. Landis & Koch aplicado com cautela: testamos convergência entre **medidas complementares**, não confiabilidade entre raters do mesmo construto.

`duplicate_stability` **não entra na matriz κ** — fonte de priorização (F10), não de aprovação (consistente com `overall_passed` do F8).

#### Cobertura por par (3 categorias)

| Categoria | n esperado | Pares |
|---|---|---|
| Cobertura completa | ~4.357 | 6 pares entre {semantic, structural, lexical, audit} |
| Cobertura parcial (modifier) | ~3.000 | 4 pares modifier × outras |
| Cobertura amostral (BT) | ~250 | 5 pares BT × outras |

Total: 15 pares. `n_pairs` reportado junto com κ — CI largo em pares de baixa cobertura fica visível.

#### F9.1 Distribuição de consenso (com abstain)

Para cada laudo, conta apenas **fontes ativas** (não-abstain, não-out-of-sample):

```python
def consensus_distribution(record):
    sources = [v for k in [...] if (v := extract_passed(record, k)) is not None]
    return {"n_active_sources", "n_passed", "consensus_ratio", "all_pass", "all_fail"}
```

Reporta histograma `{n_passed: count}` e tabela cruzada `n_active × n_passed` (laudos com 4 fontes ativas, 5 fontes ativas, 6 fontes ativas).

**Critério H3:** ≥ 95% laudos com `consensus_ratio ≥ n_active - 1` (ou seja, no máximo 1 fonte discorda da maioria).

#### F9.2 Cohen's κ pareado (15 pares, com abstain)

```python
def kappa_with_ci(s_a, s_b, n_resamples=10000):
    pairs = [(a, b) for a, b in zip(s_a, s_b) if a is not None and b is not None]
    # Cohen's kappa + bootstrap BCa, n=10000
```

Bootstrap **BCa, n=10000** (alinhado com F3, F6, F7).

#### F9.3 Disagreement por par × sentido

Apenas pares com **κ < 0.5** são destacados. Saída separa os 2 sentidos:

```json
"semantic_vs_audit_deepseek": {
  "semantic_pass_audit_deepseek_fail": [{"report_id":"R1", "composite_score":80, ...}],
  "semantic_fail_audit_deepseek_pass": [{"report_id":"R2", ...}]
}
```

Top 5 por sentido, ordenados por composite_score crescente (casos mais informativos primeiro). Alimenta F10 (priorização MQM) e seção §10 do notebook (análise de erros).

#### F9.4 κ estratificado por BI-RADS (subsidia H6)

Por categoria 0–6, recalcula matriz κ sobre subset. Estratos com `n < 30` retornam `reason: insufficient_n_in_stratum` (sem κ).

**Interpretação H6:** κ estável entre categorias → sem viés. κ degrada em estrato → flag para investigação.

#### Output: `results/translation/agreement_report.json`

```json
{
  "metadata": {
    "schema_version": "2026-04-28-v1",
    "n_records": 4357,
    "kappa_method": "Cohen's kappa pairwise + bootstrap BCa n=10000",
    "abstain_policy": "report_id with None in either source filtered from pair"
  },
  "interpretation": {
    "note": "κ baixo entre fontes complementares é desejável (ortogonalidade)...",
    "expected_higher_kappa_pairs": ["semantic vs back_translation", ...],
    "expected_lower_kappa_pairs": ["structural vs semantic", ...]
  },
  "pairwise_kappa": {
    "semantic_vs_structural": {"kappa": 0.62, "ci_low": 0.58, "ci_high": 0.66, "n": 4357},
    ...
  },
  "consensus": {
    "histogram_n_passed": {6: 4012, 5: 198, 4: 28, ...},
    "crosstab_active_x_passed": {6: {6: 4012, ...}, 5: {...}}
  },
  "kappa_by_birads_strata": {
    "0": {"semantic_vs_audit_deepseek": {...}, ...},
    "1": {...}, ..., "6": {"reason": "insufficient_n_in_stratum"}
  },
  "disagreement_examples": {
    "<pair_with_kappa<0.5>": {"<a>_pass_<b>_fail": [...], "<a>_fail_<b>_pass": [...]}
  }
}
```

**Restart-safety:** roda em segundos sobre `validation_results.jsonl`.

---

### F10 — Amostra MQM com revisão humana cega (n=50)

**Objetivo:** revisão humana **cega** de 50 laudos para gerar fonte ortogonal independente do framework. Critério de seleção hierárquico baseado em flags do `validation_results.jsonl` (F8); MQM reduzido para 6 dimensões essenciais + 4 opcionais; protocolo pré-registrado.

#### Critério de seleção hierárquico (lê schema F8 — sem campos legados)

```python
def selection_priority(record):
    v = record["validations"]
    if v["audit_deepseek"]["has_critical_error"]: return (1, "critical_audit_error")
    if v["duplicate_stability"].get("requires_review"): return (2, "duplicate_structural_instability")
    if v["lexical_birads"]["lexical_loss_with_structural_fail"]: return (3, "lexical_loss_critical")
    if record["failure_reasons"]: return (4, "_".join(record["failure_reasons"][:3]))
    if v["back_translation"].get("in_sample") and not v["back_translation"]["passed"]: return (5, "back_translation_failed")
    return (99, "no_flag")  # controles "todos passam"
```

**Cotas por tier (estratificação composta tier × BI-RADS):**

| Tier | Quota | Reason |
|---|---|---|
| 1 | 10 | critical_audit_error |
| 2 | 8 | duplicate instability |
| 3 | 6 | lexical_loss_critical |
| 4 | 16 | multi-source disagreement |
| 5 | 5 | back_translation_failed |
| 99 | 5 | controles |

Total: 50 laudos. Dentro de cada tier, balanceado por categoria BI-RADS quando possível.

#### Protocolo de revisão (pré-registrado, tag git `mqm-protocol-pre-registered`)

| Decisão | Valor |
|---|---|
| Tamanho da amostra | 50 (não 50-100) |
| Modalidade | **cega** — revisor NÃO vê composite_score nem failure_reasons durante o preenchimento |
| Tempo estimado | ~3 min/laudo × 50 = 3-4h |
| Critério de "rejeitar" | `mqm_accuracy < 2 OR has_critical_error_human = True` |
| Resolução de divergências | flag manual em `uncertainty` (sem revisor secundário) |

**Por que cegamento:** sem ele, MQM vira validação enviesada do framework. Com cegamento, MQM é fonte independente — Cohen's κ humano × auditor LLM testa convergência genuína.

#### MQM reduzido — 6 dimensões essenciais + 4 opcionais

**Essenciais (todas as linhas):**
- `mqm_accuracy` (Likert 0–4) — fidelidade semântica
- `mqm_terminology` (0–4) — preservação BI-RADS
- `mqm_omissions` (0/1) — omissão clínica
- `mqm_birads_category_correct` (0/1)
- `mqm_negation_OK` (0/1)
- `mqm_laterality_correct` (0/1)

**Opcionais (preencher só se discrepância evidente):**
- `mqm_fluency`, `mqm_additions`, `mqm_pt_br_correct`, `mqm_measures_correct`

**Justificativa:** 10 dimensões × 50 laudos = 500 julgamentos → fadiga compromete qualidade. 6 essenciais cobrem H1 (accuracy) + H2 (terminology + omissions) + H3 (laterality + negation + birads). Opcionais cobrem dimensões secundárias.

#### Excel com 2 sheets (cegamento operacional)

| Sheet | Conteúdo | Visibilidade |
|---|---|---|
| `Revisão` | report_id, es_text, pt_text, birads_label, selection_reason + colunas MQM em branco + `uncertainty` + `reviewer_notes` + `final_verdict` | visível para o revisor |
| `Evidence` | composite_score, failure_reasons, audit_final_status, has_critical_error, passed por fonte, in_sample, in_pair, etc. | **oculta** até pós-revisão |

#### Outputs pós-revisão (alimentam F11)

- `results/translation/human_review_results.csv` — uma linha por laudo com colunas MQM preenchidas + `has_critical_error_human` + `mqm_overall_pass`
- `results/translation/human_review_summary.json`:
```json
{
  "n_reviewed": 50,
  "n_critical_error_human": 1,
  "critical_error_rate_human": 0.02,
  "median_mqm_accuracy": 4.0,
  "median_mqm_terminology": 4.0,
  "n_omissions_flagged": 2,
  "n_uncertainty_flagged": 0,
  "verdict_distribution": {"approve": 45, "fix": 4, "reject": 1}
}
```

`has_critical_error_human` permite **κ humano × auditor LLM** (F11 §9): se κ ≥ 0.4, calibração cruzada validada.

#### Entrega TCC

- Tabela de resultados (50 laudos)
- Cohen's κ humano × DeepSeek (`has_critical_error` × `has_critical_error_human`)
- Cohen's κ humano × structural checks
- Análise de divergências por tier (qualitativa)
- κ humano-humano (se houver revisor secundário; sem ele, reportar como limitação)

**Entrega TCC:**
- Tabela de resultados
- Cohen's κ humano × DeepSeek
- Cohen's κ humano × structural checks
- Cohen's κ humano × back-translation verdict
- Cohen's κ humano × humano (você × orientador, confiabilidade do gold)
- Análise qualitativa de erros (taxonomia + frequência)

---

### F11 — Notebook consolidado P1-T12 (headline crítica + Holm-Bonferroni + reproducibility)

**`notebooks/01_translation_report.ipynb`** — estrutura:

| Seção | Conteúdo |
|---|---|
| **0. Headline executiva** | Tabela de 1 página (`build_executive_summary()`) — primeira saída do notebook |
| **1. Visão geral** | Volume, distribuição BI-RADS, **headline = taxa de erro crítico (T12.6/H8)** + composite mediana + overall_passed rate |
| **2. Qualidade semântica (F3)** | BERTScore-F1 + chrF++ + cosine + length_ratio principais; TER apêndice. **BLEU excluído** (justificativa em §4.2.2 do TCC) |
| **3. Back-translation (F2)** | Caveat amostra de 250 com mesmo modelo família + 5 mitigações + threshold empírico |
| **4. Structural checks (F4)** | `all_structural_pass` rate + breakdown por dimensão (categoria, medidas, lateralidade, negação, anatomia, drift) |
| **5. Léxico BI-RADS (F5)** | `overall_canonical_rate` × `overall_acceptable_rate`, anomalias, top-20 termos divergentes |
| **5b. Morfossintaxe (F6)** | `preservation_rate`, `divergence_breakdown`, abstain rate, threshold empírico |
| **6. Estabilidade operacional (F7)** | Caveat operacional, 4 camadas, 3 níveis, structural instability rate |
| **7. Auditoria DeepSeek (F1)** | C1–C7 distributions + meta-validação (kept vs refuted) |
| **7b. Calibração GPT-4o-mini (F1 sub-estudo)** | Cohen's κ DeepSeek↔GPT por critério, decisão `PRIMARY_STABLE`/`MODERATE`/`DOWNGRADE` |
| **8. Concordância entre fontes (F9)** | κ heatmap das 6 fontes + nota interpretativa + κ por BI-RADS (subsidia H6) |
| **9. Revisão humana (F10)** | κ humano × LLM auditor; cross-validation `has_critical_error_human` × LLM |
| **10. Análise de erros** | **Taxonomia via `failure_reasons` do F8** — distribuição, top-20 por razão, recomendações |
| **11. Composite Score** | Distribuição, faixas (90+, 75-89, <75), referência à tag `composite-score-formula-pre-registered` |
| **12. Reproducibility statement** | **Auto-gerado** — hashes, modelos, parâmetros, custos, tags pré-registradas |

**Princípios:**
- **"T-x produz, F11 lê"** — todos os summary JSONs (F1, F3, F6, F7, F9, F10) são consumidos diretamente, sem recomputo
- **Holm-Bonferroni** sobre H1–H8 — FWER controlado em α=0.05, 8 hipóteses confirmatórias declaradas pré-execução
- **Hipóteses exploratórias** (surgidas durante análise) reportadas separadamente sem correção, marcadas como `exploratory: True`

**Fonte primária do notebook:** `validation_results.jsonl` (F8) + 8 summary JSONs.

---

## 5. Quality Score Composto (executive summary)

Score único `[0, 100]` agregando todas as evidências:

```
Q_total = 0.30 · Q_semantic    (H1, H6)
        + 0.25 · Q_lexical     (H2)
        + 0.15 · Q_structural  (H4) ← novo eixo
        + 0.15 · Q_audit       (H3, DeepSeek)
        + 0.10 · Q_back_trans  (H1, H3) ← novo eixo
        + 0.05 · Q_reprod      (H5)
```

Onde:
- `Q_semantic = 100 · median(BERTScore_F1)` (clip a [0,100])
- `Q_lexical = 100 · ( 0.5·canonical_ratio_global + 0.3·(1−anomaly_rate) + 0.2·modifier_agreement )`
- `Q_structural = 100 · mean(category_pass, measures_pass, laterality_pass, negation_pass, no_pt_drift)`
- `Q_audit = 100 · (1 − fraction_with_critical)` — fração de laudos COM ≥1 inconsistência `critical` (T12.6). Substitui o `score_global` 0–10 (que mistura severidades). Headline metric do TCC.
- `Q_back_trans = 100 · median(cos_es_es_bt)`
- `Q_reprod = 100 · median(cosine_intra_duplicates)`

**Pesos justificados:**
- 0.30 semântica (preservação de significado é o que importa para classificação)
- 0.25 léxico (terminologia BI-RADS para extração regra-baseada)
- 0.15 estrutural (preservação programática de elementos críticos)
- 0.15 auditor LLM (validação suporte)
- 0.10 back-translation (validação independente)
- 0.05 reprodutibilidade (sanity check)

**Faixas interpretativas:**

| Q_total | Veredito |
|---|---|
| ≥ 90 | "Tradução de alta qualidade adequada para extração automática" |
| 80–89 | "Qualidade boa, requer pós-validação em casos limítrofes" |
| 70–79 | "Qualidade aceitável, requer revisão humana sistemática" |
| < 70 | "Requer reprocessamento" |

---

## 6. Ameaças à validade e mitigações

| Ameaça | Risco | Mitigação |
|--------|-------|-----------|
| **Family bias do tradutor original** | Gemini pode favorecer suas próprias escolhas | Back-translation usa **Gemini 2.5 Flash com `thinking_budget=0` + temperature=0 + prompt minimalista**; mitigado por direção inversa (PT→ES) e cross-check com checks programáticos F4 |
| **Family bias do auditor** | DeepSeek pode ter blind spots | Triangulação com 3 outras fontes não-LLM (intrínseca, BT, structural) |
| **Confounding métrica única** | métrica positiva esconde defeito | 5 métricas intrínsecas + 5 checks estruturais + BT + LLM + humano |
| **Ground-truth ausente** | nenhuma referência humana | F10: amostra MQM 50–100 com orientador (gold parcial) |
| **Sample bias na revisão humana** | concentra em fáceis | F10 estratifica por discordância multifonte e BI-RADS |
| **Reprodutibilidade do tradutor** | variação | F7 (duplicatas) + temperature=0 confirmado |
| **Viés do glossário Atlas** | glossário incompleto | F5.A construído de fonte oficial CBR/SBM; F5.C reporta termos fora do glossário |
| **Falso positivo retroativo** (auditor cobra termos Atlas que o tradutor nunca viu) | reprovações injustas por desalinhamento glossário-cobrança | F5.A com **retrocompatibilidade**: toda PT do glossário original aparece em `pt_variants_acceptable` do Atlas. Verificação automática `verify_atlas_backward_compat.py` antes de commit |
| **Cherry-picking** | seleção de evidência | Pré-registro: TODAS as métricas reportadas |
| **Drift PT-pt** | tradução vaza variante europeia | F4.6 detecta cognatos diagnósticos (H7) |
| **Variação por categoria BI-RADS** | qualidade não-uniforme | H6: Kruskal-Wallis estratificado |
| **Round-trip semântica trivial** | BT pode passar mesmo com erro | Combinação com structural checks (regex não falha por paráfrase) |

---

## 7. Reprodutibilidade total (audit trail)

Toda fase produz:
1. **Artefato de saída** (JSONL/CSV) versionado em git
2. **Hash do prompt** (F1, F2) registrado em metadata
3. **Modelo + versão exata** (`gpt-4o-mini-2024-07-18`, `deepseek-chat-v3-...`)
4. **Random seed** (irrelevante a T=0 mas registrado)
5. **Timestamp UTC** de cada chamada
6. **Tokens consumidos** + custo
7. **`validation_results.jsonl`** consolidado é a fonte única para o notebook

O notebook tem seção "Reproducibility statement" com todos os parâmetros e SHAs de commit.

**Commits granulares:** cada fase um commit separado.

---

## 8. Estrutura proposta para o capítulo de Resultados do TCC

```
4. AVALIAÇÃO DA TRADUÇÃO

  4.1 Framework de avaliação
      Triangulação multi-fonte
      Hipóteses operacionais H1–H7

  4.2 Métricas intrínsecas
      4.2.1 Preservação semântica (cosine, BERTScore)
      4.2.2 Métrica lexical (chrF++) — justificativa para excluir BLEU
      4.2.3 Apêndice: TER (edit distance complementar)
      4.2.3 Resultados (distribuições, CIs)

  4.3 Back-translation independente
      4.3.1 Configuração (GPT-4o-mini PT→ES)
      4.3.2 Comparação ES_orig × ES_bt
      4.3.3 Resultados

  4.4 Checks programáticos estruturais
      4.4.1 Categoria BI-RADS
      4.4.2 Medidas e lateralidade
      4.4.3 Negação e anatomia
      4.4.4 Variante regional (PT-br)
      4.4.5 Resultados consolidados

  4.5 Avaliação léxica BI-RADS
      4.5.1 Glossário expandido (CBR/SBM)
      4.5.2 Consistência terminológica global (overall_acceptable_rate)
      4.5.3 Anomalias léxicas

  4.5b Concordância morfossintática (preservation_rate, threshold empírico)

  4.6 Auditoria por LLM (DeepSeek)
      4.6.1 Configuração e prompt
      4.6.2 Resultados C1–C7
      4.6.3 Meta-validação

  4.6b Sub-estudo de calibração (GPT-4o-mini sobre subset ~250)
      Cohen's κ DeepSeek↔GPT por critério; decisão PRIMARY_STABLE/MODERATE/DOWNGRADE

  4.7 Reprodutibilidade (estabilidade em T=0)
      4.7.1 Análise de duplicatas
      4.7.2 Resultados

  4.8 Concordância entre fontes
      4.8.1 Consenso multifonte
      4.8.2 Cohen's κ pareado

  4.9 Revisão humana (MQM)
      4.9.1 Amostragem por discordância
      4.9.2 Protocolo de revisão
      4.9.3 Concordância humano × fontes

  4.10 Análise de erros
      4.10.1 Taxonomia (MQM)
      4.10.2 Frequência por tipo
      4.10.3 Casos críticos
      4.10.4 Causa raiz e recomendações

  4.11 Quality Score Composto e discussão

  4.12 Limitações e ameaças à validade

  4.13 Síntese: a tradução suporta a tarefa-alvo?
```

---

## 9. Tabela-resumo dos artefatos

| Arquivo | Fase | Linhas | Propósito |
|---------|------|--------|-----------|
| `audit_deepseek.jsonl` | F1 | 4.357 | auditoria completa DeepSeek |
| `back_translation.csv` | F2 | 4.357 | PT→ES + métricas round-trip |
| `intrinsic_metrics.csv` | F3 | 4.357 | cosine, BERTScore-F1, chrF++, length_ratio (principais) + TER (apêndice). Sem BLEU. |
| `structural_checks.csv` | F4 | 4.357 | regex determinístico (categoria, medidas, etc) |
| `birads_glossary_atlas_es_pt.json` | F5.A | ~200 termos | glossário expandido |
| `lexical_consistency.csv` | F5.B | ~200 | 1 linha por termo Atlas |
| `lexical_anomalies.csv` | F5.C | variável | 1 linha por anomalia |
| `modifier_preservation.csv` | F6 | 4.357 | concordância gramatical |
| `duplicate_stability.csv` | F7 | 48 | pares de duplicatas |
| **`validation_results.jsonl`** | **F8** | **4.357** | **fonte única consolidada** |
| `agreement_report.json` | F9 | 1 | estatística inter-fontes |
| `human_review_sample.xlsx` | F10 | 50–100 | MQM para preenchimento |
| `01_translation_report.ipynb` | F11 | 1 | relatório final TCC |

---

## 10. Pontos pendentes para decisão

### A. Premissas científicas
- [ ] Triangulação multi-fonte (5 eixos: intrínsecas + structural + BT + LLM + humano)
- [ ] Hipóteses H1–H7 como definidas
- [ ] Quality Score com pesos 0.30/0.25/0.15/0.15/0.10/0.05

### B. Escopo operacional
- [ ] F2: back-translation 4.357 laudos via Gemini 2.5 Flash PT→ES com thinking OFF (~$3.05)
- [ ] F3: BERTScore-F1 + chrF++ + cosine + length_ratio como métricas primárias; TER apêndice; BLEU excluído (não defensável em ES↔PT)
- [ ] F4: checks programáticos (categoria BI-RADS, medidas, lateralidade, negação, anatomia, drift PT-pt)
- [ ] F5.A: construir glossário Atlas CBR/SBM (~200 termos)
- [ ] F8: persistência consolidada em `validation_results.jsonl`
- [ ] F10: amostra 50–100 estratificada por discordância multifonte
- [ ] F11: seção dedicada de análise de erros no notebook

### C. Saídas
- [ ] Notebook único `01_translation_report.ipynb` com 12 seções
- [ ] Formatos: JSONL para auditorias e validação consolidada, CSV para métricas, JSON para agregados estatísticos

### D. Recursos
- [ ] Custo total ~$3.27 USD em APIs (R$ ~16)
- [ ] Tempo de máquina ~10h (F1+F2 paralelizados)
- [ ] Tempo de implementação 2–3 dias úteis

---

## 11. Referências fundamentais

- ACR. *Breast Imaging Reporting and Data System (BI-RADS) Atlas, 5th edition*. American College of Radiology, 2013.
- Colégio Brasileiro de Radiologia (CBR) — adaptação BI-RADS PT-br.
- Sociedade Brasileira de Mastologia (SBM) — laudo padronizado.
- Campbell, D. T., & Fiske, D. W. (1959). *Convergent and discriminant validation by the multitrait-multimethod matrix*. Psychological Bulletin.
- Lommel, A., Uszkoreit, H., & Burchardt, A. (2014). *Multidimensional Quality Metrics (MQM): A framework for declaring and describing translation quality metrics*. Tradumàtica.
- Freitag, M., et al. (2021). *Experts, errors, and context: A large-scale study of human evaluation for machine translation*. TACL.
- Landis, J. R., & Koch, G. G. (1977). *The measurement of observer agreement for categorical data*. Biometrics, 33(1), 159–174.
- Popović, M. (2017). *chrF++: words helping character n-grams*. WMT.
- Papineni, K., et al. (2002). *BLEU: a method for automatic evaluation of machine translation*. ACL.
- Zhang, T., et al. (2020). *BERTScore: Evaluating text generation with BERT*. ICLR.
- Snover, M., et al. (2006). *A study of translation edit rate with targeted human annotation*. AMTA.
- Sennrich, R. (2017). *How grammatical is character-level neural machine translation? Assessing MT quality with contrastive translation pairs* — defesa do round-trip / back-translation como avaliação.

---

**Status do documento:** rascunho aguardando aprovação final do orientado para iniciar implementação.

**Próximo passo:** após aprovação, criar plano de implementação fase-a-fase em `docs/superpowers/plans/2026-04-26-plan-translation-evaluation.md`.
