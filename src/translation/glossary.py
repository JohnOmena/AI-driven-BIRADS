"""Load and format the BI-RADS glossary for translation prompts."""

import json
from pathlib import Path


def load_glossary(glossary_path: str) -> list[tuple[str, str]]:
    """Load glossary JSON and return flat list of (es, pt) term pairs."""
    with open(glossary_path, encoding="utf-8") as f:
        data = json.load(f)

    pairs = []
    for category_terms in data["terms"].values():
        for entry in category_terms:
            pairs.append((entry["es"], entry["pt"]))
    return pairs


def format_glossary_for_prompt(pairs: list[tuple[str, str]]) -> str:
    """Format term pairs as a readable glossary block for the LLM prompt."""
    lines = ["Glossário de termos BI-RADS (Espanhol → Português):"]
    for es, pt in pairs:
        lines.append(f"  {es} → {pt}")
    return "\n".join(lines)
