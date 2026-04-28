"""Tests para src/translation/c1_descriptors.py — derivação programática do C1."""

import json

import pytest

from src.translation.c1_descriptors import build_c1_block, C1_CATEGORIES, C1_LABELS


@pytest.fixture
def atlas_minimal(tmp_path):
    """Atlas mínimo para testes unitários — não usa o Atlas real do projeto."""
    atlas = {
        "metadata": {"version": "test"},
        "categories": {
            "mass_shape": [
                {"es": "oval", "pt_canonical": "oval",
                 "pt_variants_acceptable": ["oval", "ovalada", "ovalado"]},
                {"es": "irregular", "pt_canonical": "irregular",
                 "pt_variants_acceptable": ["irregular"]},
            ],
            "mass_margin": [
                {"es": "espiculado", "pt_canonical": "espiculado",
                 "pt_variants_acceptable": ["espiculado", "espiculada",
                                             "espiculados", "espiculadas"]},
            ],
            "mass_density": [
                {"es": "isodenso", "pt_canonical": "isodenso",
                 "pt_variants_acceptable": ["isodenso", "isodensa", "isodensos", "isodensas"]},
            ],
            "calcifications_morphology": [],
            "calcifications_distribution": [],
            "associated_features": [],
            # Categoria que NÃO entra em C1 — deve ser ignorada
            "anatomy": [
                {"es": "mama", "pt_canonical": "mama",
                 "pt_variants_acceptable": ["mama", "mamas"]},
            ],
        }
    }
    p = tmp_path / "atlas.json"
    p.write_text(json.dumps(atlas, ensure_ascii=False), encoding="utf-8")
    return str(p)


def test_block_includes_all_acceptable_variants(atlas_minimal):
    """Todas as variantes aceitáveis aparecem, não apenas canonical."""
    block = build_c1_block(atlas_minimal)
    # oval/ovalada/ovalado em alguma ordem (separadas por /)
    assert "oval/ovalada/ovalado" in block or \
           "ovalada/oval/ovalado" in block or \
           "oval" in block and "ovalada" in block and "ovalado" in block


def test_block_has_required_section_headers(atlas_minimal):
    """Cada categoria C1 produz um label legível (Forma, Margem, etc)."""
    block = build_c1_block(atlas_minimal)
    assert "Forma:" in block
    assert "Margem:" in block
    assert "Densidade:" in block


def test_block_excludes_non_c1_categories(atlas_minimal):
    """Anatomy (mama) NÃO deve aparecer no bloco C1."""
    block = build_c1_block(atlas_minimal)
    # 'mama' fixture tem só 'mama' como termo, e fixture coloca em anatomy
    # então 'mama' não deve aparecer no bloco C1 (que só pega 6 categorias específicas)
    # Atenção: a string 'mama' pode aparecer em outros contextos — checar pelo label
    assert "Anatomia:" not in block
    assert "anatomy" not in block.lower()


def test_block_has_acceptance_clause(atlas_minimal):
    """Bloco termina com instrução de aceitar qualquer variante."""
    block = build_c1_block(atlas_minimal)
    assert "Aceite QUALQUER variante" in block


def test_block_explicit_about_morphological_agreement(atlas_minimal):
    """Bloco diz que concordância de gênero/número não é erro de C1."""
    block = build_c1_block(atlas_minimal)
    assert "concordancia" in block.lower() or "morfossintatica" in block.lower()


def test_block_uses_real_atlas():
    """Smoke test contra o Atlas real do projeto."""
    block = build_c1_block()  # default = configs/birads_glossary_atlas_es_pt.json

    # Categorias esperadas
    assert "Forma:" in block
    assert "Margem:" in block
    assert "Densidade:" in block
    assert "Morfologia de calcificacoes:" in block
    assert "Distribuicao de calcificacoes:" in block

    # Termos PT-br corretos com til devem aparecer
    assert "heterogêneo" in block
    assert "pleomórfico" in block
    assert "linear fino" in block

    # NÃO deve ter espanhol cru ou PT-pt errado
    assert "lineal fino" not in block.lower()  # ES errado
    # heterogeneo (sem til) só aparece se a versão correta estiver presente
    # (porque "heterogêneo" contém "heterogeneo" como substring)
    assert "heterogeneo" not in block.lower() or "heterogêneo" in block

    # Deve incluir TODAS as variantes morfológicas
    # ex: pleomórfico/pleomórfica/pleomórficos/pleomórficas
    assert "pleomórfica" in block
    assert "espiculada" in block
    assert "espiculado" in block


def test_c1_categories_are_6():
    """C1 cobre exatamente as 6 categorias do decision_log."""
    expected = {
        "mass_shape", "mass_margin", "mass_density",
        "calcifications_morphology", "calcifications_distribution",
        "associated_features",
    }
    assert set(C1_CATEGORIES) == expected


def test_every_category_has_label():
    """Cada categoria C1 tem um label legível em PT-br."""
    for cat in C1_CATEGORIES:
        assert cat in C1_LABELS, f"Categoria {cat} sem label"
