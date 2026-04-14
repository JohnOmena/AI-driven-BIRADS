# AI-Driven BI-RADS Classification on Mammography Reports — Design Spec

**Data:** 2026-04-13
**Base:** Replicação do paper "AI-Driven Lung-RADS Classification on CT Reports" (Ferreira et al., IEEE CBMS 2025), adaptado para BI-RADS em mamografia.
**Repositório:** https://github.com/JohnOmena/AI-driven-BIRADS.git

---

## Resumo do Projeto

Avaliar a eficácia de LLMs na extração de características de achados mamográficos a partir de laudos em espanhol e português, utilizando question-answering (QA), para classificação automatizada BI-RADS. O pipeline opera em dois idiomas paralelos (ES e PT), com quatro LLMs, duas estratégias de prompting, e três motores de decisão para classificação.

### Decisões-chave

| Aspecto | Decisão |
|---|---|
| Domínio | BI-RADS (mamografia) em vez de Lung-RADS (CT) |
| Idiomas | Dois pipelines paralelos: 100% espanhol + 100% português |
| Base de dados | 4.357 laudos de mamografia em espanhol (`reports_raw_canonical.csv`) |
| Tradução | Módulo dedicado: base completa ES→PT com validação de fidelidade (Gemini 2.0 Flash + DeepSeek-V3) |
| Pré-processamento | Filtro de achado único (6 passos) + filtro de completude via LLM |
| Question table | 13 perguntas (nódulo único, calcificações, massa, localização) |
| LLMs | GPT-4o, Gemini 2.0 Flash, Llama 3.3 70B, DeepSeek-V3 (arquitetura modular) |
| Prompting | Zero-shot CoT + Few-shot (5 exemplos por similaridade) |
| Consistência | 3 repetições por query, métricas Cp/Cn |
| Temperatura | 0 (determinística) |
| Chamadas API | Independentes por relatório, sem cache |
| Custos | Monitoramento com limites máximos por API |
| Divisão dataset | 70/30 estratificada (exemplos few-shot / teste) |
| Motores de decisão | Rule-based + Árvore de Decisão + Rede Bayesiana |
| Avaliação | Com e sem ground truth por pergunta; P/R/F1; Friedman/Nemenyi |
| Visualizações | Bar charts, boxplots, heatmaps, matrizes de confusão |
| Armazenamento | CSV/JSON |
| Linguagem | Python com PyTorch, Hugging Face, regex |
| Arquitetura | Scripts independentes (Abordagem A) com config via CLI + objeto |

---

## Estrutura de Pastas

```
AI-driven-BIRADS/
├── configs/
│   ├── question_table/
│   │   └── qt_mass_calc.json
│   ├── models.yaml
│   ├── lexicon/
│   │   ├── birads_lexicon_es.json
│   │   └── birads_lexicon_pt.json
│   ├── classification/
│   │   ├── birads_rules.json
│   │   ├── decision_tree_params.json
│   │   └── bayesian_network.json
│   └── prompts/
│       ├── zero_shot_cot_pt.txt
│       ├── zero_shot_cot_es.txt
│       ├── few_shot_pt.txt
│       └── few_shot_es.txt
├── data/
│   ├── reports_raw_canonical.csv
│   ├── reports_translated_pt.csv
│   ├── reports_filtered_es.csv
│   └── reports_filtered_pt.csv
├── src/
│   ├── translation/
│   ├── preprocessing/
│   ├── embedding/
│   ├── qa/
│   ├── postprocessing/
│   ├── classification/
│   └── evaluation/
├── results/
├── notebooks/
├── doc/
│   └── AI-Driven Lung-RADS Classification on CT Reports.pdf
├── docs/
│   └── superpowers/
│       └── specs/
└── requirements.txt
```

---

## Ciclo de Qualidade e Documentação (todas as seções)

Cada etapa do pipeline inclui obrigatoriamente, após a implementação:

### 1. Inspeção de código
- Revisar o código buscando bugs, edge cases não tratados, inconsistências
- Verificar aderência ao design aprovado
- Checar tipos de dados e configuração via CLI e via objeto
- **Commit** após correções

### 2. Testes
- Testar com amostra reduzida antes de rodar o pipeline completo
- Validar saídas contra casos conhecidos/esperados
- Verificar integridade dos arquivos gerados (JSON válido, CSV correto)
- Testar edge cases (relatórios vazios, respostas inesperadas, caracteres especiais)
- **Commit** após testes

### 3. Correções
- Corrigir bugs e problemas encontrados nos testes
- **Commit** após fixes

### 4. Execução completa
- Rodar o pipeline completo sobre todos os dados
- **Commit** com resultados

### 5. Análise
- Analisar resultados e identificar oportunidades de melhoria
- Documentar limitações encontradas
- **Commit** após análise

### 6. Propor melhorias
- Sugerir ajustes no pipeline se os resultados indicarem necessidade
- Implementar melhorias aprovadas
- **Commit** após melhorias

### 7. Documentar e gerar relatório
- Documentar o que foi feito, decisões tomadas e resultados obtidos
- Gerar Jupyter notebook auto-contido em `notebooks/` com:
  - Descrição da etapa e seu objetivo
  - Código executado com outputs visíveis
  - Visualizações dos resultados intermediários
  - Métricas e estatísticas relevantes
  - Observações e próximos passos
- **Commit** após documentação

### Notebooks por seção

| Seção | Notebook |
|---|---|
| 1 — Tradução | `notebooks/01_translation_report.ipynb` |
| 2 — Pré-processamento | `notebooks/02_preprocessing_report.ipynb` |
| 3 — Embedding | `notebooks/03_embedding_report.ipynb` |
| 4 — QA Pipeline | `notebooks/04_qa_pipeline_report.ipynb` |
| 5 — Pós-processamento | `notebooks/05_postprocessing_report.ipynb` |
| 6 — Consistência | `notebooks/06_consistency_report.ipynb` |
| 7 — Avaliação QA | `notebooks/07_qa_evaluation_report.ipynb` |
| 8 — Classificação | `notebooks/08_classification_report.ipynb` |
| 9 — Avaliação Final | `notebooks/09_final_evaluation_report.ipynb` |

### Fluxo

```
Implementar → commit → Inspecionar → commit → Testar → commit → Corrigir → commit → Rodar completo → commit → Analisar → commit → Propor melhorias → commit → Documentar + Notebook → commit
```

---

## Seção 1: Etapa 0 — Módulo de Tradução

**Objetivo:** Gerar uma base completa em português (4.357 relatórios) a partir da base original em espanhol, 100% fiel ao texto original, com preservação do léxico BI-RADS.

### Estratégia de tradução

- Dois LLMs traduzem cada relatório independentemente: **Gemini 2.0 Flash** + **DeepSeek-V3**
- Cada LLM recebe o relatório em espanhol + prompt com instruções explícitas de:
  - Traduzir fielmente, sem omitir, resumir ou interpretar
  - Preservar a estrutura e formatação do texto
  - Usar o léxico BI-RADS oficial em português
  - Glossário BI-RADS ES↔PT incluído no prompt para termos críticos
- Temperatura 0 em ambos

### Validação de fidelidade

- Comparar as duas traduções automaticamente:
  - **Similaridade semântica** (embedding + cosine similarity) — threshold alto (e.g., >0.95)
  - **Divergências lexicais BI-RADS** — checar se termos-chave BI-RADS coincidem
- Relatórios com divergência → marcados para revisão
- Relatório final: estatísticas de concordância

### Saída

- `data/reports_translated_pt.csv`
- `results/translation/divergences.json`
- `results/translation/stats.json`

### Configuração

```python
CONFIG = {
    "source_path": "data/reports_raw_canonical.csv",
    "output_path": "data/reports_translated_pt.csv",
    "llm_primary": "gemini-2.0-flash",
    "llm_secondary": "deepseek-v3",
    "similarity_threshold": 0.95,
    "temperature": 0,
    "birads_glossary_path": "configs/birads_glossary_es_pt.json",
}
```

---

## Seção 2: Etapa 1 — Pré-processamento e Filtro de Achado Único + Filtro de Completude

**Objetivo:** Identificar e manter apenas relatórios com exatamente um achado (nódulo/massa) e com informações suficientes para responder todas as perguntas da question table.

### Limpeza de dados

- Remoção de caracteres especiais e emojis
- Adição de espaços entre palavras coladas
- Normalização de encoding

### Pesquisa do léxico BI-RADS (recurso prévio)

Antes de implementar o filtro, pesquisar sistematicamente no léxico oficial ACR BI-RADS (5ª edição) para compilar dicionários bilíngues (ES/PT) cobrindo:

- **Seções de laudos mamográficos:** e.g., ES: "hallazgos", "conclusión", "indicación clínica", "técnica", "comparación", "composición mamaria"; PT: "achados", "conclusão", "indicação clínica", "técnica", "comparação", "composição mamária"
- **Termos de achados:** e.g., ES: "nódulo", "masa", "asimetría", "distorsión arquitectural", "calcificación", "lesión"; PT: "nódulo", "massa", "assimetria", "distorção arquitetural", "calcificação", "lesão"
- **Negação e ausência:** e.g., ES: "no se observa", "sin evidencia de", "ausencia de", "no se identifica", "sin hallazgos", "descarta"; PT: "não se observa", "sem evidência de", "ausência de", "não se identifica", "sem achados", "descarta"
- **Incerteza e hipótese:** e.g., ES: "posible", "probable", "sugiere", "no se puede descartar", "a correlacionar"; PT: "possível", "provável", "sugere", "não se pode descartar", "a correlacionar"
- **Quantificadores de unidade:** e.g., ES: "un", "único", "solitario", "aislado"; PT: "um", "único", "solitário", "isolado"
- **Quantificadores de multiplicidade:** e.g., ES: "múltiples", "varios", "dos", "tres", "numerosos", "algunos", "al menos dos"; PT: "múltiplos", "vários", "dois", "três", "numerosos", "alguns", "pelo menos dois"
- **Lateralidade e localização:** e.g., ES: "mama derecha", "mama izquierda", "CSE", "CSI", "CIE", "CII", "retroareolar", "región axilar"; PT: "mama direita", "mama esquerda", "QSE", "QSI", "QIE", "QII", "retroareolar", "região axilar"

Armazenados em:
- `configs/lexicon/birads_lexicon_es.json`
- `configs/lexicon/birads_lexicon_pt.json`

### Filtro de achado único — pipeline em 6 passos

**1. Normalização textual**
- Converter para minúsculas, remover acentos, padronizar símbolos ("×" → "x")

**2. Segmentação por seções**
- Separar o laudo usando os termos de seção do léxico BI-RADS
- Apenas seções de achados e conclusão consideradas para contagem

**3. Busca de candidatos**
- Usar os termos de achados do léxico BI-RADS para identificar menções
- Extrair cada menção com contexto (janela de palavras)

**4. Filtro de negação e incerteza**
- Aplicar algoritmo tipo NegEx/ConText usando os dicionários de negação e incerteza do léxico BI-RADS
- Descartar menções negadas e hipotéticas

**5. Análise de quantificadores**
- Usar os dicionários de unidade/multiplicidade do léxico BI-RADS
- Multiplicidade → descarte; unidade → manter

**6. Deduplicação por assinatura de lesão**
- Extrair lateralidade + localização + medida usando o léxico BI-RADS
- Assinatura: `(lateralidade, localização, medida)`
- Mesma assinatura em seções diferentes → uma única lesão
- Exatamente 1 assinatura distinta → mantido

### Filtro de completude via LLM

Após o filtro de achado único, verificar quais relatórios contêm informações suficientes para responder todas as perguntas da question table.

**Estratégia:**
- Submeter cada relatório filtrado a **Gemini 2.0 Flash** e **DeepSeek-V3**
- Prompt: relatório + question table, pedir para responder todas as perguntas
- Critérios de "informação suficiente":
  - **Booleanas (Q1–Q11):** "Sim" ou "Não". Se "não informado" ou branco → "Não" (resposta padrão)
  - **Numérica (Q12 — tamanho):** modelo extrai valor numérico em mm
  - **Categórica (Q13 — localização):** modelo identifica localização ou atribui "Outros"
- Relatório mantido se **ambos os LLMs** conseguem responder Q12 e Q13
- Divergências significativas → marcados para revisão

### Saída

- `data/reports_filtered_es.csv`
- `data/reports_filtered_pt.csv`
- `results/preprocessing/filter_stats.json` — total, mantidos, descartados, distribuição BI-RADS, motivos de descarte
- `results/preprocessing/completeness_check.json`
- `results/preprocessing/completeness_divergences.json`

### Configuração

```python
CONFIG = {
    "source_es_path": "data/reports_raw_canonical.csv",
    "source_pt_path": "data/reports_translated_pt.csv",
    "output_es_path": "data/reports_filtered_es.csv",
    "output_pt_path": "data/reports_filtered_pt.csv",
    "stats_output_path": "results/preprocessing/filter_stats.json",
    "lexicon_es_path": "configs/lexicon/birads_lexicon_es.json",
    "lexicon_pt_path": "configs/lexicon/birads_lexicon_pt.json",
    "lang": "es",
    "negation_algorithm": "negex",
    "completeness_llm_primary": "gemini-2.0-flash",
    "completeness_llm_secondary": "deepseek-v3",
    "completeness_temperature": 0,
    "question_table_path": "configs/question_table/qt_mass_calc.json",
}
```

---

## Question Table Revisada (13 perguntas)

| # | field | question_pt | answer_type |
|---|---|---|---|
| 1 | single_nodule | Temos apenas um nódulo sendo descrito no exame atual? | boolean |
| 2 | has_calcifications | Há calcificações descritas no exame atual? | boolean |
| 3 | has_mass | Há massa ou nódulo descrito no exame atual? | boolean |
| 4 | calc_morph_fine_linear_branching | A morfologia das calcificações é fine linear ou fine-linear branching? | boolean |
| 5 | calc_morph_fine_pleomorphic | A morfologia das calcificações é fine pleomorphic? | boolean |
| 6 | calc_morph_typically_benign | As calcificações têm morfologia tipicamente benigna? | boolean |
| 7 | calc_dist_segmental | A distribuição das calcificações é segmentar? | boolean |
| 8 | calc_dist_linear | A distribuição das calcificações é linear/ductal? | boolean |
| 9 | calc_dist_grouped | A distribuição das calcificações é agrupada/clustered? | boolean |
| 10 | mass_margin_spiculated | A margem da massa ou nódulo é espiculada? | boolean |
| 11 | mass_shape_irregular | A forma da massa ou nódulo é irregular? | boolean |
| 12 | mass_size_mm | Qual é o tamanho da massa ou nódulo em milímetros? | number |
| 13 | nodule_location | Qual a localização do nódulo ou massa na mama? | categorical |

**Respostas padrão:**
- Boolean: "Não" quando a informação está ausente, não informada ou em branco
- Numérica: valor extraído em mm (ou null se não informado)
- Categórica: quadrante/região BI-RADS ou "Outros" quando não é clara

---

## Seção 3: Etapa 2 — Embedding e Similaridade de Documentos

**Objetivo:** Calcular embeddings dos relatórios filtrados e construir matriz de similaridade para selecionar os 5 exemplos mais similares para cada relatório de teste no few-shot learning.

### Divisão do dataset

- 70% → banco de exemplos (para seleção few-shot por similaridade)
- 30% → conjunto de teste (input para QA zero-shot e few-shot)
- Divisão estratificada por `birads_label`
- Mesma divisão aplicada a ambas as bases (ES e PT) — mesmos `report_id` em cada split

### Modelo de embeddings

- `paraphrase-multilingual-mpnet-base-v2` (Hugging Face / Sentence Transformers)
- Suporte nativo a espanhol e português

### Pipeline

1. Carregar relatórios filtrados (ES ou PT)
2. Dividir em banco de exemplos (70%) e teste (30%) com estratificação
3. Gerar embeddings para todos os relatórios
4. Calcular matriz de cosine similarity entre teste e banco de exemplos
5. Para cada relatório de teste, selecionar os top-5 mais similares

### Saída

- `results/embedding/split_es.json` — IDs de cada split para ES
- `results/embedding/split_pt.json` — IDs de cada split para PT
- `results/embedding/embeddings_es.npy`
- `results/embedding/embeddings_pt.npy`
- `results/embedding/top5_neighbors_es.json`
- `results/embedding/top5_neighbors_pt.json`

### Configuração

```python
CONFIG = {
    "source_es_path": "data/reports_filtered_es.csv",
    "source_pt_path": "data/reports_filtered_pt.csv",
    "output_dir": "results/embedding/",
    "model_name": "paraphrase-multilingual-mpnet-base-v2",
    "train_ratio": 0.70,
    "test_ratio": 0.30,
    "top_k": 5,
    "stratify_column": "birads_label",
    "random_seed": 42,
    "lang": "es",
}
```

---

## Seção 4: Etapa 3 — Pipeline de Question Answering (QA)

**Objetivo:** Para cada relatório de teste, submeter o relatório + prompt + question table a cada LLM e obter respostas estruturadas em JSON.

### Modelos

- GPT-4o (via OpenAI API)
- Gemini 2.0 Flash (via Google AI API)
- Llama 3.3 70B (via Together AI API)
- DeepSeek-V3 (via OpenAI-compatible API)

### Estratégias de prompting

**Zero-shot CoT:**
- Prompt composto por 3 partes:
  1. Relatório original (ES ou PT conforme o pipeline)
  2. Instruções de extração + question table vazia (13 perguntas)
  3. Requisitos adicionais (responder "Não" por padrão, formato JSON, conhecimentos médicos BI-RADS de referência)
- Instrução de chain-of-thought: "Pense passo a passo antes de responder"

**Few-shot (5 exemplos por similaridade):**
- Mesmo prompt do zero-shot CoT, acrescido de 5 exemplos
- Exemplos selecionados pelo módulo de embedding (Seção 3)
- Exemplos vêm do banco de exemplos (70%) com respostas do ground truth (quando disponível) ou validadas pelo filtro de completude

### Execução

- Uma requisição independente por relatório (sem contexto entre chamadas)
- Temperatura 0 em todos os modelos
- 3 repetições por query para avaliação de consistência
- Resposta solicitada em formato JSON

### Volume de chamadas por pipeline (ES ou PT)

```
N_teste × 4 modelos × 2 estratégias × 3 repetições
Ex: se N_teste = 100 → 100 × 4 × 2 × 3 = 2.400 chamadas por idioma
Total (ES + PT): 4.800 chamadas
```

### Controle de custos

- Log de tokens (input + output) por chamada
- Acumulador de custo por modelo, atualizado a cada requisição
- Limite máximo configurável por API — se atingido, o pipeline pausa e alerta
- Relatório de custos ao final de cada execução

### Saída

- `results/qa/{lang}/{model}/{strategy}/run_{n}/responses.json`
- `results/qa/{lang}/{model}/{strategy}/run_{n}/token_usage.json`
- `results/qa/cost_report.json`

### Configuração

```python
CONFIG = {
    "test_set_path": "results/embedding/split_{lang}.json",
    "top5_neighbors_path": "results/embedding/top5_neighbors_{lang}.json",
    "question_table_path": "configs/question_table/qt_mass_calc.json",
    "prompt_dir": "configs/prompts/",
    "output_dir": "results/qa/",
    "lang": "es",
    "models": ["gpt-4o", "gemini-2.0-flash", "llama-3.3-70b", "deepseek-v3"],
    "strategies": ["zero_shot_cot", "few_shot"],
    "temperature": 0,
    "num_repetitions": 3,
    "cost_limits": {
        "gpt-4o": 50.00,
        "gemini-2.0-flash": 50.00,
        "llama-3.3-70b": 50.00,
        "deepseek-v3": 50.00,
    },
}
```

---

## Seção 5: Etapa 4 — Pós-processamento das Respostas

**Objetivo:** Converter as respostas brutas dos LLMs em formato JSON padronizado e confiável.

### Pipeline de pós-processamento

**1. Extração do JSON da resposta**
- Descartar texto fora do bloco JSON/tabela
- Se não houver JSON válido, extrair via regex os pares pergunta/resposta

**2. Normalização de respostas booleanas (Q1–Q11)**
- "Sim", "Sí", "Yes", "True", "1" → `true`
- "Não", "No", "False", "0" → `false`
- Branco, "não informado", "no informado", "N/A", null → `false` (resposta padrão)

**3. Conversão de tamanho para milímetros (Q12 — mass_size_mm)**
- Regex para extrair valor numérico e unidade:
  - Padrões: "15 mm", "1.5 cm", "15mm", "1,5 cm", "15 milímetros"
  - Regex: `(\d+[.,]?\d*)\s*(mm|cm|milímetros|milimetros|centímetros|centimetros)`
- Conversão: cm → mm (×10), mm → mm
- Se não extrair → `null`

**4. Mapeamento de localização por palavras-chave (Q13 — nodule_location)**
- Regex + dicionário bilíngue:

| Palavras-chave (ES) | Palavras-chave (PT) | Categoria |
|---|---|---|
| "cuadrante superior externo", "CSE" | "quadrante superior externo", "QSE" | QSE |
| "cuadrante superior interno", "CSI" | "quadrante superior interno", "QSI" | QSI |
| "cuadrante inferior externo", "CIE" | "quadrante inferior externo", "QIE" | QIE |
| "cuadrante inferior interno", "CII" | "quadrante inferior interno", "QII" | QII |
| "retroareolar", "región central" | "retroareolar", "região central" | Retroareolar |
| "prolongación axilar", "axilar" | "prolongamento axilar", "axilar" | Axilar |
| "mama derecha" | "mama direita" | Mama Direita |
| "mama izquierda" | "mama esquerda" | Mama Esquerda |

- Combinação lateralidade + quadrante quando disponível
- Localização não clara → "Outros"

**5. Validação estrutural**
- JSON contém todas as 13 perguntas
- Tipos de dados corretos (boolean, number, categorical)
- Campos ausentes → valor padrão

### Saída

- `results/postprocessing/{lang}/{model}/{strategy}/run_{n}/structured_responses.json`
- `results/postprocessing/{lang}/{model}/{strategy}/run_{n}/parsing_errors.json`

### Configuração

```python
CONFIG = {
    "input_dir": "results/qa/",
    "output_dir": "results/postprocessing/",
    "question_table_path": "configs/question_table/qt_mass_calc.json",
    "location_keywords_path": "configs/lexicon/birads_lexicon_{lang}.json",
    "default_boolean": false,
    "default_location": "Outros",
    "default_size": null,
    "lang": "es",
}
```

---

## Seção 6: Etapa 5 — Cálculo de Consistência (Cp/Cn) e Significância Estatística

**Objetivo:** Avaliar a estabilidade das respostas dos LLMs comparando as 3 repetições de cada query.

### Métricas

**Percentual de Consistência:**
```
Cp = (nc / nt) × 100
```
Onde `nc` = respostas consistentes (iguais nas 3 repetições), `nt` = total de perguntas no dataset.

**Percentual de Inconsistência:**
```
Cn = (nic / nt) × 100
```
Onde `nic` = respostas inconsistentes.

### Granularidade da análise

**1. Consistência por pergunta por modelo:**

| LLM | Prompt | Q1 | Q2 | ... | Q13 | Avg Consistency |
|---|---|---|---|---|---|---|
| GPT-4o | Zero-shot CoT | % | % | ... | % | % |
| GPT-4o | Few-shot | % | % | ... | % | % |
| ... | ... | ... | ... | ... | ... | ... |

**2. Comparativa Zero-shot CoT vs Few-shot:**
- Consistência média de cada modelo entre as duas estratégias
- Verificar se few-shot resulta em consistência >96% (como no paper)

**3. Comparativa ES vs PT:**
- Consistência entre os dois pipelines de idioma

**4. Tipos de inconsistência:**
- Variações observadas (e.g., run_1=true, run_2=false, run_3=true)
- Inconsistência total (3 diferentes) vs parcial (2 iguais + 1 diferente)

### Testes estatísticos sobre consistência

- **Teste de Friedman:** diferença significativa na consistência entre os 4 modelos?
- **Teste post-hoc de Nemenyi:** quais pares diferem (se Friedman p < 0.05)?
- Aplicado por estratégia e por idioma

### Decisão para etapas seguintes

- Resultados de consistência determinam qual estratégia usar na classificação final
- **Resposta majoritária** (voting das 3 repetições) como resposta final

### Saída

- `results/consistency/{lang}/consistency_table.json`
- `results/consistency/{lang}/consistency_comparison.json`
- `results/consistency/{lang}/inconsistency_details.json`
- `results/consistency/{lang}/friedman_test.json`
- `results/consistency/{lang}/nemenyi_posthoc.json`
- `results/consistency/cross_lang_comparison.json`

### Configuração

```python
CONFIG = {
    "input_dir": "results/postprocessing/",
    "output_dir": "results/consistency/",
    "num_repetitions": 3,
    "voting_strategy": "majority",
    "langs": ["es", "pt"],
    "models": ["gpt-4o", "gemini-2.0-flash", "llama-3.3-70b", "deepseek-v3"],
    "strategies": ["zero_shot_cot", "few_shot"],
    "significance_level": 0.05,
}
```

---

## Seção 7: Etapa 6 — Avaliação da Extração QA (P/R/F1 por pergunta)

**Objetivo:** Avaliar a eficácia de cada LLM em extrair as 13 características clínicas, comparando com ground truth anotado.

**Pré-requisito:** Fluxo com ground truth por pergunta. Sem GT → pula para Seção 8.

### Métricas por pergunta

Para cada combinação (modelo × estratégia × idioma):

```
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1        = 2 × Precision × Recall / (Precision + Recall)
```

**TP/FP/FN por tipo:**

| Tipo | TP | FP | FN |
|---|---|---|---|
| Boolean (Q1–Q11) | Predito=True, GT=True | Predito=True, GT=False | Predito=False, GT=True |
| Numérica (Q12) | Valor dentro da tolerância | Valor fora da tolerância | GT tem valor, modelo não extraiu |
| Categórica (Q13) | Localização == GT | Localização != GT | GT tem localização, modelo respondeu "Outros" |

### Tabelas de resultado

**Eficácia com Zero-shot CoT** e **Eficácia com Few-shot (5 exemplos)** — análogas às Tables III e IV do paper.

### Análises adicionais

1. **Comparativo Zero-shot vs Few-shot por modelo**
2. **Análise de erros por modelo** — padrões de confusão recorrentes
3. **Comparativo ES vs PT**
4. **Testes estatísticos:** Friedman + Nemenyi sobre F1

### Saída

- `results/qa_evaluation/{lang}/zero_shot_cot_metrics.json`
- `results/qa_evaluation/{lang}/few_shot_metrics.json`
- `results/qa_evaluation/{lang}/error_analysis.json`
- `results/qa_evaluation/{lang}/cross_strategy_comparison.json`
- `results/qa_evaluation/{lang}/friedman_test.json`
- `results/qa_evaluation/{lang}/nemenyi_posthoc.json`
- `results/qa_evaluation/cross_lang_comparison.json`

### Configuração

```python
CONFIG = {
    "input_dir": "results/postprocessing/",
    "ground_truth_path": "data/ground_truth_{lang}.csv",
    "output_dir": "results/qa_evaluation/",
    "question_table_path": "configs/question_table/qt_mass_calc.json",
    "size_tolerance_mm": 2.0,
    "voting_strategy": "majority",
    "langs": ["es", "pt"],
    "models": ["gpt-4o", "gemini-2.0-flash", "llama-3.3-70b", "deepseek-v3"],
    "strategies": ["zero_shot_cot", "few_shot"],
    "significance_level": 0.05,
}
```

---

## Seção 8: Etapa 7 — Classificação BI-RADS (Três Motores de Decisão)

**Princípio:** LLM lê → Motor decide

**Objetivo:** Implementar três motores de decisão distintos para classificação BI-RADS, permitindo comparar abordagens.

### Motor 1: Rule-based (Diretrizes BI-RADS)

**Abordagem:** Implementação direta das diretrizes ACR BI-RADS (5ª edição) como regras lógicas determinísticas.

- 100% determinístico
- Sem necessidade de dados de treino
- Interpretável por qualquer radiologista

**Lógica de decisão:**

```
Se has_mass == true:
  Se mass_margin_spiculated == true:
    → BI-RADS 5
  Se mass_shape_irregular == true AND mass_size_mm > threshold:
    → BI-RADS 4
  Se mass_shape_irregular == false AND mass_margin_spiculated == false:
    → BI-RADS 3 ou 2 (conforme tamanho e demais features)

Se has_calcifications == true:
  Se calc_morph_fine_linear_branching == true:
    Se calc_dist_segmental == true OR calc_dist_linear == true:
      → BI-RADS 5
    Se calc_dist_grouped == true:
      → BI-RADS 4C
  Se calc_morph_fine_pleomorphic == true:
    → BI-RADS 4B ou 4C (conforme distribuição)
  Se calc_morph_typically_benign == true:
    → BI-RADS 2

Combinações massa + calcificação:
  → Característica mais suspeita domina
```

Regras documentadas em `configs/classification/birads_rules.json` consultando estritamente o atlas BI-RADS 5ª edição.

**Saída:** Categoria BI-RADS (sem probabilidades)

### Motor 2: Árvore de Decisão (Data-driven)

**Abordagem:** Construção automática de regras a partir dos dados rotulados.

- Aprende padrões diretamente dos dados (`birads_label`)
- Captura relações que o rule-based pode não cobrir
- Fornece feature importance

**Implementação:**
- Decision Tree Classifier (scikit-learn), critério Gini ou Entropy
- Input: vetor de 13 features (booleans como 0/1, numérico normalizado, categórico one-hot encoded)
- Treino: split de 70%, com validação cruzada estratificada
- Hiperparâmetros: `max_depth`, `min_samples_leaf`, `class_weight`

**Saída:** Categoria BI-RADS + P(BI-RADS = k) por classe

### Motor 3: Rede Bayesiana (Probabilístico)

**Abordagem:** Relações causais/probabilísticas entre achados e malignidade.

- Explícita, probabilística, baseada em conhecimento
- Funciona com poucos dados (priors)
- Transparente

**Estrutura do grafo:**

```
has_calcifications ──→ calc_morphology ──→ calc_suspicion_level
                       calc_distribution ──↗

has_mass ──→ mass_margin ──→ mass_suspicion_level
             mass_shape  ──↗
             mass_size   ──↗

calc_suspicion_level ──→ overall_suspicion ──→ P(malignidade) ──→ BI-RADS
mass_suspicion_level ──↗

nodule_location ──→ (fator contextual)
```

**Parametrização:**
1. Knowledge-driven (prior): CPTs do ACR BI-RADS e VPPs publicados
2. Data-driven (update): Ajuste com dados do dataset

**Biblioteca:** `pgmpy`

**Saída:** Categoria BI-RADS + P(BI-RADS = k) + P(malignidade)

### Comparação dos três motores

| Aspecto | Rule-based | Árvore de Decisão | Rede Bayesiana |
|---|---|---|---|
| Fonte do conhecimento | ACR BI-RADS manual | Dados rotulados | ACR BI-RADS + dados |
| Necessita treino | Não | Sim | Parcial (CPTs) |
| Probabilidades | Não | Sim (por folha) | Sim (completa) |
| Interpretabilidade | Total | Alta | Alta |
| Sensibilidade a dados escassos | Imune | Vulnerável | Resistente (priors) |
| Captura padrões ocultos | Não | Sim | Sim |

### Saída completa

- `results/classification/{lang}/{model}/{strategy}/{engine}/predicted_birads.json`
- `configs/classification/birads_rules.json`
- `configs/classification/decision_tree_params.json`
- `configs/classification/bayesian_network.json`

### Configuração

```python
CONFIG = {
    "input_dir": "results/postprocessing/",
    "output_dir": "results/classification/",
    "rules_path": "configs/classification/birads_rules.json",
    "bayesian_network_path": "configs/classification/bayesian_network.json",
    "decision_tree_params_path": "configs/classification/decision_tree_params.json",
    "question_table_path": "configs/question_table/qt_mass_calc.json",
    "voting_strategy": "majority",
    "engine": "rule_based",  # "rule_based" | "decision_tree" | "bayesian_network"
    "lang": "es",
    "model": "gpt-4o",
    "strategy": "few_shot",
}
```

---

## Seção 9: Etapa 8 — Avaliação Final e Análise de Resultados

**Objetivo:** Avaliar a classificação BI-RADS em todas as dimensões (LLMs × estratégias × motores × idiomas), produzir visualizações, testes estatísticos e análise interpretativa.

### 9.1 Dois fluxos de avaliação

| Fluxo | GT por pergunta | GT BI-RADS | Avalia |
|---|---|---|---|
| Com GT por pergunta | Disponível | `birads_label` | Pipeline completo |
| Sem GT por pergunta | Não disponível | `birads_label` | Classificação end-to-end |

### 9.2 Métricas por categoria BI-RADS

Para cada combinação (modelo × estratégia × motor × idioma):

| BI-RADS | DeepSeek-V3 | Gemini 2.0 Flash | GPT-4o | Llama 3.3 70B | Nº Ex. |
|---|---|---|---|---|---|
| | P / R / F1 | P / R / F1 | P / R / F1 | P / R / F1 | |
| 0–6 | | | | | |
| **weighted avg** | | | | | |

- Weighted F1 (métrica principal)
- Macro F1 (categorias minoritárias)
- Matriz de confusão
- Accuracy global

### 9.3 Testes estatísticos

**Sobre LLMs:**
- Friedman + Nemenyi sobre F1 ponderado, por estratégia, motor e idioma

**Sobre motores:**
- Friedman + Nemenyi sobre F1 entre os 3 motores, por modelo, estratégia e idioma

### 9.4 Visualizações

**Do paper (Figure 2):**

| Gráfico | Descrição |
|---|---|
| Bar chart F1 (Fig. 2a) | F1 médio por modelo, agrupado por estratégia |
| Boxplot F1 (Fig. 2b) | Distribuição de F1 entre categorias por modelo |
| Heatmap F1 (Fig. 2c) | Modelo × categoria BI-RADS |
| Eficácia por pergunta (Fig. 2d) | F1 por pergunta por modelo (fluxo com GT) |

**Adicionais:**

| Gráfico | Descrição |
|---|---|
| Comparativo motores | F1 dos 3 motores lado a lado |
| Heatmap ES vs PT | Diferença de F1 entre idiomas |
| Matrizes de confusão | Por modelo/estratégia/motor |
| Consistência vs eficácia | Scatter plot Cp vs F1 |

### 9.5 Análise comparativa multi-dimensional

**Por LLM:** melhor modelo, categorias problemáticas, padrões de erro

**Por estratégia:** ganho do few-shot, custo-benefício

**Por motor:** rule-based vs árvore vs bayesiana, padrões capturados, convergência de feature importance vs VPPs

**Por idioma:** degradação pela tradução, categorias afetadas

**Análise de erros:** confusões frequentes, features incorretas que causaram erros, relação com erros de extração QA

### 9.6 Síntese e recomendações

- Melhor combinação: LLM + estratégia + motor + idioma
- Trade-off custo vs desempenho
- Limitações identificadas
- Propostas de melhoria para iterações futuras

### Saída

- `results/evaluation/{lang}/birads_metrics_{strategy}_{engine}.json`
- `results/evaluation/{lang}/confusion_matrices_{engine}.json`
- `results/evaluation/{lang}/friedman_test_{engine}.json`
- `results/evaluation/{lang}/nemenyi_posthoc_{engine}.json`
- `results/evaluation/{lang}/error_analysis_{engine}.json`
- `results/evaluation/cross_lang_comparison.json`
- `results/evaluation/cross_engine_comparison.json`
- `results/evaluation/synthesis.json`
- `results/figures/` — gráficos em PNG e PDF

### Configuração

```python
CONFIG = {
    "input_dir": "results/classification/",
    "ground_truth_path": "data/reports_filtered_{lang}.csv",
    "qa_ground_truth_path": "data/ground_truth_{lang}.csv",
    "output_dir": "results/evaluation/",
    "figures_dir": "results/figures/",
    "langs": ["es", "pt"],
    "models": ["gpt-4o", "gemini-2.0-flash", "llama-3.3-70b", "deepseek-v3"],
    "strategies": ["zero_shot_cot", "few_shot"],
    "engines": ["rule_based", "decision_tree", "bayesian_network"],
    "significance_level": 0.05,
    "birads_categories": [0, 1, 2, 3, 4, 5, 6],
    "figure_formats": ["png", "pdf"],
    "has_qa_ground_truth": true,
}
```
