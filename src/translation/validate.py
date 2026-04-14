"""Validate translation fidelity: LLM audit + semantic similarity + BI-RADS lexicon check."""

import json
import re

from sentence_transformers import SentenceTransformer
import numpy as np


_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    """Lazy-load the embedding model (singleton)."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
    return _embedding_model


def compute_similarity(text_a: str, text_b: str) -> float:
    """Compute cosine similarity between two texts using multilingual embeddings."""
    model = get_embedding_model()
    embeddings = model.encode([text_a, text_b], convert_to_numpy=True)
    cos_sim = np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    )
    return float(cos_sim)


def check_birads_terms_preserved(
    original_es: str, translated_pt: str,
    glossary_pairs: list[tuple[str, str]],
) -> dict:
    """Check if BI-RADS terms from the original were correctly translated.

    For each ES term found in the original, checks if the corresponding PT term
    appears in the translation.

    Returns dict with match_ratio, matched_terms, and missing_terms.
    """
    original_lower = original_es.lower()
    translated_lower = translated_pt.lower()

    expected_translations = []
    for es_term, pt_term in glossary_pairs:
        if es_term.lower() in original_lower:
            expected_translations.append((es_term, pt_term))

    if not expected_translations:
        return {"match_ratio": 1.0, "matched_terms": [], "missing_terms": [], "total_expected": 0}

    matched = []
    missing = []
    for es_term, pt_term in expected_translations:
        if pt_term.lower() in translated_lower:
            matched.append({"es": es_term, "pt": pt_term})
        else:
            missing.append({"es": es_term, "pt_expected": pt_term})

    match_ratio = len(matched) / len(expected_translations)
    return {
        "match_ratio": match_ratio,
        "matched_terms": matched,
        "missing_terms": missing,
        "total_expected": len(expected_translations),
    }


def parse_audit_response(response_text: str) -> dict:
    """Parse the JSON audit response from the auditor LLM.

    Handles cases where the LLM wraps the JSON in markdown code blocks
    or adds extra text.

    Returns dict with keys: aprovado, score, inconsistencias.
    Falls back to a failed audit if parsing fails.
    """
    text = response_text.strip()

    # Try to extract JSON from markdown code block
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    else:
        # Try to find raw JSON object
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            text = json_match.group(0)

    try:
        result = json.loads(text)
        # Validate expected keys
        if "aprovado" not in result:
            result["aprovado"] = False
        if "score" not in result:
            result["score"] = 0
        if "inconsistencias" not in result:
            result["inconsistencias"] = []
        return result
    except (json.JSONDecodeError, ValueError):
        return {
            "aprovado": False,
            "score": 0,
            "inconsistencias": [{"criterio": "parse_error", "problema": f"Failed to parse audit response: {text[:200]}"}],
            "raw_response": text[:500],
        }


def classify_translation(audit_result: dict, similarity: float, term_match_ratio: float) -> str:
    """Classify overall translation quality combining audit + metrics.

    Returns 'approved', 'review', or 'rejected'.
    """
    if audit_result.get("aprovado") and similarity >= 0.90 and term_match_ratio >= 0.8:
        return "approved"
    if audit_result.get("score", 0) >= 7 and similarity >= 0.85:
        return "review"
    return "rejected"
