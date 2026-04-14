"""Tests for translation validation (audit parsing + BI-RADS lexicon check)."""

from src.translation.validate import (
    check_birads_terms_preserved,
    parse_audit_response,
    classify_translation,
)


# --- BI-RADS term preservation tests ---

def test_birads_terms_preserved_all_found():
    """All expected PT terms present in translation."""
    pairs = [("mama derecha", "mama direita"), ("nodulo", "nodulo"), ("calcificacion", "calcificacao")]
    original = "Se observa un nodulo en mama derecha con calcificacion."
    translated = "Observa-se um nodulo na mama direita com calcificacao."
    result = check_birads_terms_preserved(original, translated, pairs)
    assert result["match_ratio"] == 1.0
    assert len(result["missing_terms"]) == 0


def test_birads_terms_preserved_missing():
    """Missing PT term should be flagged."""
    pairs = [("mama derecha", "mama direita"), ("espiculado", "espiculado")]
    original = "Nodulo espiculado en mama derecha."
    translated = "Nodulo na mama direita."  # missing espiculado
    result = check_birads_terms_preserved(original, translated, pairs)
    assert result["match_ratio"] < 1.0
    assert len(result["missing_terms"]) > 0
    assert any(t["es"] == "espiculado" for t in result["missing_terms"])


def test_birads_terms_no_terms_in_original():
    """No glossary terms in original = 1.0 match ratio."""
    pairs = [("mama derecha", "mama direita")]
    original = "Examen normal."
    translated = "Exame normal."
    result = check_birads_terms_preserved(original, translated, pairs)
    assert result["match_ratio"] == 1.0
    assert result["total_expected"] == 0


# --- Audit response parsing tests ---

def test_parse_audit_response_valid_json():
    """Parse valid JSON audit response with per-criterion data."""
    response = '{"aprovado": true, "score": 10, "criterios": {"C1_descritores_birads": {"ok": true}, "C2_categoria_birads": {"ok": true}}, "inconsistencias": []}'
    result = parse_audit_response(response)
    assert result["aprovado"] is True
    assert result["score"] == 10
    assert result["inconsistencias"] == []
    assert result["criterios"]["C1_descritores_birads"]["ok"] is True


def test_parse_audit_response_markdown_block():
    """Parse JSON wrapped in markdown code block."""
    response = '```json\n{"aprovado": false, "score": 6, "inconsistencias": [{"criterio": "lexico", "problema": "termo incorreto"}]}\n```'
    result = parse_audit_response(response)
    assert result["aprovado"] is False
    assert result["score"] == 6
    assert len(result["inconsistencias"]) == 1


def test_parse_audit_response_with_extra_text():
    """Parse JSON when LLM adds extra text before/after."""
    response = 'Aqui esta a avaliacao:\n{"aprovado": true, "score": 10, "inconsistencias": []}\nFim.'
    result = parse_audit_response(response)
    assert result["aprovado"] is True
    assert result["score"] == 10


def test_parse_audit_response_invalid():
    """Invalid response returns failed audit."""
    response = "Nao consigo avaliar este texto."
    result = parse_audit_response(response)
    assert result["aprovado"] is False
    assert result["score"] == 0


# --- Classification tests ---

def test_classify_approved():
    """High audit + high similarity + good terms = approved."""
    audit = {"aprovado": True, "score": 9}
    result = classify_translation(audit, similarity=0.95, term_match_ratio=1.0)
    assert result == "approved"


def test_classify_review():
    """Medium audit score but decent similarity = review."""
    audit = {"aprovado": False, "score": 7}
    result = classify_translation(audit, similarity=0.90, term_match_ratio=0.9)
    assert result == "review"


def test_classify_rejected():
    """Low audit + low similarity = rejected."""
    audit = {"aprovado": False, "score": 3}
    result = classify_translation(audit, similarity=0.70, term_match_ratio=0.5)
    assert result == "rejected"
