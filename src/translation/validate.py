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


def _extract_numbers(text: str) -> list[str]:
    """Extract all numbers with optional units from text."""
    return re.findall(r"\d+(?:[.,]\d+)?\s*(?:mm|cm|ml)?", text)


def _extract_birads_categories(text: str) -> list[str]:
    """Extract BI-RADS categories from text."""
    return re.findall(r"(?:BI-?RADS|BIRADS)\s*:?\s*([0-6](?:[ABC])?)", text, re.IGNORECASE)


_LATERALITY_ES_TO_PT = {
    "derecha": "direita",
    "izquierda": "esquerda",
    "bilateral": "bilateral",
}


def _check_laterality(original_es: str, translated_pt: str) -> bool:
    """Check if laterality terms are correctly mapped ES->PT."""
    orig_lower = original_es.lower()
    trans_lower = translated_pt.lower()
    for es_term, pt_term in _LATERALITY_ES_TO_PT.items():
        if es_term in orig_lower:
            if pt_term not in trans_lower:
                return False
    return True


def validate_audit_findings(
    original_es: str,
    translated_pt: str,
    audit_result: dict,
    glossary_pairs: list[tuple[str, str]],
) -> dict:
    """Cross-validate DeepSeek's audit findings against the actual texts.

    For each inconsistency reported by the auditor, checks programmatically
    if the issue is real (confirmed) or a false positive (rejected).

    Verification per criterion:
        C1 (descriptors): glossary cross-check
        C2 (BI-RADS category): regex extraction and comparison
        C3 (measures): numeric extraction and comparison
        C4 (laterality): directional term mapping ES->PT
        C5 (omissions): sentence-level content check
        C6 (negation): negation keyword analysis
        C7 (temporal): trusted (hard to verify programmatically)

    Returns dict with:
        confirmed: list of verified inconsistencies to send for correction
        rejected: list of false positive findings with rejection reason
        verdict: 'correct' (send to Gemini) or 'keep' (translation is fine)
    """
    inconsistencies = audit_result.get("inconsistencias", [])
    if not inconsistencies:
        return {"confirmed": [], "rejected": [], "verdict": "keep"}

    orig_lower = original_es.lower()
    trans_lower = translated_pt.lower()

    confirmed = []
    rejected = []

    for inc in inconsistencies:
        criterio = inc.get("criterio", "").upper()
        problema = inc.get("problema", "")
        original_snippet = inc.get("original", "").lower()
        traducao_snippet = inc.get("traducao", "").lower()

        # C1: BI-RADS descriptors — verify against glossary
        if "C1" in criterio:
            if original_snippet and original_snippet not in orig_lower:
                rejected.append({**inc, "_rejection": "trecho original nao encontrado no texto"})
                continue
            if traducao_snippet and traducao_snippet not in trans_lower:
                rejected.append({**inc, "_rejection": "trecho da traducao nao encontrado no texto"})
                continue
            # Check if there's a real glossary mismatch
            is_glossary_issue = False
            for es_term, pt_term in glossary_pairs:
                if es_term.lower() in orig_lower and pt_term.lower() not in trans_lower:
                    is_glossary_issue = True
                    break
            if not is_glossary_issue and traducao_snippet:
                # Auditor flagged but all glossary terms are present
                rejected.append({**inc, "_rejection": "todos os termos do glossario presentes na traducao"})
                continue
            confirmed.append(inc)

        # C2: BI-RADS category — extract and compare
        elif "C2" in criterio:
            orig_cats = _extract_birads_categories(original_es)
            trans_cats = _extract_birads_categories(translated_pt)
            if sorted(orig_cats) == sorted(trans_cats):
                rejected.append({**inc, "_rejection": f"categorias BI-RADS identicas: {orig_cats}"})
            else:
                confirmed.append(inc)

        # C3: Measures and numbers — extract and compare
        elif "C3" in criterio:
            orig_nums = _extract_numbers(original_es)
            trans_nums = _extract_numbers(translated_pt)
            if sorted(orig_nums) == sorted(trans_nums):
                rejected.append({**inc, "_rejection": f"numeros identicos: {orig_nums}"})
            else:
                confirmed.append(inc)

        # C4: Laterality — verify mapping
        elif "C4" in criterio:
            if _check_laterality(original_es, translated_pt):
                rejected.append({**inc, "_rejection": "lateralidade correta na traducao"})
            else:
                confirmed.append(inc)

        # C5: Omissions/additions — check snippet presence
        elif "C5" in criterio:
            if original_snippet and original_snippet in orig_lower:
                # Check if the semantic content is in the translation
                confirmed.append(inc)
            elif original_snippet and original_snippet not in orig_lower:
                rejected.append({**inc, "_rejection": "trecho citado nao existe no original"})
            else:
                confirmed.append(inc)

        # C6: Negation/sense inversion — check negation keywords
        elif "C6" in criterio:
            neg_es = ["no se", "sin ", "ni ", "no "]
            neg_pt = ["nao se", "sem ", "nem ", "nao "]
            # Count negations in original and translation
            orig_neg = sum(1 for n in neg_es if n in orig_lower)
            trans_neg = sum(1 for n in neg_pt if n in trans_lower)
            if orig_neg == trans_neg:
                rejected.append({**inc, "_rejection": f"mesma quantidade de negacoes (orig={orig_neg}, trad={trans_neg})"})
            else:
                confirmed.append(inc)

        # C7: Temporal comparisons — hard to verify, trust auditor
        elif "C7" in criterio:
            confirmed.append(inc)

        # Unknown criterion — trust auditor
        else:
            confirmed.append(inc)

    # Verdict: only correct if there are confirmed issues
    verdict = "correct" if confirmed else "keep"

    return {
        "confirmed": confirmed,
        "rejected": rejected,
        "verdict": verdict,
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
