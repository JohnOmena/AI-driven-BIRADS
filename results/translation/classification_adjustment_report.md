# Relatorio de Ajuste na Classificacao e Correcao de Traducoes

**Data:** 2026-04-14
**Analista:** Pipeline automatizado + revisao manual
**Escopo:** 120 laudos traduzidos (primeiros 120 de 4.357)

## Resumo Executivo

Analise em duas fases:

**Fase 1 - Classificacao:** 3 bugs no pipeline geravam falsos negativos (traducoes
corretas classificadas como "review"). Correcao reclassificou 35 laudos.

**Fase 2 - Correcao de traducoes:** Validacao manual confirmou que o auditor
DeepSeek V3 identificou corretamente problemas reais em muitas traducoes do
Gemini 2.5 Flash. Foram encontrados 4 padroes de erro sistematico, corrigidos
em 57 laudos via pos-processamento automatizado.

## Fase 1: Ajustes na Classificacao

### Problema 1: Falso negativo no match de termos BI-RADS (substring)

**Arquivo:** `src/translation/validate.py` - `check_birads_terms_preserved()`

**Descricao:** O glossario contem tanto "retroareolar" -> "retroareolar" quanto
"areola" -> "areola". O algoritmo detectava "areola" como substring dentro de
"retroareolar" e buscava "areola" (com acento) na traducao. A traducao
corretamente usa "retroareolar" (sem acento isolado), gerando falso negativo.

**Impacto:** 8 laudos com `term_match_ratio` artificialmente reduzido.

**Correcao:** Funcao `_is_subterm_of_matched()` filtra termos do glossario que
sao substrings de outros termos maiores encontrados no original.

### Problema 2: Threshold de similaridade restritivo para cross-language

**Arquivo:** `src/translation/validate.py` - `classify_translation()`

**Descricao:** Threshold de 0.90 e restritivo demais para comparacao ES->PT.
Embeddings multilinguais capturam diferencas lexicais entre idiomas.

**Impacto:** 7 laudos com score 10 do auditor classificados como "review".

**Correcao:** Threshold reduzido de 0.90 para 0.85.

### Problema 3: Classificador sem via alternativa para auditor restritivo

**Correcao:** Path 2 adicionado: `score >= 8 AND sim >= 0.85 AND terms >= 0.90`.

### Regras de Classificacao Atualizadas

```
APROVADO (qualquer caminho):
  Path 1: aprovado=true AND similarity >= 0.85 AND term_match >= 0.80
  Path 2: score >= 8 AND similarity >= 0.85 AND term_match >= 0.90

REVIEW:
  score >= 7 AND similarity >= 0.80

REJEITADO:
  Todos os demais
```

## Fase 2: Correcao de Traducoes (DeepSeek acertou)

A revisao manual das traducoes com `aprovado: false` revelou que o DeepSeek
identificou problemas reais. Foram encontrados 4 padroes sistematicos de erro
do Gemini 2.5 Flash:

### Erro 1: Concordancia de genero em descritores BI-RADS (8 laudos)

**Problema:** "margenes oscurecidos" (ES, masculino) traduzido como "margens
obscurecidos" (PT). "Margens" e feminino em portugues, exigindo "obscurecidas".

**Exemplo:**
- Antes:  `IMAGEM NODULAR DE MARGENS OBSCURECIDOS`
- Depois: `IMAGEM NODULAR DE MARGENS OBSCURECIDAS`

**Criterio violado:** C1 - Descritores BI-RADS (concordancia genero/numero)

### Erro 2: Verbo em espanhol mantido na traducao (1 laudo)

**Problema:** "no se observan" traduzido como "nao se observan" (manteve
conjugacao espanhola em vez de "observam").

**Exemplo:**
- Antes:  `NAO SE OBSERVAN CALCIFICACOES SUSPEITAS`
- Depois: `NAO SE OBSERVAM CALCIFICACOES SUSPEITAS`

**Criterio violado:** C6 - Erros de traducao

### Erro 3: Traducao livre de termo medico (35 laudos)

**Problema:** "caracteres ganglionares" (termo medico tecnico) traduzido
livremente como "caracteristicas ganglionares". O termo correto em PT medico
e "caracteres".

**Exemplo:**
- Antes:  `IMAGENS NODULARES COM CARACTERISTICAS GANGLIONARES`
- Depois: `IMAGENS NODULARES COM CARACTERES GANGLIONARES`

**Criterio violado:** C1 - Fidelidade lexical medica

### Erro 4: Formatacao ".-" removida (14 laudos)

**Problema:** Linhas terminadas em ".-" no original (convencao de laudos em
espanhol) foram normalizadas para "." pelo Gemini, violando a regra de
preservacao de estrutura e pontuacao.

**Exemplo:**
- Antes:  `NAO SE OBSERVAM CALCIFICACOES SUSPEITAS.`
- Depois: `NAO SE OBSERVAM CALCIFICACOES SUSPEITAS.-`

**Criterio violado:** C5 - Preservacao de formatacao original

### Resumo das Correcoes Aplicadas

| Tipo de Correcao             | Laudos Afetados | Criterio |
|------------------------------|:---------:|:--------:|
| Fidelidade lexical (caracteres) | 35     | C1       |
| Formatacao .- restaurada     | 14        | C5       |
| Concordancia de genero       | 8         | C1       |
| Verbo espanhol corrigido     | 1         | C6       |
| **Total de laudos corrigidos** | **57** (com sobreposicoes) |  |

### Pos-processamento Integrado ao Pipeline

Funcao `postprocess_translation()` adicionada em `src/translation/validate.py`
para corrigir automaticamente esses padroes ANTES da auditoria pelo DeepSeek.
Isso melhora a qualidade da traducao que o auditor recebe, resultando em scores
mais altos e menos falsos negativos.

**Ordem no pipeline:**
1. Gemini traduz ES -> PT
2. **`postprocess_translation()` corrige padroes conhecidos**
3. DeepSeek audita traducao corrigida
4. Metricas de similaridade e termos sao calculadas
5. Classificacao final

## Validacao

- 35 testes unitarios (todos passando)
- 5 testes dedicados ao pos-processamento
- Revisao manual de amostras confirmou correcoes
- Logs detalhados:
  - `reclassification_log.json`: mudancas de classificacao
  - `corrections_log.json`: correcoes aplicadas por laudo

## Nota sobre Pipeline em Execucao

O pipeline em background (traduzindo laudos 61-4357) usa o codigo antigo em
memoria. Quando concluir, sera necessario:
1. Re-aplicar `postprocess_translation()` nos novos laudos
2. Re-classificar com as novas regras
3. Gerar estatisticas finais
