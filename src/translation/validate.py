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


def _is_subterm_of_matched(es_term: str, all_es_terms: list[str]) -> bool:
    """Check if es_term is a substring of another longer glossary term in the list.

    Prevents false negatives like "areola" matching inside "retroareolar"
    when "retroareolar" is also a glossary term found in the original.
    """
    es_lower = es_term.lower()
    for other in all_es_terms:
        other_lower = other.lower()
        if other_lower != es_lower and es_lower in other_lower:
            return True
    return False


def check_birads_terms_preserved(
    original_es: str, translated_pt: str,
    glossary_pairs: list[tuple[str, str]],
) -> dict:
    """Check if BI-RADS terms from the original were correctly translated.

    For each ES term found in the original, checks if the corresponding PT term
    appears in the translation. Uses word-boundary matching to avoid false
    substring hits (e.g. "areola" inside "retroareolar").

    Returns dict with match_ratio, matched_terms, and missing_terms.
    """
    original_lower = original_es.lower()
    translated_lower = translated_pt.lower()

    # First pass: find all ES terms present in original
    found_es_terms = [es for es, _ in glossary_pairs if es.lower() in original_lower]

    # Second pass: filter out terms that are substrings of other found terms
    expected_translations = []
    for es_term, pt_term in glossary_pairs:
        if es_term.lower() in original_lower:
            if not _is_subterm_of_matched(es_term, found_es_terms):
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


def postprocess_translation(original_es: str, translated_pt: str) -> tuple[str, list[dict]]:
    """Fix known systematic Gemini translation errors.

    Fixes applied:
        1. Gender agreement: 'margens obscurecidos' -> 'margens obscurecidas'
        2. Spanish verbs: 'observan' -> 'observam'
        3. Medical term fidelity: 'características' -> 'caracteres' (when original uses 'caracteres')
        4. Formatting: restore '.-' line endings when original has them

    Returns (corrected_text, list_of_fixes_applied).
    """
    text = translated_pt
    fixes = []

    # Fix 1: Gender agreement on BI-RADS descriptors
    if re.search(r"margens\s+obscurecidos", text, re.IGNORECASE):
        text = re.sub(r"(?i)(margens\s+)obscurecidos", r"\1obscurecidas", text)
        fixes.append({"tipo": "C1_concordancia_genero", "de": "margens obscurecidos", "para": "margens obscurecidas"})

    # Fix 2: Spanish verb conjugation
    if re.search(r"\bobservan\b", text, re.IGNORECASE):
        text = re.sub(r"(?i)\bobservan\b", "observam", text)
        fixes.append({"tipo": "C6_verbo_espanhol", "de": "observan", "para": "observam"})

    # Fix 3: Preserve medical term 'caracteres' (not 'características')
    if "caracteres" in original_es.lower():
        new_text = re.sub(
            r"(?i)caracter\u00edsticas|caracteristicas",
            lambda m: "Caracteres" if m.group(0)[0].isupper() else "caracteres",
            text,
        )
        if new_text != text:
            text = new_text
            fixes.append({"tipo": "C1_fidelidade_lexical", "de": "caracteristicas", "para": "caracteres"})

    # Fix 4: Restore '.-' line endings
    orig_lines = original_es.strip().split("\n")
    trans_lines = text.strip().split("\n")
    if len(orig_lines) == len(trans_lines):
        restored = False
        fixed_lines = []
        for ol, tl in zip(orig_lines, trans_lines):
            if ol.rstrip().endswith(".-") and tl.rstrip().endswith(".") and not tl.rstrip().endswith(".-"):
                tl = tl.rstrip() + "-"
                restored = True
            fixed_lines.append(tl)
        if restored:
            text = "\n".join(fixed_lines)
            fixes.append({"tipo": "C5_formatacao", "de": ".", "para": ".-"})

    return text, fixes


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

    Approval paths:
        1. Auditor approved + similarity >= 0.85 + terms >= 0.80
        2. Score >= 8 + similarity >= 0.85 + terms >= 0.90
           (overrides strict auditor for high-quality translations)

    Returns 'approved', 'review', or 'rejected'.
    """
    score = audit_result.get("score", 0)

    # Path 1: Auditor explicitly approved
    if audit_result.get("aprovado") and similarity >= 0.85 and term_match_ratio >= 0.80:
        return "approved"

    # Path 2: High score + strong metrics (auditor strict but translation good)
    if score >= 8 and similarity >= 0.85 and term_match_ratio >= 0.90:
        return "approved"

    if score >= 7 and similarity >= 0.80:
        return "review"
    return "rejected"
