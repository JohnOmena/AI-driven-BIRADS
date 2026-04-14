"""Translation module configuration.

Usage:
    - Edit CONFIG dict directly for default values
    - Override via CLI: python -m src.translation.translate --llm-primary gemini-2.0-flash
"""

import argparse
from pathlib import Path

CONFIG = {
    "source_path": "data/reports_raw_canonical.csv",
    "output_path": "data/reports_translated_pt.csv",
    "output_primary_path": "results/translation/translations_primary.csv",
    "output_secondary_path": "results/translation/translations_secondary.csv",
    "divergences_path": "results/translation/divergences.json",
    "stats_path": "results/translation/stats.json",
    "llm_primary": "gemini-2.0-flash",
    "llm_secondary": "deepseek-v3",
    "similarity_threshold": 0.95,
    "temperature": 0,
    "birads_glossary_path": "configs/birads_glossary_es_pt.json",
    "models_config_path": "configs/models.yaml",
    "batch_size": 10,
    "max_retries": 3,
    "resume": True,
}


def parse_args() -> dict:
    """Parse CLI arguments and merge with CONFIG defaults."""
    parser = argparse.ArgumentParser(description="Translate ES reports to PT")
    parser.add_argument("--source-path", type=str, help="Path to source CSV")
    parser.add_argument("--output-path", type=str, help="Path to output CSV")
    parser.add_argument("--llm-primary", type=str, help="Primary LLM for translation")
    parser.add_argument("--llm-secondary", type=str, help="Secondary LLM for validation")
    parser.add_argument("--similarity-threshold", type=float, help="Min similarity threshold")
    parser.add_argument("--temperature", type=float, help="LLM temperature")
    parser.add_argument("--batch-size", type=int, help="Reports per batch")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh, ignore previous progress")

    args = parser.parse_args()
    config = CONFIG.copy()

    # Override CONFIG with any provided CLI args
    if args.source_path:
        config["source_path"] = args.source_path
    if args.output_path:
        config["output_path"] = args.output_path
    if args.llm_primary:
        config["llm_primary"] = args.llm_primary
    if args.llm_secondary:
        config["llm_secondary"] = args.llm_secondary
    if args.similarity_threshold is not None:
        config["similarity_threshold"] = args.similarity_threshold
    if args.temperature is not None:
        config["temperature"] = args.temperature
    if args.batch_size:
        config["batch_size"] = args.batch_size
    if args.no_resume:
        config["resume"] = False

    return config
