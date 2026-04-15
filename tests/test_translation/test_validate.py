"""Tests for translation validation (audit parsing + BI-RADS lexicon check)."""

from src.translation.validate import (
    check_birads_terms_preserved,
    parse_audit_response,
    classify_translation,
    postprocess_translation,
    validate_audit_findings,
    _is_subterm_of_matched,
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


def test_birads_terms_subterm_not_counted():
    """Subterm 'areola' should not be counted separately when 'retroareolar' is present."""
    pairs = [("retroareolar", "retroareolar"), ("areola", "aréola")]
    original = "Imagen en region retroareolar de mama derecha."
    translated = "Imagem na regiao retroareolar da mama direita."
    result = check_birads_terms_preserved(original, translated, pairs)
    assert result["match_ratio"] == 1.0
    assert result["total_expected"] == 1  # Only retroareolar, not areola


def test_is_subterm_of_matched():
    """Subterm detection works correctly."""
    terms = ["retroareolar", "areola", "mama derecha"]
    assert _is_subterm_of_matched("areola", terms) is True
    assert _is_subterm_of_matched("retroareolar", terms) is False
    assert _is_subterm_of_matched("mama derecha", terms) is False


# --- Post-processing tests ---

def test_postprocess_fixes_gender_agreement():
    """Fix 'margens obscurecidos' -> 'margens obscurecidas'."""
    original = "Imagen nodular de margenes oscurecidos."
    translated = "Imagem nodular de margens obscurecidos."
    fixed, fixes = postprocess_translation(original, translated)
    assert "obscurecidas" in fixed
    assert "obscurecidos" not in fixed
    assert len(fixes) == 1
    assert fixes[0]["tipo"] == "C1_concordancia_genero"


def test_postprocess_fixes_spanish_verb():
    """Fix Spanish verb 'observan' -> Portuguese 'observam'."""
    original = "No se observan calcificaciones sospechosas."
    translated = "Nao se observan calcificacoes suspeitas."
    fixed, fixes = postprocess_translation(original, translated)
    assert "observam" in fixed
    assert any(f["tipo"] == "C6_verbo_espanhol" for f in fixes)


def test_postprocess_fixes_caracteres():
    """Fix 'caracteristicas' -> 'caracteres' when original uses 'caracteres'."""
    original = "Imagenes nodulares con caracteres ganglionares."
    translated = "Imagens nodulares com caracter\u00edsticas ganglionares."
    fixed, fixes = postprocess_translation(original, translated)
    assert "caracteres" in fixed
    assert "caracter\u00edsticas" not in fixed
    assert any(f["tipo"] == "C1_fidelidade_lexical" for f in fixes)


def test_postprocess_preserves_formatting():
    """Restore '.-' line endings from original."""
    original = "Linea uno.-\nLinea dos.-"
    translated = "Linha um.\nLinha dois."
    fixed, fixes = postprocess_translation(original, translated)
    assert fixed == "Linha um.-\nLinha dois.-"
    assert any(f["tipo"] == "C5_formatacao" for f in fixes)


def test_postprocess_no_fix_when_correct():
    """No fixes applied when translation is already correct."""
    original = "Imagenes nodulares con caracteres ganglionares."
    translated = "Imagens nodulares com caracteres ganglionares."
    fixed, fixes = postprocess_translation(original, translated)
    assert fixed == translated
    assert len(fixes) == 0


# --- Audit validation tests (meta-auditing the DeepSeek) ---

def test_validate_rejects_false_positive_laterality():
    """Reject C4 finding when laterality is actually correct."""
    original = "Nodulo en mama derecha."
    translated = "Nodulo na mama direita."
    audit = {
        "aprovado": False,
        "score": 8,
        "inconsistencias": [
            {"criterio": "C4", "problema": "lateralidade incorreta"}
        ],
    }
    result = validate_audit_findings(original, translated, audit, [])
    assert result["verdict"] == "keep"
    assert len(result["rejected"]) == 1
    assert len(result["confirmed"]) == 0


def test_validate_confirms_real_laterality_issue():
    """Confirm C4 finding when laterality is actually wrong."""
    original = "Nodulo en mama derecha."
    translated = "Nodulo na mama esquerda."
    audit = {
        "aprovado": False,
        "score": 5,
        "inconsistencias": [
            {"criterio": "C4", "problema": "lateralidade invertida"}
        ],
    }
    result = validate_audit_findings(original, translated, audit, [])
    assert result["verdict"] == "correct"
    assert len(result["confirmed"]) == 1


def test_validate_rejects_false_positive_birads_category():
    """Reject C2 finding when BI-RADS category is actually preserved."""
    original = "BI-RADS 3."
    translated = "BI-RADS 3."
    audit = {
        "aprovado": False,
        "score": 8,
        "inconsistencias": [
            {"criterio": "C2", "problema": "categoria alterada"}
        ],
    }
    result = validate_audit_findings(original, translated, audit, [])
    assert result["verdict"] == "keep"
    assert len(result["rejected"]) == 1


def test_validate_confirms_real_number_issue():
    """Confirm C3 finding when measurements are actually different."""
    original = "Nodulo de 14 mm."
    translated = "Nodulo de 41 mm."
    audit = {
        "aprovado": False,
        "score": 5,
        "inconsistencias": [
            {"criterio": "C3", "problema": "medida alterada", "original": "14 mm", "traducao": "41 mm"}
        ],
    }
    result = validate_audit_findings(original, translated, audit, [])
    assert result["verdict"] == "correct"
    assert len(result["confirmed"]) == 1


def test_validate_rejects_false_positive_negation():
    """Reject C6 finding when negation count matches."""
    original = "No se observan calcificaciones. No se observan masas."
    translated = "Nao se observam calcificacoes. Nao se observam massas."
    audit = {
        "aprovado": False,
        "score": 8,
        "inconsistencias": [
            {"criterio": "C6", "problema": "negacao removida"}
        ],
    }
    result = validate_audit_findings(original, translated, audit, [])
    assert result["verdict"] == "keep"
    assert len(result["rejected"]) == 1


def test_validate_mixed_confirmed_and_rejected():
    """Mixed findings: some confirmed, some rejected."""
    original = "Nodulo de 14 mm en mama derecha. BI-RADS 4A."
    translated = "Nodulo de 14 mm na mama direita. BI-RADS 4A."
    audit = {
        "aprovado": False,
        "score": 7,
        "inconsistencias": [
            {"criterio": "C4", "problema": "lateralidade invertida"},  # FALSE: direita is correct
            {"criterio": "C7", "problema": "referencia temporal omitida"},  # TRUSTED: C7
        ],
    }
    result = validate_audit_findings(original, translated, audit, [])
    assert result["verdict"] == "correct"  # C7 confirmed
    assert len(result["confirmed"]) == 1
    assert len(result["rejected"]) == 1
    assert result["rejected"][0]["criterio"] == "C4"


def test_validate_empty_inconsistencies():
    """No inconsistencies = keep translation."""
    audit = {"aprovado": True, "score": 10, "inconsistencias": []}
    result = validate_audit_findings("", "", audit, [])
    assert result["verdict"] == "keep"
    assert len(result["confirmed"]) == 0


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

def test_classify_approved_auditor_approved():
    """Auditor approved + good similarity + good terms = approved (path 1)."""
    audit = {"aprovado": True, "score": 9}
    result = classify_translation(audit, similarity=0.90, term_match_ratio=1.0)
    assert result == "approved"


def test_classify_approved_cross_language_similarity():
    """Auditor approved with cross-language similarity >= 0.85 = approved."""
    audit = {"aprovado": True, "score": 10}
    result = classify_translation(audit, similarity=0.86, term_match_ratio=1.0)
    assert result == "approved"


def test_classify_approved_high_score_override():
    """Score >= 8 + strong metrics overrides strict auditor (path 2)."""
    audit = {"aprovado": False, "score": 8}
    result = classify_translation(audit, similarity=0.93, term_match_ratio=1.0)
    assert result == "approved"


def test_classify_review():
    """Score 7 + decent similarity = review."""
    audit = {"aprovado": False, "score": 7}
    result = classify_translation(audit, similarity=0.85, term_match_ratio=0.9)
    assert result == "review"


def test_classify_review_low_terms():
    """Score 8 but low term match = review (not approved via path 2)."""
    audit = {"aprovado": False, "score": 8}
    result = classify_translation(audit, similarity=0.90, term_match_ratio=0.85)
    assert result == "review"


def test_classify_rejected():
    """Low audit + low similarity = rejected."""
    audit = {"aprovado": False, "score": 3}
    result = classify_translation(audit, similarity=0.70, term_match_ratio=0.5)
    assert result == "rejected"
