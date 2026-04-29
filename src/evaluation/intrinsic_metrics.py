"""T15 — Métricas intrínsecas de tradução automática (ES↔PT).

Métricas main:
  - BERTScore-F1 (xlm-roberta-large) — semântica via embeddings contextuais
  - chrF++ (sacrebleu) — char n-grams + word 2-grams, robusta para línguas próximas
  - Cosine similarity (mpnet multilingual) — semântica via embedding distinto
  - Length ratio — sanity check de omissão/expansão

Métrica apêndice:
  - TER (sacrebleu) — edit distance complementar

⚠ BLEU intencionalmente excluído das métricas intrínsecas ES↔PT.
Razão: par românico próximo + flexão morfológica torna BLEU enviesado para baixo
mesmo com semântica preservada. chrF++ é a métrica lexical recomendada pela
literatura recente (Popović 2017, Freitag et al. 2022). BLEU permanece em F2
(back-translation ES↔ES_bt, monolingual, onde é apropriado).

Outputs:
  - results/translation/intrinsic_metrics.csv (uma linha por laudo)
  - results/translation/intrinsic_metrics_summary.json (agregados para T23)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


def tokenize_basic(text: str) -> list[str]:
    """Tokenização simples por whitespace (length_ratio)."""
    return str(text).strip().split()


def length_ratio(es_text: str, pt_text: str) -> float:
    """len(pt_tokens) / len(es_tokens)."""
    es_tokens = tokenize_basic(es_text)
    pt_tokens = tokenize_basic(pt_text)
    if not es_tokens:
        return 0.0
    return len(pt_tokens) / len(es_tokens)


def compute_chrf(reference: str, hypothesis: str) -> float:
    """chrF++ via sacrebleu. reference = ES, hypothesis = PT (ou vice-versa)."""
    import sacrebleu
    score = sacrebleu.corpus_chrf([hypothesis], [[reference]],
                                    word_order=2, char_order=6)
    return float(score.score)


def compute_ter(reference: str, hypothesis: str) -> float:
    """TER via sacrebleu (edit distance normalizada)."""
    import sacrebleu
    score = sacrebleu.corpus_ter([hypothesis], [[reference]])
    return float(score.score) / 100.0  # sacrebleu retorna em escala 0-100


def compute_metrics_for_pair(es_text: str, pt_text: str,
                              embedder=None, bert_scorer=None) -> dict:
    """Computa todas as métricas main + TER para um par (ES, PT).

    embedder: SentenceTransformer (mpnet multilingual)
    bert_scorer: callable que recebe (cand, ref, lang) e retorna F1
    """
    out = {}

    # length_ratio (sempre — sem deps externas)
    out["length_ratio"] = length_ratio(es_text, pt_text)

    # chrF++ e TER (sacrebleu — sem modelo)
    out["chrf"] = compute_chrf(es_text, pt_text)
    out["ter"] = compute_ter(es_text, pt_text)

    # cosine similarity (precisa do embedder)
    if embedder is not None:
        emb_es = embedder.encode([str(es_text)], convert_to_tensor=True,
                                  show_progress_bar=False)
        emb_pt = embedder.encode([str(pt_text)], convert_to_tensor=True,
                                  show_progress_bar=False)
        # Cosine via produto interno de vetores normalizados
        from sentence_transformers import util
        cos = float(util.cos_sim(emb_es, emb_pt)[0][0].item())
        out["cosine_sim"] = cos

    # BERTScore (precisa do bert_scorer)
    if bert_scorer is not None:
        # bert_scorer retorna (P, R, F1) — pegamos só F1
        p, r, f1 = bert_scorer([str(pt_text)], [str(es_text)])
        out["bertscore_p"] = float(p[0])
        out["bertscore_r"] = float(r[0])
        out["bertscore_f1"] = float(f1[0])

    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None,
                        help="Processar apenas N laudos (smoke/debug)")
    parser.add_argument("--out-csv", default="results/translation/intrinsic_metrics.csv")
    parser.add_argument("--out-summary", default="results/translation/intrinsic_metrics_summary.json")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch para BERTScore")
    args = parser.parse_args()

    # Inputs
    df_pt = pd.read_csv("data/reports_translated_pt.csv").drop_duplicates("report_id", keep="last")
    df_es = pd.read_csv("data/reports_raw_canonical.csv")
    df = df_pt.merge(df_es[["report_id", "report_text_raw"]],
                     on="report_id", suffixes=("_pt", "_es"))
    df = df.rename(columns={"report_text_raw_pt": "pt_text",
                              "report_text_raw_es": "es_text"})

    if args.limit:
        df = df.head(args.limit)

    # Resume
    out_path = Path(args.out_csv)
    if out_path.exists():
        done = set(pd.read_csv(out_path)["report_id"])
        df = df[~df["report_id"].isin(done)]
        print(f"Resume: {len(done)} já feitos, {len(df)} pendentes")
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)

    if len(df) == 0:
        print("Nada a processar")
        return 0

    # Carregar modelos uma única vez
    print("Carregando modelos...")
    from sentence_transformers import SentenceTransformer
    from bert_score import BERTScorer

    embedder = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
    print("  embedder OK (mpnet multilingual)")

    bert_scorer_obj = BERTScorer(model_type="xlm-roberta-large", lang="es",
                                  rescale_with_baseline=False)
    def bert_scorer(cands, refs):
        return bert_scorer_obj.score(cands, refs)
    print("  BERTScorer OK (xlm-roberta-large)")

    print(f"Processando {len(df)} laudos...")
    t_start = time.time()

    # Batch BERTScore para eficiência (resto é per-laudo)
    rows: list[dict] = []
    write_every = 50

    for i, row in enumerate(df.itertuples(index=False), 1):
        es = row.es_text
        pt = row.pt_text
        try:
            metrics = compute_metrics_for_pair(es, pt, embedder, bert_scorer)
        except Exception as e:
            print(f"  [{i}/{len(df)}] {row.report_id} ERRO: {type(e).__name__}: {str(e)[:100]}")
            continue

        rec = {"report_id": row.report_id, **metrics}
        rows.append(rec)

        if i % write_every == 0 or i == len(df):
            mode = "a" if out_path.exists() else "w"
            header = not out_path.exists()
            pd.DataFrame(rows).to_csv(out_path, mode=mode, header=header, index=False)
            elapsed = time.time() - t_start
            rate = i / elapsed if elapsed > 0 else 0
            print(f"  [{i}/{len(df)}] flushed; rate={rate:.2f}/s")
            rows = []

    elapsed = time.time() - t_start
    print(f"\nT15 completo em {elapsed/60:.1f} min")
    print(f"CSV: {out_path}")

    # Build summary
    print("Construindo summary...")
    df_csv = pd.read_csv(out_path)
    summary = build_summary(df_csv, args.out_summary)
    print(f"Summary salvo em: {args.out_summary}")
    print(json.dumps({k: v for k, v in summary.items()
                       if not isinstance(v, dict)}, indent=2))
    return 0


def build_summary(df: pd.DataFrame, out_path: str) -> dict:
    """Agrega métricas para consumo direto pelo notebook (T23)."""
    def stats(col: str) -> dict:
        s = df[col].dropna()
        if len(s) == 0:
            return {}
        return {
            "median":   round(float(s.median()), 4),
            "mean":     round(float(s.mean()), 4),
            "p5":       round(float(s.quantile(0.05)), 4),
            "p95":      round(float(s.quantile(0.95)), 4),
            "min":      round(float(s.min()), 4),
            "max":      round(float(s.max()), 4),
            "n":        int(len(s)),
        }

    summary = {
        "n_records":       int(len(df)),
        "metrics_main": {
            "bertscore_f1":    stats("bertscore_f1") if "bertscore_f1" in df.columns else None,
            "chrf":            stats("chrf"),
            "cosine_sim":      stats("cosine_sim") if "cosine_sim" in df.columns else None,
            "length_ratio":    stats("length_ratio"),
        },
        "metrics_appendix": {
            "ter":             stats("ter"),
        },
        "bleu_excluded": "decisão T15 — não defensável para par ES↔PT (Freitag 2022)",
        "bertscore_f1_median":   None,
        "lexical_acceptable_rate": None,  # não vem aqui — vem de T17
    }

    # Headlines para executive summary (T23)
    if "bertscore_f1" in df.columns:
        summary["bertscore_f1_median"] = round(float(df["bertscore_f1"].median()), 4)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return summary


if __name__ == "__main__":
    sys.exit(main())
