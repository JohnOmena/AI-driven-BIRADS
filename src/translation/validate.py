"""Validate translation fidelity: semantic similarity + BI-RADS lexicon check."""

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


def check_birads_terms_match(
    text_a: str, text_b: str, glossary_pt_terms: list[str]
) -> dict:
    """Check if both translations contain the same BI-RADS terms.

    Returns dict with match_ratio and list of mismatched terms.
    """
    text_a_lower = text_a.lower()
    text_b_lower = text_b.lower()

    terms_in_a = set()
    terms_in_b = set()
    for term in glossary_pt_terms:
        term_lower = term.lower()
        if term_lower in text_a_lower:
            terms_in_a.add(term)
        if term_lower in text_b_lower:
            terms_in_b.add(term)

    all_terms = terms_in_a | terms_in_b
    if not all_terms:
        return {"match_ratio": 1.0, "mismatched_terms": [], "terms_found": 0}

    matching = terms_in_a & terms_in_b
    mismatched = list(all_terms - matching)
    match_ratio = len(matching) / len(all_terms)

    return {
        "match_ratio": match_ratio,
        "mismatched_terms": mismatched,
        "terms_found": len(all_terms),
    }


def classify_divergence(
    similarity: float, term_match_ratio: float, threshold: float = 0.95
) -> str:
    """Classify whether a translation pair needs review.

    Returns 'ok' or 'review'.
    """
    if similarity >= threshold and term_match_ratio >= 0.8:
        return "ok"
    return "review"
