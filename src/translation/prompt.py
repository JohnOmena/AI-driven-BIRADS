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
    and returns a structured assessment.

    Args:
        original_text: The original Spanish mammography report.
        translated_text: The Portuguese translation to audit.
        glossary_text: Formatted glossary of BI-RADS terms ES->PT.

    Returns:
        Complete prompt string for the auditor LLM.
    """
    prompt = f"""Voce e um auditor medico especializado em radiologia mamaria e no sistema BI-RADS.

Sua tarefa e avaliar a qualidade de uma traducao de laudo de mamografia do espanhol para o portugues do Brasil.

Compare o TEXTO ORIGINAL com a TRADUCAO e verifique TODOS os criterios abaixo:

CRITERIOS DE AUDITORIA:

1. FIDELIDADE SEMANTICA: A traducao preserva fielmente o significado completo do original? Ha omissoes, adicoes, distorcoes ou interpretacoes indevidas?

2. LEXICO BI-RADS: Os termos padronizados BI-RADS foram traduzidos corretamente para o portugues conforme o glossario? Os descritores (forma, margem, morfologia, distribuicao, densidade) estao corretos?

3. CATEGORIA BI-RADS: A classificacao BI-RADS (0, 1, 2, 3, 4A, 4B, 4C, 5, 6) foi mantida intacta?

4. NUMEROS E MEDIDAS: Todos os valores numericos, unidades de medida, dimensoes e quantidades foram preservados exatamente?

5. LATERALIDADE E LOCALIZACAO: A lateralidade e a localizacao anatomica estao corretas na traducao?

6. COMPARACOES TEMPORAIS: Referencias a exames anteriores e evolucao temporal foram mantidas?

7. ACHADOS ASSOCIADOS: Todos os achados descritos no original estao presentes na traducao?

{glossary_text}

TEXTO ORIGINAL (Espanhol):
{original_text}

TRADUCAO (Portugues do Brasil):
{translated_text}

RESULTADO DA AUDITORIA:
Responda EXATAMENTE no formato JSON abaixo, sem texto adicional antes ou depois:

{{
  "aprovado": true ou false,
  "score": 0 a 10 (nota geral da traducao),
  "inconsistencias": [
    {{
      "criterio": "nome do criterio violado",
      "original": "trecho do texto original",
      "traducao": "trecho da traducao com problema",
      "problema": "descricao do problema encontrado"
    }}
  ]
}}

Se a traducao estiver perfeita, retorne {{"aprovado": true, "score": 10, "inconsistencias": []}}"""
    return prompt
