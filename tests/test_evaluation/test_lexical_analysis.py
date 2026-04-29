"""Tests para src/evaluation/lexical_analysis.py — T17."""

import pytest

from src.evaluation.lexical_analysis import (
    categorize_pt_variant,
    count_term_occurrences,
    analyze_laudo_lexical,
    detect_anomalies,
    _is_gender_variant,
    _is_number_variant,
)


@pytest.fixture
def entry_oval():
    return {
        "es": "oval",
        "pt_canonical": "oval",
        "pt_variants_acceptable": ["oval", "ovalada", "ovalado"],
        "pt_variants_unacceptable": ["oval do"],
    }


# --- Categorização ---

def test_canonical_match(entry_oval):
    assert categorize_pt_variant("oval", entry_oval) == "canonical"


def test_acceptable_non_canonical(entry_oval):
    assert categorize_pt_variant("ovalado", entry_oval) == "acceptable"


def test_gender_variant_inferred(entry_oval):
    """Variante não listada que difere só em -o/-a."""
    entry = {**entry_oval, "pt_variants_acceptable": ["oval"]}  # remove ovalada/ovalado
    # "ovala" diferiria de "oval" em sufixo a (mas len difere)
    # Vamos usar caso clássico: redondo/redonda
    entry2 = {"es": "redondo", "pt_canonical": "redondo",
              "pt_variants_acceptable": ["redondo"]}
    assert categorize_pt_variant("redonda", entry2) == "gender_variant"


def test_number_variant_inferred():
    entry = {"es": "oval", "pt_canonical": "oval",
             "pt_variants_acceptable": ["oval"]}
    assert categorize_pt_variant("ovais", entry) in ("number_variant", "unknown_for_term")
    # caso clássico:
    entry2 = {"es": "calcificacion", "pt_canonical": "calcificacao",
              "pt_variants_acceptable": ["calcificacao"]}
    assert categorize_pt_variant("calcificacaos", entry2) == "number_variant"


def test_unacceptable_typo(entry_oval):
    assert categorize_pt_variant("oval do", entry_oval) == "unacceptable"


def test_unknown_for_term(entry_oval):
    assert categorize_pt_variant("redondo", entry_oval) == "unknown_for_term"


def test_categorize_case_insensitive(entry_oval):
    assert categorize_pt_variant("OVALADA", entry_oval) == "acceptable"


# --- count_term_occurrences ---

def test_count_term_word_boundary():
    assert count_term_occurrences("massa esquerda", "massa") == 1
    assert count_term_occurrences("massas esquerdas", "massa") == 0  # word boundary


def test_count_term_accent_insensitive():
    assert count_term_occurrences("calcificação benigna", "calcificacao") == 1


def test_count_term_multiple():
    assert count_term_occurrences("massa massa massa", "massa") == 3


# --- _is_gender_variant / _is_number_variant ---

def test_gender_o_a():
    assert _is_gender_variant("redondo", "redonda") is True
    assert _is_gender_variant("redonda", "redondo") is True


def test_gender_not_same_word():
    assert _is_gender_variant("redonda", "redonda") is False


def test_number_simple_s():
    assert _is_number_variant("massas", "massa") is True
    assert _is_number_variant("massa", "massas") is True


def test_number_es_plural():
    assert _is_number_variant("margens", "margem") is True


def test_number_not_same():
    assert _is_number_variant("massa", "massa") is False


# --- analyze_laudo_lexical (integração) ---

def test_analyze_term_present_with_canonical():
    atlas = {"categories": {"shape": [
        {"es": "oval", "pt_canonical": "oval",
         "pt_variants_acceptable": ["oval"],
         "bi_rads_code": "MASS_SHAPE_OVAL"}
    ]}}
    rows = analyze_laudo_lexical("masa oval", "massa oval", atlas)
    assert len(rows) == 1
    assert rows[0]["es_term"] == "oval"
    assert rows[0]["canonical"] == 1


def test_analyze_term_absent_returns_empty():
    atlas = {"categories": {"shape": [
        {"es": "oval", "pt_canonical": "oval",
         "pt_variants_acceptable": ["oval"]}
    ]}}
    rows = analyze_laudo_lexical("masa irregular", "massa irregular", atlas)
    assert rows == []  # 'oval' não no ES


def test_analyze_loss_flag():
    """ES tem 3 ocorrências, PT tem 1 — perda."""
    atlas = {"categories": {"shape": [
        {"es": "nodulo", "pt_canonical": "nodulo",
         "pt_variants_acceptable": ["nodulo"]}
    ]}}
    rows = analyze_laudo_lexical("nodulo nodulo nodulo", "nodulo apenas", atlas)
    assert rows[0]["lexical_loss_flag"] is True


def test_analyze_no_loss_when_balanced():
    atlas = {"categories": {"shape": [
        {"es": "nodulo", "pt_canonical": "nodulo",
         "pt_variants_acceptable": ["nodulo"]}
    ]}}
    rows = analyze_laudo_lexical("nodulo grande", "nodulo grande", atlas)
    assert rows[0]["lexical_loss_flag"] is False


# --- detect_anomalies ---

def test_no_anomaly_for_canonical_use():
    atlas = {"categories": {"shape": [
        {"es": "oval", "pt_canonical": "oval",
         "pt_variants_acceptable": ["oval"]}
    ]}}
    anomalies = detect_anomalies("masa oval", "massa oval", atlas)
    assert anomalies == []


def test_no_anomaly_for_acceptable_variant():
    atlas = {"categories": {"shape": [
        {"es": "oval", "pt_canonical": "oval",
         "pt_variants_acceptable": ["oval", "ovalada"]}
    ]}}
    anomalies = detect_anomalies("masa oval", "massa ovalada", atlas)
    assert anomalies == []  # ovalada está em acceptable


def test_anomaly_for_unacceptable_typo():
    atlas = {"categories": {"shape": [
        {"es": "oval", "pt_canonical": "oval",
         "pt_variants_acceptable": ["oval"],
         "pt_variants_unacceptable": ["oval do"]}
    ]}}
    anomalies = detect_anomalies("masa oval", "massa oval do irregular", atlas)
    assert len(anomalies) == 1
    assert anomalies[0]["category"] == "unacceptable"
