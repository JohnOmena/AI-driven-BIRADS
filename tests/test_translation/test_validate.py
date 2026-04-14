"""Tests for translation validation (similarity + BI-RADS lexicon check)."""

from src.translation.validate import (
    check_birads_terms_match,
    classify_divergence,
)


def test_birads_terms_match_identical():
    """Identical translations should have all terms matching."""
    glossary_pt = ["mama direita", "calcificação", "nódulo"]
    text_a = "Observa-se um nódulo na mama direita com calcificação."
    text_b = "Observa-se um nódulo na mama direita com calcificação."
    result = check_birads_terms_match(text_a, text_b, glossary_pt)
    assert result["match_ratio"] == 1.0


def test_birads_terms_match_divergent():
    """Different BI-RADS terms should be flagged."""
    glossary_pt = ["mama direita", "mama esquerda", "nódulo"]
    text_a = "Observa-se um nódulo na mama direita."
    text_b = "Observa-se um nódulo na mama esquerda."
    result = check_birads_terms_match(text_a, text_b, glossary_pt)
    assert result["match_ratio"] < 1.0
    assert len(result["mismatched_terms"]) > 0


def test_classify_divergence_ok():
    """High similarity + high term match = OK."""
    result = classify_divergence(similarity=0.98, term_match_ratio=1.0, threshold=0.95)
    assert result == "ok"


def test_classify_divergence_review():
    """Low similarity = needs review."""
    result = classify_divergence(similarity=0.90, term_match_ratio=1.0, threshold=0.95)
    assert result == "review"


def test_classify_divergence_term_mismatch():
    """High similarity but low term match = needs review."""
    result = classify_divergence(similarity=0.98, term_match_ratio=0.5, threshold=0.95)
    assert result == "review"
