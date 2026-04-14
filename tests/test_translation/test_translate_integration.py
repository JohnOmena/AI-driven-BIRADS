"""Integration test for the translation pipeline with mocked LLM APIs."""

import json
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import yaml

from src.translation.translate import run_translation


def _create_test_fixtures(tmp_dir: Path) -> dict:
    """Create minimal test data and configs for integration test."""
    reports = pd.DataFrame({
        "report_id": ["RPT_001", "RPT_002"],
        "report_text_raw": [
            "Se observa un nodulo en mama derecha.",
            "No se observan calcificaciones sospechosas.",
        ],
        "birads_label": [2, 1],
    })
    source_path = tmp_dir / "test_reports.csv"
    reports.to_csv(source_path, index=False, encoding="utf-8")

    glossary = {
        "metadata": {"source": "test"},
        "terms": {
            "anatomy": [{"es": "mama derecha", "pt": "mama direita"}],
            "findings": [{"es": "nodulo", "pt": "nodulo"}],
        },
    }
    glossary_path = tmp_dir / "glossary.json"
    with open(glossary_path, "w", encoding="utf-8") as f:
        json.dump(glossary, f, ensure_ascii=False)

    models_yaml = {
        "models": {
            "gemini-2.5-flash": {
                "provider": "google",
                "model_id": "gemini-2.5-flash",
                "env_key": "GOOGLE_API_KEY",
                "cost_per_1m_input": 0.15,
                "cost_per_1m_output": 0.60,
                "cost_limit_usd": 50.0,
            },
            "deepseek-v3": {
                "provider": "openai_compatible",
                "model_id": "deepseek-chat",
                "api_base": "https://api.deepseek.com/v1",
                "env_key": "DEEPSEEK_API_KEY",
                "cost_per_1m_input": 0.07,
                "cost_per_1m_output": 1.10,
                "cost_limit_usd": 50.0,
            },
        },
    }
    models_path = tmp_dir / "models.yaml"
    with open(models_path, "w", encoding="utf-8") as f:
        yaml.dump(models_yaml, f)

    config = {
        "source_path": str(source_path),
        "output_path": str(tmp_dir / "translated.csv"),
        "translations_path": str(tmp_dir / "translations.csv"),
        "audit_path": str(tmp_dir / "results" / "audit_results.json"),
        "stats_path": str(tmp_dir / "results" / "stats.json"),
        "llm_translator": "gemini-2.5-flash",
        "llm_auditor": "deepseek-v3",
        "temperature": 0,
        "birads_glossary_path": str(glossary_path),
        "models_config_path": str(models_path),
        "batch_size": 10,
        "max_retries": 1,
        "resume": False,
    }
    return config


# Mock the translator to return Portuguese text, and the auditor to return approval JSON
def _mock_generate(prompt, temperature=0):
    """Mock generate that returns translation or audit depending on prompt content."""
    if "RESULTADO DA AUDITORIA" in prompt:
        return '{"aprovado": true, "score": 9, "inconsistencias": []}'
    return "Observa-se um nodulo na mama direita."


@patch("src.translation.client.LLMClient.generate", side_effect=_mock_generate)
@patch("src.translation.validate.compute_similarity", return_value=0.95)
def test_pipeline_produces_output_files(mock_similarity, mock_generate, tmp_path):
    """Full pipeline with mocked APIs produces expected output files."""
    config = _create_test_fixtures(tmp_path)

    with patch.dict("os.environ", {
        "GOOGLE_API_KEY": "fake",
        "DEEPSEEK_API_KEY": "fake",
    }):
        run_translation(config)

    # Check output files exist
    assert Path(config["output_path"]).exists()
    assert Path(config["audit_path"]).exists()
    assert Path(config["stats_path"]).exists()

    # Check translated CSV has correct structure
    translated = pd.read_csv(config["output_path"], encoding="utf-8")
    assert len(translated) == 2
    assert "report_id" in translated.columns
    assert "report_text_raw" in translated.columns
    assert "birads_label" in translated.columns

    # Check stats
    with open(config["stats_path"], encoding="utf-8") as f:
        stats = json.load(f)
    assert stats["total_reports"] == 2
    assert stats["translated_successfully"] == 2
    assert stats["audit_approved"] == 2

    # Check audit results
    with open(config["audit_path"], encoding="utf-8") as f:
        audits = json.load(f)
    assert len(audits) == 2
    assert all(a["audit"]["aprovado"] for a in audits)
