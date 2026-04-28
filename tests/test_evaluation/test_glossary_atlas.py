"""Tests de invariantes do glossário Atlas (T12).

Garantem que o JSON é estruturalmente válido e que a regra de
retrocompatibilidade (toda PT do antigo em pt_variants_acceptable do Atlas)
e morfologia (4 tags por forms_pt/forms_es) não são quebradas em mudanças
futuras.
"""

import json
from pathlib import Path

import pytest


REQUIRED_MORPH_TAGS = {"M-SING", "F-SING", "M-PLUR", "F-PLUR"}


@pytest.fixture(scope="module")
def atlas() -> dict:
    return json.loads(
        Path("configs/birads_glossary_atlas_es_pt.json").read_text(encoding="utf-8")
    )


@pytest.fixture(scope="module")
def old_glossary() -> dict:
    return json.loads(
        Path("configs/birads_glossary_es_pt.json").read_text(encoding="utf-8")
    )


# --- Estrutura ---

def test_atlas_has_required_top_keys(atlas):
    assert "metadata" in atlas
    assert "categories" in atlas
    assert isinstance(atlas["categories"], dict)
    assert len(atlas["categories"]) > 0


def test_every_entry_has_canonical_and_acceptable(atlas):
    """Todo termo Atlas precisa de pt_canonical + pt_variants_acceptable."""
    for cat_key, entries in atlas["categories"].items():
        for entry in entries:
            assert "es" in entry, f"{cat_key} entrada sem 'es': {entry}"
            assert "pt_canonical" in entry, f"{entry['es']} sem pt_canonical"
            assert "pt_variants_acceptable" in entry, \
                f"{entry['es']} sem pt_variants_acceptable"
            assert isinstance(entry["pt_variants_acceptable"], list)
            assert len(entry["pt_variants_acceptable"]) >= 1, \
                f"{entry['es']} pt_variants_acceptable vazio"


def test_canonical_is_in_acceptable(atlas):
    """pt_canonical deve estar em pt_variants_acceptable (consistência)."""
    for cat_key, entries in atlas["categories"].items():
        for entry in entries:
            canonical = entry["pt_canonical"].lower()
            acceptable = {v.lower() for v in entry["pt_variants_acceptable"]}
            assert canonical in acceptable, \
                f"{entry['es']} ({cat_key}): pt_canonical={entry['pt_canonical']!r} " \
                f"não está em pt_variants_acceptable"


# --- Retrocompatibilidade (regra invariante) ---

def test_atlas_backward_compatible_with_original(atlas, old_glossary):
    """Toda PT do glossário original deve aparecer em pt_variants_acceptable do Atlas.

    Pré-condição absoluta — se quebrar, falsos positivos retroativos
    no T13/T17 (apontamentos contra o tradutor que seguiu o glossário recebido).
    """
    old_pt = {
        e["pt"].strip().lower()
        for cat, items in old_glossary["terms"].items()
        for e in items
    }

    new_acceptable = set()
    for cat, items in atlas["categories"].items():
        for e in items:
            new_acceptable.add(e["pt_canonical"].strip().lower())
            new_acceptable.update(v.strip().lower() for v in e["pt_variants_acceptable"])

    missing = old_pt - new_acceptable
    assert not missing, f"Atlas falta retrocompatibilidade para: {sorted(missing)}"


# --- Morfologia (T18 pré-requisito) ---

def test_morphology_entries_have_4_tags(atlas):
    """forms_pt/forms_es em adjetivos têm exatamente M-SING/F-SING/M-PLUR/F-PLUR."""
    for cat_key, entries in atlas["categories"].items():
        for entry in entries:
            for field in ("forms_pt", "forms_es"):
                forms = entry.get(field)
                if forms is None:
                    continue
                assert set(forms.keys()) == REQUIRED_MORPH_TAGS, \
                    f"{entry['es']} ({cat_key}): {field} keys {set(forms.keys())} " \
                    f"!= {REQUIRED_MORPH_TAGS}"


def test_morphology_pt_forms_in_acceptable(atlas):
    """Toda forma listada em forms_pt deve estar em pt_variants_acceptable."""
    for cat_key, entries in atlas["categories"].items():
        for entry in entries:
            forms_pt = entry.get("forms_pt")
            if not forms_pt:
                continue
            acceptable = {v.lower() for v in entry["pt_variants_acceptable"]}
            acceptable.add(entry["pt_canonical"].lower())
            for tag, form in forms_pt.items():
                assert form.lower() in acceptable, \
                    f"{entry['es']} ({cat_key}): forms_pt[{tag}]={form!r} " \
                    f"não está em pt_variants_acceptable"


def test_morphology_pt_es_must_coexist(atlas):
    """Se tem forms_pt, tem forms_es e vice-versa."""
    for cat_key, entries in atlas["categories"].items():
        for entry in entries:
            has_pt = "forms_pt" in entry
            has_es = "forms_es" in entry
            assert has_pt == has_es, \
                f"{entry['es']} ({cat_key}): forms_pt e forms_es devem coexistir"


# --- Sanity ---

def test_no_critical_terms_have_es_in_pt(atlas):
    """pt_canonical não pode ser palavra ES típica (regression test).

    Ex: 'lineal fino' (espanhol) era usado em prompt.py do auditor, T12.5
    corrigiu derivando do Atlas. Garantir que Atlas não cai no mesmo erro.
    """
    es_only_words = {"lineal", "puntiforme", "pleomorfico"}  # sem til = ES
    for cat_key, entries in atlas["categories"].items():
        for entry in entries:
            canonical_lower = entry["pt_canonical"].lower()
            for es_word in es_only_words:
                if es_word == "puntiforme":
                    continue  # puntiforme é aceito também em PT-br BI-RADS
                assert es_word not in canonical_lower.split(), \
                    f"{entry['es']} ({cat_key}): pt_canonical contém palavra ES " \
                    f"{es_word!r}: {entry['pt_canonical']!r}"
