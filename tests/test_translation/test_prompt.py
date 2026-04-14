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


def test_audit_prompt_contains_all_criteria():
    """The audit prompt must include all 7 criteria."""
    original = "Texto."
    translated = "Texto."
    glossary_text = ""
    prompt = build_audit_prompt(original, translated, glossary_text)
    prompt_lower = prompt.lower()
    # C1: BI-RADS descriptors
    assert "descritores" in prompt_lower
    assert "forma" in prompt_lower and "margem" in prompt_lower
    # C2: BI-RADS category
    assert "categoria" in prompt_lower
    # C3: Measures and numbers
    assert "medida" in prompt_lower or "numerico" in prompt_lower
    # C4: Laterality
    assert "lateralidade" in prompt_lower
    # C5: Omissions and additions
    assert "omiss" in prompt_lower
    # C6: Sense inversion and negation errors
    assert "negacao" in prompt_lower or "negacao" in prompt_lower
    assert "invers" in prompt_lower
    # C7: Temporal comparisons
    assert "temporal" in prompt_lower or "anteriores" in prompt_lower


def test_audit_prompt_requests_structured_json():
    """The audit prompt must request per-criterion JSON with aprovado/score/criterios."""
    original = "Texto."
    translated = "Texto."
    glossary_text = ""
    prompt = build_audit_prompt(original, translated, glossary_text)
    assert "aprovado" in prompt
    assert "score" in prompt
    assert "inconsistencias" in prompt
    assert "criterios" in prompt
    assert "C1_descritores_birads" in prompt
    assert "C6_inversoes_negacao" in prompt
