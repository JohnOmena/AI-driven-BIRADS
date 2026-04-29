"""T16 — Programmatic structural checks (regex determinístico).

Validações sobre cada par (ES, PT) cobrindo elementos clinicamente críticos:
  - Categoria BI-RADS (deve ser preservada)
  - Medidas (números + unidades — todos preservados)
  - Lateralidade (esquerda/direita — sem inversão)
  - Negação (preservada em estrutura)
  - Anatomia (menções essenciais presentes)
  - Drift PT-pt (cognatos diagnósticos)

Output: results/translation/structural_checks.csv (uma linha por laudo).

Algumas funções base já foram implementadas em T14.B (não nesta task): este
módulo cria-as do zero para ser independente.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

import pandas as pd


# --- Normalização ---

def _norm(s: str) -> str:
    s = str(s or "").lower().strip()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# --- 1. Categoria BI-RADS ---

CATEGORY_RE_ES = re.compile(r"BI[\s\-]?RADS\s*[:\.\-]?\s*(?:categor[íi]a)?\s*([0-6])(?:\s*[ABC])?", re.IGNORECASE)
CATEGORY_RE_PT = re.compile(r"BI[\s\-]?RADS\s*[:\.\-]?\s*(?:categoria)?\s*([0-6])(?:\s*[ABC])?", re.IGNORECASE)


def extract_birads_category(text: str) -> int | None:
    """Extrai a primeira categoria BI-RADS encontrada (0-6). Retorna None se não há."""
    if not text:
        return None
    m = CATEGORY_RE_ES.search(text) or CATEGORY_RE_PT.search(text)
    if m:
        return int(m.group(1))
    return None


def check_category_preserved(es_text: str, pt_text: str,
                              label: int | None = None) -> dict:
    """Avalia se a categoria BI-RADS foi preservada na tradução.

    Lógica:
      - Ambos textos sem categoria mencionada → PASS (não há o que comparar;
        categoria vem do birads_label dataset, não do texto livre)
      - ES menciona mas PT não (ou vice-versa) → FAIL (categoria foi perdida/adicionada)
      - Ambos mencionam → comparar; FAIL se diferentes
      - Quando ambos mencionam E há label disponível → também comparar com label
    """
    cat_es = extract_birads_category(es_text)
    cat_pt = extract_birads_category(pt_text)
    cat_label = int(label) if label is not None and not pd.isna(label) else None

    if cat_es is None and cat_pt is None:
        # Categoria não está no texto livre — nada a comparar (caso comum)
        category_pass = True
    elif cat_es is None or cat_pt is None:
        # Apenas um menciona — perda ou adição de categoria
        category_pass = False
    else:
        # Ambos mencionam — comparar
        category_pass = (cat_es == cat_pt)
        if category_pass and cat_label is not None:
            category_pass = (cat_pt == cat_label)

    return {
        "category_es":     cat_es,
        "category_pt":     cat_pt,
        "category_label":  cat_label,
        "category_pass":   category_pass,
    }


# --- 2. Medidas ---

MEASURE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(mm|cm|m²|%|ml)(?=\W|$)", re.IGNORECASE)


def extract_measures(text: str) -> list[tuple[float, str]]:
    """Lista ordenada de (valor, unidade). Normaliza vírgula→ponto."""
    out = []
    for m in MEASURE_RE.finditer(text or ""):
        val = float(m.group(1).replace(",", "."))
        unit = m.group(2).lower()
        out.append((val, unit))
    return sorted(out)


def check_measures_preserved(es_text: str, pt_text: str) -> dict:
    es_set = set(extract_measures(es_text))
    pt_set = set(extract_measures(pt_text))
    return {
        "measures_es_count":   len(es_set),
        "measures_pt_count":   len(pt_set),
        "measures_match":      es_set == pt_set,
        "measures_missing":    json.dumps(list(es_set - pt_set), ensure_ascii=False),
        "measures_extra":      json.dumps(list(pt_set - es_set), ensure_ascii=False),
    }


# --- 3. Lateralidade ---

LAT_PT_TO_ES = {
    "esquerda":  "izquierda", "esquerdo":  "izquierdo",
    "direita":   "derecha",   "direito":   "derecho",
    "bilateral": "bilateral",
}


def extract_laterality(text: str, lang: str = "pt") -> set[str]:
    """Retorna {'L', 'R', 'B'} encontrados no texto."""
    text_n = _norm(text)
    found = set()
    if lang == "pt":
        if re.search(r"\besquerd[oa]s?\b", text_n):
            found.add("L")
        if re.search(r"\bdireit[oa]s?\b", text_n):
            found.add("R")
        if re.search(r"\bbilatera[lis]+", text_n):  # bilateral, bilaterais, bilaterales  # bilateral, bilaterais, bilateralmente
            found.add("B")
    else:  # es
        if re.search(r"\bizquierd[oa]s?\b", text_n):
            found.add("L")
        if re.search(r"\bderech[oa]s?\b", text_n):
            found.add("R")
        if re.search(r"\bbilatera[lis]+", text_n):  # bilateral, bilaterais, bilaterales
            found.add("B")
    return found


def check_laterality_preserved(es_text: str, pt_text: str) -> dict:
    lat_es = extract_laterality(es_text, "es")
    lat_pt = extract_laterality(pt_text, "pt")
    return {
        "laterality_es":     ",".join(sorted(lat_es)),
        "laterality_pt":     ",".join(sorted(lat_pt)),
        "laterality_match":  lat_es == lat_pt,
    }


# --- 4. Negação ---
# T16 fix (2026-04-28): regex word-bounded com alternation ordenada (compostas
# primeiro, genérico último). re.findall consome non-overlapping → não duplica.
# Lista linear anterior subdimensionava PT em 24 p.p. (NEG_PT só "não se" mas
# laudos PT-br usam "não são observadas", "não há", "nem" predominantemente).

_NEG_ES_RE = re.compile(
    r"\b(?:"
    r"no\s+(?:se|son|fue|fueron|hay|ha)"            # passivas/compostas
    r"|ni|sin|ausencia|ausente|ningun[ao]?"          # léxicas + coordenativa
    r"|no"                                            # genérico (último)
    r")\b",
    re.IGNORECASE,
)
_NEG_PT_RE = re.compile(
    r"\b(?:"
    r"nao\s+(?:se|sao|foi|foram|ha)"                 # passivas/compostas
    r"|nem|sem|ausencia|ausente|nenhum[ao]?"          # léxicas + coordenativa
    r"|nao"                                           # genérico (último)
    r")\b",
    re.IGNORECASE,
)


def count_negations(text: str, lang: str = "pt") -> int:
    text_n = _norm(text)
    rgx = _NEG_PT_RE if lang == "pt" else _NEG_ES_RE
    return len(rgx.findall(text_n))


def check_negation_preserved(es_text: str, pt_text: str) -> dict:
    n_es = count_negations(es_text, "es")
    n_pt = count_negations(pt_text, "pt")
    ratio = (n_pt / n_es) if n_es > 0 else (1.0 if n_pt == 0 else 0.0)
    return {
        "negation_es_count":  n_es,
        "negation_pt_count":  n_pt,
        "negation_ratio":     round(ratio, 3),
        "negation_pass":      0.8 <= ratio <= 1.2 if n_es > 0 else (n_pt == 0),
    }


# --- 5. Anatomia ---

ANATOMY_TERMS_PT = ["mama", "quadrante", "axilar", "areolar", "mamilo", "linfonodo", "ducto", "tecido"]


def check_anatomy_present(pt_text: str) -> dict:
    text_n = _norm(pt_text)
    found = sum(1 for t in ANATOMY_TERMS_PT if t in text_n)
    return {
        "anatomy_terms_found":  found,
        "anatomy_pass":         found >= 1,  # qualquer menção anatômica é OK
    }


# --- 6. Drift PT-pt ---

PT_PT_MARKERS = [
    r"\barquitect[óo]nic[ao]s?\b",
    r"\bfacto\b",
    r"\bobjecto\b",
    r"\bacç[ãa]o\b",
    r"\bdirecç[ãa]o\b",
    r"\bperspectiv[ao]s?\b",  # PT-pt; PT-br: perspetiva também válido mas raro
    r"\butente\b",
    r"\becr[ãa]\b",
]
PT_PT_RE = re.compile("|".join(PT_PT_MARKERS), re.IGNORECASE)


def check_pt_drift(pt_text: str) -> dict:
    detected = PT_PT_RE.findall(pt_text or "")
    return {
        "pt_drift":         bool(detected),
        "pt_drift_terms":   json.dumps(detected, ensure_ascii=False),
    }


# --- Top-level: run on pair ---

def run_structural_checks(es_text: str, pt_text: str,
                           birads_label: int | float | None = None) -> dict:
    """Roda todas as 6 checagens; retorna dict completo + flag agregada."""
    cat = check_category_preserved(es_text, pt_text, birads_label)
    meas = check_measures_preserved(es_text, pt_text)
    lat = check_laterality_preserved(es_text, pt_text)
    neg = check_negation_preserved(es_text, pt_text)
    anat = check_anatomy_present(pt_text)
    drift = check_pt_drift(pt_text)

    out = {**cat, **meas, **lat, **neg, **anat, **drift}
    out["all_structural_pass"] = all([
        out["category_pass"],
        out["measures_match"],
        out["laterality_match"],
        out["negation_pass"],
        out["anatomy_pass"],
        not out["pt_drift"],
    ])
    return out


# --- Main ---

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out-csv", default="results/translation/structural_checks.csv")
    args = parser.parse_args()

    df_pt = pd.read_csv("data/reports_translated_pt.csv").drop_duplicates("report_id", keep="last")
    df_es = pd.read_csv("data/reports_raw_canonical.csv")
    df = df_pt.merge(df_es[["report_id", "report_text_raw"]],
                     on="report_id", suffixes=("_pt", "_es"))
    df = df.rename(columns={"report_text_raw_pt": "pt_text",
                              "report_text_raw_es": "es_text"})

    if args.limit:
        df = df.head(args.limit)

    out_path = Path(args.out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"T16: processando {len(df)} laudos")
    t_start = time.time()
    rows = []
    for i, row in enumerate(df.itertuples(index=False), 1):
        result = run_structural_checks(row.es_text, row.pt_text, row.birads_label)
        rec = {"report_id": row.report_id, **result}
        rows.append(rec)
        if i % 500 == 0:
            print(f"  [{i}/{len(df)}]")

    pd.DataFrame(rows).to_csv(out_path, index=False)
    elapsed = time.time() - t_start
    print(f"T16 completo em {elapsed:.1f}s")
    print(f"CSV: {out_path}")

    # Sanity prints
    df_out = pd.read_csv(out_path)
    print(f"\nSanity:")
    print(f"  category_pass:    {df_out['category_pass'].mean()*100:.2f}%")
    print(f"  measures_match:   {df_out['measures_match'].mean()*100:.2f}%")
    print(f"  laterality_match: {df_out['laterality_match'].mean()*100:.2f}%")
    print(f"  negation_pass:    {df_out['negation_pass'].mean()*100:.2f}%")
    print(f"  anatomy_pass:     {df_out['anatomy_pass'].mean()*100:.2f}%")
    print(f"  pt_drift rate:    {df_out['pt_drift'].mean()*100:.2f}%")
    print(f"  all_structural_pass: {df_out['all_structural_pass'].mean()*100:.2f}%")


if __name__ == "__main__":
    sys.exit(main())
