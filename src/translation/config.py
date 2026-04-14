"""Translation module configuration.

Usage:
    - Edit CONFIG dict directly for default values
    - Override via CLI: python -m src.translation.translate --llm-translator gemini-2.5-flash
"""

import argparse
from pathlib import Path

CONFIG = {
    "source_path": "data/reports_raw_canonical.csv",
    "output_path": "data/reports_translated_pt.csv",
    "translations_path": "results/translation/translations.csv",
    "audit_path": "results/translation/audit_results.json",
    "stats_path": "results/translation/stats.json",
    "llm_translator": "gemini-2.5-flash",
    "llm_auditor": "deepseek-v3",
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
    parser.add_argument("--llm-translator", type=str, help="LLM for translation (Gemini)")
    parser.add_argument("--llm-auditor", type=str, help="LLM for audit/validation (DeepSeek)")
    parser.add_argument("--temperature", type=float, help="LLM temperature")
    parser.add_argument("--batch-size", type=int, help="Reports per batch")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh, ignore previous progress")

    args = parser.parse_args()
    config = CONFIG.copy()

    if args.source_path:
        config["source_path"] = args.source_path
    if args.output_path:
        config["output_path"] = args.output_path
    if args.llm_translator:
        config["llm_translator"] = args.llm_translator
    if args.llm_auditor:
        config["llm_auditor"] = args.llm_auditor
    if args.temperature is not None:
        config["temperature"] = args.temperature
    if args.batch_size:
        config["batch_size"] = args.batch_size
    if args.no_resume:
        config["resume"] = False

    return config
