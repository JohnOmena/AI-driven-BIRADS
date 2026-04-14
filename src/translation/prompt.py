"""Build prompts for translation and audit of mammography reports."""


def build_translation_prompt(report_text: str, glossary_text: str) -> str:
    """Build a translation prompt ensuring fidelity and BI-RADS lexicon preservation.

    Args:
        report_text: The original Spanish mammography report.
        glossary_text: Formatted glossary of BI-RADS terms ES->PT.

    Returns:
        Complete prompt string for the translator LLM.
    """
    prompt = f"""Voce e um tradutor medico especializado em radiologia mamaria e no sistema BI-RADS (ACR BI-RADS Atlas, 5a Edicao).

Sua tarefa e traduzir fielmente o seguinte laudo de mamografia do espanhol para o portugues do Brasil.

REGRAS OBRIGATORIAS DE TRADUCAO:

1. FIDELIDADE ABSOLUTA: Traduzir o texto completo de forma fiel, sem omitir, resumir, interpretar, parafrasear ou adicionar informacoes que nao constem no original.

2. LEXICO BI-RADS: Utilizar OBRIGATORIAMENTE a terminologia oficial BI-RADS em portugues conforme o glossario abaixo. Os descritores padronizados (forma, margem, densidade, morfologia, distribuicao) devem ser traduzidos usando exclusivamente os termos BI-RADS do idioma de destino.

3. CATEGORIA BI-RADS: Manter intacta a classificacao BI-RADS (ex: BI-RADS 0, 1, 2, 3, 4A, 4B, 4C, 5, 6). Nao alterar, omitir ou reinterpretar a categoria.

4. LATERALIDADE E LOCALIZACAO: Preservar exatamente a lateralidade (mama direita/esquerda, bilateral) e a localizacao anatomica (quadrante, regiao retroareolar, prolongamento axilar, etc.).

5. MEDIDAS E QUANTIDADES: Manter todos os valores numericos, unidades de medida (mm, cm), quantidades e dimensoes exatamente como no original.

6. COMPARACOES TEMPORAIS: Preservar todas as referencias a exames anteriores, evolucao temporal, estabilidade ou mudanca de achados (ex: "estavel em relacao ao estudo previo", "novo achado").

7. ACHADOS ASSOCIADOS: Manter todos os achados descritos (retração cutanea, espessamento cutaneo, linfadenopatia, etc.) sem omissoes.

8. ESTRUTURA: Preservar exatamente a estrutura, formatacao, paragrafos, secoes e pontuacao do texto original.

9. SIGLAS UNIVERSAIS: Nao traduzir siglas universais (BI-RADS, CSE, CSI, CIE, CII, MLO, CC).

10. SAIDA: Retornar APENAS o texto traduzido, sem explicacoes, comentarios, notas ou prefacios.

{glossary_text}

LAUDO ORIGINAL (Espanhol):
{report_text}

TRADUCAO (Portugues do Brasil):"""
    return prompt


def build_audit_prompt(original_text: str, translated_text: str, glossary_text: str) -> str:
    """Build an audit prompt for the validator LLM to check translation quality.

    The auditor compares the original Spanish text with the Portuguese translation
    and returns a structured per-criterion assessment.

    Args:
        original_text: The original Spanish mammography report.
        translated_text: The Portuguese translation to audit.
        glossary_text: Formatted glossary of BI-RADS terms ES->PT.

    Returns:
        Complete prompt string for the auditor LLM.
    """
    prompt = f"""Voce e um auditor medico especializado em radiologia mamaria e no sistema BI-RADS (ACR BI-RADS Atlas, 5a Edicao).

Sua tarefa e auditar a qualidade de uma traducao de laudo de mamografia do espanhol para o portugues do Brasil.

Compare CUIDADOSAMENTE o TEXTO ORIGINAL com a TRADUCAO e avalie CADA UM dos criterios abaixo de forma independente:

CRITERIOS DE AUDITORIA:

C1. DESCRITORES BI-RADS (PRIORIDADE MAXIMA): Os descritores padronizados BI-RADS foram traduzidos corretamente para o portugues conforme o glossario? Verifique CADA descritor presente no original:
    - Forma: ovalado/a, redondo/a, irregular, lobulado/a
    - Margem: circunscrito/a, obscurecido/a, microlobulado, indistinto, espiculado/a
    - Densidade: isodenso/a, hipodenso, hiperdenso, heterogeneo, homogeneo
    - Morfologia de calcificacoes: puntiforme, amorfo, pleomorfico, lineal fino, ramificado
    - Distribuicao: agrupada, segmentar, linear, regional, difusa, ductal
    Verifique tambem concordancia de genero e numero dos descritores.

C2. CATEGORIA BI-RADS: A classificacao BI-RADS (0, 1, 2, 3, 4A, 4B, 4C, 5, 6) foi mantida exatamente igual? Nao pode haver alteracao, omissao ou reinterpretacao da categoria.

C3. MEDIDAS, NUMEROS E UNIDADES: Todos os valores numericos (tamanho em mm/cm, quantidade de nodulos, distancias) e unidades de medida foram preservados exatamente como no original?

C4. LATERALIDADE E LOCALIZACAO ANATOMICA: A lateralidade (mama direita/esquerda, bilateral) e a localizacao anatomica (quadrante, regiao retroareolar, prolongamento axilar, plano posterior, etc.) estao corretas na traducao? Nao pode haver inversao de lado.

C5. OMISSOES E ADICOES: A traducao contem TODAS as informacoes do original? Ha trechos omitidos? Ha informacoes adicionadas que nao existem no original?

C6. INVERSOES DE SENTIDO E ERROS DE NEGACAO: Ha alguma frase onde o sentido foi invertido na traducao? Verificar especialmente: frases negativas que se tornaram positivas ou vice-versa (ex: "no se observan" traduzido sem negacao), atribuicoes trocadas entre achados, alteracao de relacoes causais ou temporais.

C7. COMPARACOES TEMPORAIS E ACHADOS ASSOCIADOS: Referencias a exames anteriores, evolucao, estabilidade e todos os achados associados (retracao cutanea, espessamento, linfadenopatia, etc.) foram mantidos?

{glossary_text}

TEXTO ORIGINAL (Espanhol):
{original_text}

TRADUCAO (Portugues do Brasil):
{translated_text}

RESULTADO DA AUDITORIA:
Responda EXATAMENTE no formato JSON abaixo, sem texto adicional antes ou depois:

{{
  "aprovado": true ou false,
  "score": 0 a 10,
  "criterios": {{
    "C1_descritores_birads": {{"ok": true/false, "nota": "explicacao se nao ok"}},
    "C2_categoria_birads": {{"ok": true/false, "nota": "explicacao se nao ok"}},
    "C3_medidas_numeros": {{"ok": true/false, "nota": "explicacao se nao ok"}},
    "C4_lateralidade_localizacao": {{"ok": true/false, "nota": "explicacao se nao ok"}},
    "C5_omissoes_adicoes": {{"ok": true/false, "nota": "explicacao se nao ok"}},
    "C6_inversoes_negacao": {{"ok": true/false, "nota": "explicacao se nao ok"}},
    "C7_temporais_achados": {{"ok": true/false, "nota": "explicacao se nao ok"}}
  }},
  "inconsistencias": [
    {{
      "criterio": "C1/C2/C3/C4/C5/C6/C7",
      "original": "trecho exato do texto original",
      "traducao": "trecho exato da traducao com problema",
      "problema": "descricao precisa do problema encontrado"
    }}
  ]
}}

Se a traducao estiver perfeita, retorne:
{{"aprovado": true, "score": 10, "criterios": {{"C1_descritores_birads": {{"ok": true}}, "C2_categoria_birads": {{"ok": true}}, "C3_medidas_numeros": {{"ok": true}}, "C4_lateralidade_localizacao": {{"ok": true}}, "C5_omissoes_adicoes": {{"ok": true}}, "C6_inversoes_negacao": {{"ok": true}}, "C7_temporais_achados": {{"ok": true}}}}, "inconsistencias": []}}"""
    return prompt
