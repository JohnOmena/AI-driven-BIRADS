"""Tests for glossary loading and formatting."""

import json
import tempfile
from pathlib import Path

from src.translation.glossary import load_glossary, format_glossary_for_prompt


def test_load_glossary_returns_term_pairs():
    """Loading the glossary returns a flat list of (es, pt) term pairs."""
    glossary_data = {
        "metadata": {"source": "test"},
        "terms": {
            "anatomy": [
                {"es": "mama derecha", "pt": "mama direita"},
                {"es": "mama izquierda", "pt": "mama esquerda"},
            ],
            "morphology": [
                {"es": "espiculado", "pt": "espiculado"},
            ],
        },
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(glossary_data, f, ensure_ascii=False)
        tmp_path = f.name

    pairs = load_glossary(tmp_path)
    assert len(pairs) == 3
    assert ("mama derecha", "mama direita") in pairs
    assert ("espiculado", "espiculado") in pairs
    Path(tmp_path).unlink()


def test_format_glossary_for_prompt():
    """Glossary formatted for prompt contains ES→PT mappings."""
    pairs = [
        ("mama derecha", "mama direita"),
        ("calcificación", "calcificação"),
    ]
    text = format_glossary_for_prompt(pairs)
    assert "mama derecha → mama direita" in text
    assert "calcificación → calcificação" in text
