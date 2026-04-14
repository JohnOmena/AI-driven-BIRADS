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
