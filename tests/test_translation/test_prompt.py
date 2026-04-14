"""Tests for translation and audit prompt construction."""

from src.translation.prompt import build_translation_prompt, build_audit_prompt


# --- Translation prompt tests ---

def test_prompt_contains_report_text():
    """The prompt must include the original report text."""
    report = "Se observa un nodulo espiculado en mama derecha."
    glossary_text = "mama derecha -> mama direita"
    prompt = build_translation_prompt(report, glossary_text)
    assert "Se observa un nodulo espiculado en mama derecha." in prompt


def test_prompt_contains_glossary():
    """The prompt must include the glossary."""
    report = "Texto de ejemplo."
    glossary_text = "mama derecha -> mama direita\ncalcificacion -> calcificacao"
    prompt = build_translation_prompt(report, glossary_text)
    assert "mama derecha -> mama direita" in prompt
    assert "calcificacion -> calcificacao" in prompt


def test_prompt_contains_fidelity_instructions():
    """The prompt must contain explicit fidelity instructions."""
    report = "Texto."
    glossary_text = ""
    prompt = build_translation_prompt(report, glossary_text)
    prompt_lower = prompt.lower()
    assert "fiel" in prompt_lower
    assert "omitir" in prompt_lower


def test_prompt_instructs_birads_preservation():
    """The prompt must instruct to preserve BI-RADS terminology."""
    report = "Texto."
    glossary_text = ""
    prompt = build_translation_prompt(report, glossary_text)
    assert "BI-RADS" in prompt


def test_prompt_instructs_laterality_preservation():
    """The prompt must instruct to preserve laterality."""
    report = "Texto."
    glossary_text = ""
    prompt = build_translation_prompt(report, glossary_text)
    prompt_lower = prompt.lower()
    assert "lateralidade" in prompt_lower or "lateralidad" in prompt_lower


def test_prompt_instructs_measurement_preservation():
    """The prompt must instruct to preserve measurements and units."""
    report = "Texto."
    glossary_text = ""
    prompt = build_translation_prompt(report, glossary_text)
    prompt_lower = prompt.lower()
    assert "medida" in prompt_lower or "unidade" in prompt_lower


# --- Audit prompt tests ---

def test_audit_prompt_contains_both_texts():
    """The audit prompt must include both original and translated text."""
    original = "Se observa un nodulo en mama derecha."
    translated = "Observa-se um nodulo na mama direita."
    glossary_text = ""
    prompt = build_audit_prompt(original, translated, glossary_text)
    assert original in prompt
    assert translated in prompt


def test_audit_prompt_contains_criteria():
    """The audit prompt must include fidelity, lexicon, and number checks."""
    original = "Texto."
    translated = "Texto."
    glossary_text = ""
    prompt = build_audit_prompt(original, translated, glossary_text)
    prompt_lower = prompt.lower()
    assert "fidelidade" in prompt_lower
    assert "lexico" in prompt_lower or "bi-rads" in prompt_lower.replace("-", "")
    assert "numero" in prompt_lower or "medida" in prompt_lower


def test_audit_prompt_requests_json():
    """The audit prompt must request JSON output with aprovado/score/inconsistencias."""
    original = "Texto."
    translated = "Texto."
    glossary_text = ""
    prompt = build_audit_prompt(original, translated, glossary_text)
    assert "aprovado" in prompt
    assert "score" in prompt
    assert "inconsistencias" in prompt
