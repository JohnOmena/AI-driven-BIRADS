"""Main translation pipeline: ES->PT with Gemini translation + DeepSeek audit.

Architecture:
    1. Gemini 2.5 Flash translates each report ES->PT-BR
    2. DeepSeek V3 audits the translation quality (fidelity, lexicon, completeness)
    3. Semantic similarity + BI-RADS term check provide additional metrics

Usage:
    python -m src.translation.translate
    python -m src.translation.translate --llm-translator gemini-2.5-flash --batch-size 5
"""

import json
import time
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv
from tqdm import tqdm

from src.translation.config import CONFIG, parse_args
from src.translation.glossary import load_glossary, format_glossary_for_prompt
from src.translation.prompt import build_translation_prompt, build_audit_prompt, build_correction_prompt
from src.translation.client import create_client, LLMClient
from src.translation.validate import (
    compute_similarity,
    check_birads_terms_preserved,
    parse_audit_response,
    classify_translation,
    postprocess_translation,
)


def load_models_config(config: dict) -> dict:
    """Load models.yaml config."""
    with open(config["models_config_path"], encoding="utf-8") as f:
        return yaml.safe_load(f)


def translate_report(
    report_text: str,
    client: LLMClient,
    glossary_text: str,
    temperature: float,
    max_retries: int = 3,
) -> str | None:
    """Translate a single report with retry logic.

    Returns the translated text, or None if all retries fail.
    """
    prompt = build_translation_prompt(report_text, glossary_text)

    for attempt in range(max_retries):
        try:
            response = client.generate(prompt, temperature=temperature)
            if response and response.strip():
                return response.strip()
        except RuntimeError:
            raise  # Cost limit - don't retry
        except Exception as e:
            print(f"  Attempt {attempt + 1}/{max_retries} failed for {client.name}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None


def correct_translation(
    original_text: str,
    translated_text: str,
    inconsistencies: list[dict],
    client: LLMClient,
    glossary_text: str,
    temperature: float,
    max_retries: int = 3,
) -> str | None:
    """Ask the translator to fix specific issues found by the auditor.

    Returns corrected translation, or None if all retries fail.
    """
    prompt = build_correction_prompt(
        original_text, translated_text, inconsistencies, glossary_text,
    )

    for attempt in range(max_retries):
        try:
            response = client.generate(prompt, temperature=temperature)
            if response and response.strip():
                return response.strip()
        except RuntimeError:
            raise
        except Exception as e:
            print(f"  Correction attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None


def audit_report(
    original_text: str,
    translated_text: str,
    client: LLMClient,
    glossary_text: str,
    temperature: float,
    max_retries: int = 3,
) -> dict | None:
    """Audit a translation using the auditor LLM.

    Returns parsed audit dict, or None if all retries fail.
    """
    prompt = build_audit_prompt(original_text, translated_text, glossary_text)

    for attempt in range(max_retries):
        try:
            response = client.generate(prompt, temperature=temperature)
            if response and response.strip():
                raw_text = response.strip()
                parsed = parse_audit_response(raw_text)
                parsed["_raw_response"] = raw_text
                return parsed
        except RuntimeError:
            raise  # Cost limit - don't retry
        except Exception as e:
            print(f"  Audit attempt {attempt + 1}/{max_retries} failed for {client.name}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return None


def load_progress(output_path: str) -> set[str]:
    """Load already-translated report IDs for resume capability."""
    path = Path(output_path)
    if path.exists():
        df = pd.read_csv(path, encoding="utf-8")
        return set(df["report_id"].astype(str))
    return set()


def save_batch(records: list[dict], output_path: str, append: bool = False) -> None:
    """Save a batch of records to CSV."""
    df = pd.DataFrame(records)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if append and path.exists():
        existing = pd.read_csv(path, encoding="utf-8")
        df = pd.concat([existing, df], ignore_index=True)

    df.to_csv(path, index=False, encoding="utf-8")


def run_translation(config: dict) -> None:
    """Run the full translation pipeline: translate + audit."""
    print("=" * 60)
    print("Translation Pipeline ES -> PT-BR")
    print("Translator: {} | Auditor: {}".format(config["llm_translator"], config["llm_auditor"]))
    print("=" * 60)

    # Load data
    print(f"\nLoading reports from {config['source_path']}...")
    df = pd.read_csv(config["source_path"], encoding="utf-8")
    print(f"  Total reports: {len(df)}")

    # Load glossary
    print(f"Loading glossary from {config['birads_glossary_path']}...")
    glossary_pairs = load_glossary(config["birads_glossary_path"])
    glossary_text = format_glossary_for_prompt(glossary_pairs)
    print(f"  Loaded {len(glossary_pairs)} term pairs")

    # Create LLM clients
    models_config = load_models_config(config)
    translator_name = config["llm_translator"]
    auditor_name = config["llm_auditor"]

    client_translator = create_client(translator_name, models_config["models"][translator_name])
    client_auditor = create_client(auditor_name, models_config["models"][auditor_name])

    # Check resume
    done_ids = load_progress(config["translations_path"]) if config["resume"] else set()
    if done_ids:
        print(f"  Resuming: {len(done_ids)} reports already processed")

    # Translate + audit
    translation_records = []
    audit_results = []

    pending = df[~df["report_id"].astype(str).isin(done_ids)]
    print(f"\n  Reports to process: {len(pending)}")
    print(f"  Temperature: {config['temperature']}")
    print()

    for idx, row in tqdm(pending.iterrows(), total=len(pending), desc="Translating"):
        report_id = str(row["report_id"])
        report_text = row["report_text_raw"]

        # Step 1: Translate with Gemini
        translation = translate_report(
            report_text, client_translator, glossary_text,
            config["temperature"], config["max_retries"],
        )

        if not translation:
            translation_records.append({
                "report_id": report_id,
                "report_text_translated": "",
                "translation_success": False,
                "audit_approved": False,
                "audit_score": 0,
                "similarity": 0.0,
                "term_match_ratio": 0.0,
                "status": "failed",
            })
            continue

        # Step 2: Post-process translation (fix known Gemini patterns)
        translation, pp_fixes = postprocess_translation(report_text, translation)

        # Step 3: Audit with DeepSeek
        audit = audit_report(
            report_text, translation, client_auditor, glossary_text,
            config["temperature"], config["max_retries"],
        )

        audit_data = audit or {"aprovado": False, "score": 0, "inconsistencias": [{"criterio": "audit_failed", "problema": "Auditor did not respond"}]}
        correction_history = []

        # Step 4: Correction loop — if DeepSeek rejects, ask Gemini to fix
        if not audit_data.get("aprovado") and audit_data.get("inconsistencias"):
            inconsistencies = audit_data["inconsistencias"]
            correction_history.append({
                "round": 0,
                "score": audit_data.get("score", 0),
                "inconsistencias": inconsistencies,
            })

            corrected = correct_translation(
                report_text, translation, inconsistencies,
                client_translator, glossary_text,
                config["temperature"], config["max_retries"],
            )

            if corrected:
                # Post-process the correction too
                corrected, corr_pp_fixes = postprocess_translation(report_text, corrected)
                pp_fixes.extend(corr_pp_fixes)

                # Re-audit the corrected version
                re_audit = audit_report(
                    report_text, corrected, client_auditor, glossary_text,
                    config["temperature"], config["max_retries"],
                )

                if re_audit:
                    re_audit_data = re_audit
                    correction_history.append({
                        "round": 1,
                        "score": re_audit_data.get("score", 0),
                        "inconsistencias": re_audit_data.get("inconsistencias", []),
                    })

                    # Accept correction if it improved
                    if re_audit_data.get("score", 0) >= audit_data.get("score", 0):
                        translation = corrected
                        audit_data = re_audit_data

        # Step 5: Compute additional metrics
        similarity = compute_similarity(report_text, translation)
        terms_check = check_birads_terms_preserved(report_text, translation, glossary_pairs)

        # Step 6: Classify
        status = classify_translation(audit_data, similarity, terms_check["match_ratio"])

        translation_records.append({
            "report_id": report_id,
            "report_text_translated": translation,
            "translation_success": True,
            "audit_approved": audit_data.get("aprovado", False),
            "audit_score": audit_data.get("score", 0),
            "similarity": round(similarity, 4),
            "term_match_ratio": round(terms_check["match_ratio"], 4),
            "status": status,
        })

        # Separate raw response for auditability
        raw_response = audit_data.pop("_raw_response", "")

        audit_results.append({
            "report_id": report_id,
            "original_text": report_text,
            "translated_text": translation,
            "audit": audit_data,
            "audit_raw_response": raw_response,
            "postprocess_fixes": pp_fixes,
            "correction_history": correction_history,
            "terms_check": {
                "match_ratio": round(terms_check["match_ratio"], 4),
                "missing_terms": terms_check["missing_terms"],
                "total_expected": terms_check["total_expected"],
            },
            "similarity": round(similarity, 4),
            "status": status,
        })

        # Save periodically
        if (len(translation_records) % config["batch_size"] == 0) or (idx == pending.index[-1]):
            save_batch(translation_records, config["translations_path"], append=bool(done_ids))
            done_ids.update(r["report_id"] for r in translation_records)
            translation_records = []

    # Build final output
    print("\nBuilding final translated dataset...")
    all_translations = pd.read_csv(config["translations_path"], encoding="utf-8")
    original_df = pd.read_csv(config["source_path"], encoding="utf-8")

    successful = all_translations[all_translations["translation_success"] == True]
    final_df = original_df[["report_id", "birads_label"]].merge(
        successful[["report_id", "report_text_translated"]],
        on="report_id",
        how="inner",
    )
    final_df = final_df.rename(columns={"report_text_translated": "report_text_raw"})
    final_df.to_csv(config["output_path"], index=False, encoding="utf-8")
    print(f"  Saved {len(final_df)} translated reports to {config['output_path']}")

    # Save audit results
    results_dir = Path(config["audit_path"]).parent
    results_dir.mkdir(parents=True, exist_ok=True)

    with open(config["audit_path"], "w", encoding="utf-8") as f:
        json.dump(audit_results, f, ensure_ascii=False, indent=2)

    # Compute stats
    total = len(all_translations)
    n_success = int(all_translations["translation_success"].sum())
    n_approved = int(all_translations["audit_approved"].sum()) if "audit_approved" in all_translations.columns else 0
    n_review = len([r for r in audit_results if r["status"] == "review"])
    n_rejected = len([r for r in audit_results if r["status"] == "rejected"])
    avg_score = all_translations["audit_score"].mean() if "audit_score" in all_translations.columns else 0
    avg_similarity = all_translations["similarity"].mean() if "similarity" in all_translations.columns else 0

    stats = {
        "total_reports": len(df),
        "translated_successfully": n_success,
        "audit_approved": n_approved,
        "audit_review": n_review,
        "audit_rejected": n_rejected,
        "avg_audit_score": round(float(avg_score), 2),
        "avg_similarity": round(float(avg_similarity), 4),
        "translator_model": translator_name,
        "auditor_model": auditor_name,
        "translator_usage": client_translator.get_usage_report(),
        "auditor_usage": client_auditor.get_usage_report(),
    }
    with open(config["stats_path"], "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"  Stats saved to {config['stats_path']}")

    # Print summary
    print("\n" + "=" * 60)
    print("TRANSLATION SUMMARY")
    print("=" * 60)
    print(f"  Total:            {len(df)}")
    print(f"  Translated:       {n_success}")
    print(f"  Audit approved:   {n_approved}")
    print(f"  Audit review:     {n_review}")
    print(f"  Audit rejected:   {n_rejected}")
    print(f"  Avg audit score:  {avg_score:.1f}/10")
    print(f"  Avg similarity:   {avg_similarity:.4f}")
    print(f"  Translator cost:  ${client_translator.total_cost_usd:.4f}")
    print(f"  Auditor cost:     ${client_auditor.total_cost_usd:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    load_dotenv()
    config = parse_args()
    run_translation(config)
