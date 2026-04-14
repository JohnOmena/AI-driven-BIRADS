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
