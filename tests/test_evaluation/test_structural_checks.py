"""Tests para src/evaluation/structural_checks.py — T16."""

import pytest

from src.evaluation.structural_checks import (
    extract_birads_category,
    check_category_preserved,
    extract_measures,
    check_measures_preserved,
    extract_laterality,
    check_laterality_preserved,
    count_negations,
    check_negation_preserved,
    check_anatomy_present,
    check_pt_drift,
    run_structural_checks,
)


# --- Categoria BI-RADS ---

def test_extract_category_birads_simple():
    assert extract_birads_category("BI-RADS 4") == 4
    assert extract_birads_category("BI-RADS: categoría 2") == 2
    assert extract_birads_category("birads-3") == 3


def test_extract_category_subcategoria():
    """Subcategoria 4A/4B/4C — pega o número 4."""
    assert extract_birads_category("BI-RADS 4A") == 4


def test_extract_category_absent():
    assert extract_birads_category("nenhuma menção") is None


def test_check_category_preserved_match():
    out = check_category_preserved("BI-RADS 4 lesão", "BI-RADS 4 lesão", label=4)
    assert out["category_pass"] is True


def test_check_category_preserved_mismatch():
    out = check_category_preserved("BI-RADS 4", "BI-RADS 3", label=4)
    assert out["category_pass"] is False


# --- Medidas ---

def test_extract_measures_normalizes_comma():
    """Vírgula vira ponto: 2,5cm → 2.5cm."""
    assert extract_measures("nódulo 15mm e 2,5cm") == [(2.5, "cm"), (15.0, "mm")]


def test_extract_measures_handles_unit_variations():
    measures = extract_measures("calcificação 0.5 mm e 10%")
    assert (0.5, "mm") in measures
    assert (10.0, "%") in measures


def test_check_measures_preserved_match():
    es = "nódulo de 15mm na mama"
    pt = "nódulo de 15mm na mama"
    out = check_measures_preserved(es, pt)
    assert out["measures_match"] is True


def test_check_measures_preserved_mismatch():
    """ES: 15mm, PT: 15cm — divergência crítica."""
    es = "nódulo de 15mm"
    pt = "nódulo de 15cm"
    out = check_measures_preserved(es, pt)
    assert out["measures_match"] is False


# --- Lateralidade ---

def test_extract_laterality_es():
    assert extract_laterality("mama izquierda", "es") == {"L"}
    assert extract_laterality("mama derecha", "es") == {"R"}
    assert extract_laterality("hallazgos bilaterales", "es") == {"B"}


def test_extract_laterality_pt():
    assert extract_laterality("mama esquerda", "pt") == {"L"}
    assert extract_laterality("mama direita", "pt") == {"R"}
    assert extract_laterality("achados bilaterais", "pt") == {"B"}


def test_check_laterality_preserved_no_inversion():
    out = check_laterality_preserved("mama izquierda", "mama esquerda")
    assert out["laterality_match"] is True


def test_check_laterality_preserved_inversion_detected():
    """ES esquerda → PT direita = erro crítico."""
    out = check_laterality_preserved("mama izquierda", "mama direita")
    assert out["laterality_match"] is False


# --- Negação ---

def test_count_negations_es():
    assert count_negations("no se observan calcificaciones", "es") >= 1
    assert count_negations("sin nódulos", "es") >= 1


def test_count_negations_pt():
    assert count_negations("não se observam calcificações", "pt") >= 1
    assert count_negations("sem nódulos", "pt") >= 1


def test_check_negation_preserved_match():
    es = "no se observan nódulos"
    pt = "não se observam nódulos"
    out = check_negation_preserved(es, pt)
    assert out["negation_pass"] is True


def test_check_negation_lost():
    """ES tem 2 negações, PT tem 0 — erro grave."""
    es = "no se observan nódulos sin calcificaciones"
    pt = "observam-se nódulos com calcificações"
    out = check_negation_preserved(es, pt)
    assert out["negation_pass"] is False


# --- Anatomia ---

def test_check_anatomy_pass():
    out = check_anatomy_present("mama direita com lesão no quadrante superior")
    assert out["anatomy_pass"] is True


def test_check_anatomy_fail_no_terms():
    out = check_anatomy_present("xpto qweqwe asdf")
    assert out["anatomy_pass"] is False


# --- Drift PT-pt ---

def test_check_pt_drift_clean():
    out = check_pt_drift("distorção arquitetural na mama esquerda")
    assert out["pt_drift"] is False


def test_check_pt_drift_detected():
    out = check_pt_drift("distorção arquitectónica na mama esquerda")
    assert out["pt_drift"] is True
    assert "arquitectónica" in out["pt_drift_terms"] or "arquitect" in out["pt_drift_terms"].lower()


def test_check_pt_drift_facto():
    out = check_pt_drift("o facto é que")
    assert out["pt_drift"] is True


# --- Top-level integration ---

def test_run_structural_checks_all_pass():
    es = "mama izquierda BI-RADS 4 nódulo 15mm sin calcificaciones"
    pt = "mama esquerda BI-RADS 4 nódulo 15mm sem calcificações"
    out = run_structural_checks(es, pt, birads_label=4)
    assert out["all_structural_pass"] is True


def test_run_structural_checks_category_fail():
    es = "BI-RADS 4 lesão"
    pt = "BI-RADS 3 lesão"
    out = run_structural_checks(es, pt, birads_label=4)
    assert out["all_structural_pass"] is False
    assert out["category_pass"] is False


def test_run_structural_checks_pt_drift_fails_aggregate():
    """pt_drift True deve impedir all_structural_pass."""
    es = "BI-RADS 2 mama izquierda"
    pt = "BI-RADS 2 mama esquerda — facto presente"  # 'facto' = PT-pt
    out = run_structural_checks(es, pt, birads_label=2)
    assert out["pt_drift"] is True
    assert out["all_structural_pass"] is False
