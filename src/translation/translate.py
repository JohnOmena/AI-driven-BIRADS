"""Main translation pipeline: ES→PT with dual-LLM validation.

Usage:
    python -m src.translation.translate
    python -m src.translation.translate --llm-primary gemini-2.0-flash --batch-size 5
"""

import json
import time
from pathlib import Path

import pandas as pd
import yaml
from tqdm import tqdm

from src.translation.config import CONFIG, parse_args
from src.translation.glossary import load_glossary, format_glossary_for_prompt
from src.translation.prompt import build_translation_prompt
from src.translation.client import create_client, LLMClient
from src.translation.validate import (
    compute_similarity,
    check_birads_terms_match,
    classify_divergence,
)


def load_models_config(config: dict) -> dict:
    """Load models.yaml config."""
    with open(config["models_config_path"], encoding="utf-8") as f:
        return yaml.safe_load(f)


def translate_report(
    report_text: str,
    client: LLMClient,
    prompt_template_args: dict,
    temperature: float,
    max_retries: int = 3,
) -> str | None:
    """Translate a single report with retry logic.

    Returns the translated text, or None if all retries fail.
    """
    glossary_text = prompt_template_args["glossary_text"]
    prompt = build_translation_prompt(report_text, glossary_text)

    for attempt in range(max_retries):
        try:
            response = client.generate(prompt, temperature=temperature)
            if response and response.strip():
                return response.strip()
        except RuntimeError:
            raise  # Cost limit — don't retry
        except Exception as e:
            print(f"  Attempt {attempt + 1}/{max_retries} failed for {client.name}: {e}")
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


def save_translations(translations: list[dict], output_path: str, append: bool = False) -> None:
    """Save translations to CSV."""
    df = pd.DataFrame(translations)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if append and path.exists():
        existing = pd.read_csv(path, encoding="utf-8")
        df = pd.concat([existing, df], ignore_index=True)

    df.to_csv(path, index=False, encoding="utf-8")


def run_translation(config: dict) -> None:
    """Run the full translation pipeline."""
    print("=" * 60)
    print("Translation Pipeline ES → PT")
    print("=" * 60)

    # Load data
    print(f"\nLoading reports from {config['source_path']}...")
    df = pd.read_csv(config["source_path"], encoding="utf-8")
    print(f"  Total reports: {len(df)}")

    # Load glossary
    print(f"Loading glossary from {config['birads_glossary_path']}...")
    glossary_pairs = load_glossary(config["birads_glossary_path"])
    glossary_text = format_glossary_for_prompt(glossary_pairs)
    glossary_pt_terms = [pt for _, pt in glossary_pairs]
    print(f"  Loaded {len(glossary_pairs)} term pairs")

    # Create LLM clients
    models_config = load_models_config(config)
    primary_name = config["llm_primary"]
    secondary_name = config["llm_secondary"]

    print(f"\nCreating clients: {primary_name} (primary), {secondary_name} (secondary)")
    client_primary = create_client(primary_name, models_config["models"][primary_name])
    client_secondary = create_client(secondary_name, models_config["models"][secondary_name])

    prompt_args = {"glossary_text": glossary_text}

    # Check resume
    done_primary = load_progress(config["output_primary_path"]) if config["resume"] else set()
    done_secondary = load_progress(config["output_secondary_path"]) if config["resume"] else set()
    done_both = done_primary & done_secondary
    if done_both:
        print(f"  Resuming: {len(done_both)} reports already translated")

    # Translate
    results_primary = []
    results_secondary = []
    validation_results = []

    pending = df[~df["report_id"].astype(str).isin(done_both)]
    print(f"\n  Reports to translate: {len(pending)}")
    print(f"  Temperature: {config['temperature']}")
    print()

    for idx, row in tqdm(pending.iterrows(), total=len(pending), desc="Translating"):
        report_id = str(row["report_id"])
        report_text = row["report_text_raw"]

        # Primary translation
        translation_1 = translate_report(
            report_text, client_primary, prompt_args,
            config["temperature"], config["max_retries"],
        )

        # Secondary translation
        translation_2 = translate_report(
            report_text, client_secondary, prompt_args,
            config["temperature"], config["max_retries"],
        )

        results_primary.append({
            "report_id": report_id,
            "report_text_translated": translation_1 or "",
            "translation_success": translation_1 is not None,
        })
        results_secondary.append({
            "report_id": report_id,
            "report_text_translated": translation_2 or "",
            "translation_success": translation_2 is not None,
        })

        # Validate if both succeeded
        if translation_1 and translation_2:
            similarity = compute_similarity(translation_1, translation_2)
            terms_check = check_birads_terms_match(
                translation_1, translation_2, glossary_pt_terms,
            )
            status = classify_divergence(
                similarity, terms_check["match_ratio"], config["similarity_threshold"],
            )
            validation_results.append({
                "report_id": report_id,
                "similarity": round(similarity, 4),
                "term_match_ratio": round(terms_check["match_ratio"], 4),
                "mismatched_terms": terms_check["mismatched_terms"],
                "status": status,
            })

        # Save periodically
        if (len(results_primary) % config["batch_size"] == 0) or (idx == pending.index[-1]):
            save_translations(results_primary, config["output_primary_path"], append=bool(done_both))
            save_translations(results_secondary, config["output_secondary_path"], append=bool(done_both))
            done_both.update(r["report_id"] for r in results_primary)
            results_primary = []
            results_secondary = []

    # Build final output: use primary translation as reference
    print("\nBuilding final translated dataset...")
    primary_df = pd.read_csv(config["output_primary_path"], encoding="utf-8")
    original_df = pd.read_csv(config["source_path"], encoding="utf-8")

    final_df = original_df[["report_id", "birads_label"]].merge(
        primary_df[["report_id", "report_text_translated"]],
        on="report_id",
        how="inner",
    )
    final_df = final_df.rename(columns={"report_text_translated": "report_text_raw"})
    final_df.to_csv(config["output_path"], index=False, encoding="utf-8")
    print(f"  Saved {len(final_df)} translated reports to {config['output_path']}")

    # Save validation results
    results_dir = Path(config["divergences_path"]).parent
    results_dir.mkdir(parents=True, exist_ok=True)

    divergences = [v for v in validation_results if v["status"] == "review"]
    with open(config["divergences_path"], "w", encoding="utf-8") as f:
        json.dump(divergences, f, ensure_ascii=False, indent=2)
    print(f"  Divergences flagged for review: {len(divergences)}")

    # Save stats
    total_validated = len(validation_results)
    ok_count = sum(1 for v in validation_results if v["status"] == "ok")
    avg_similarity = (
        sum(v["similarity"] for v in validation_results) / total_validated
        if total_validated > 0 else 0
    )
    stats = {
        "total_reports": len(df),
        "translated_reports": len(final_df),
        "validated_reports": total_validated,
        "ok_count": ok_count,
        "review_count": len(divergences),
        "avg_similarity": round(avg_similarity, 4),
        "primary_model": primary_name,
        "secondary_model": secondary_name,
        "primary_usage": client_primary.get_usage_report(),
        "secondary_usage": client_secondary.get_usage_report(),
    }
    with open(config["stats_path"], "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    print(f"  Stats saved to {config['stats_path']}")

    # Print summary
    print("\n" + "=" * 60)
    print("TRANSLATION SUMMARY")
    print("=" * 60)
    print(f"  Total translated: {len(final_df)}/{len(df)}")
    print(f"  Avg similarity:   {avg_similarity:.4f}")
    print(f"  OK:               {ok_count}")
    print(f"  Needs review:     {len(divergences)}")
    print(f"  Primary cost:     ${client_primary.total_cost_usd:.4f}")
    print(f"  Secondary cost:   ${client_secondary.total_cost_usd:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    config = parse_args()
    run_translation(config)
