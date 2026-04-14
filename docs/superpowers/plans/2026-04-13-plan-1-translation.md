# Plan 1: Translation Module — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Translate the complete Spanish mammography report database (4,357 reports) to Portuguese using two LLMs (Gemini 2.0 Flash + DeepSeek-V3) with cross-validation for fidelity and BI-RADS lexicon preservation.

**Architecture:** A translation script sends each report to two LLMs independently, then a validation script compares both translations using semantic similarity and BI-RADS lexicon checks. Reports with significant divergence are flagged. The final output is a complete Portuguese CSV parallel to the Spanish original.

**Tech Stack:** Python, Google Generative AI SDK (Gemini), OpenAI-compatible SDK (DeepSeek), Sentence Transformers (embeddings for validation), pandas

**Spec:** `docs/superpowers/specs/2026-04-13-birads-classification-pipeline-design.md` — Seção 1

**Depends on:** Plan 0 (project setup) completed

---

## File Structure

```
configs/
├── birads_glossary_es_pt.json          (create)
src/
├── translation/
│   ├── __init__.py                     (exists — empty)
│   ├── config.py                       (create — CONFIG object + CLI)
│   ├── glossary.py                     (create — load/use glossary)
│   ├── prompt.py                       (create — build translation prompt)
│   ├── client.py                       (create — LLM API clients)
│   ├── translate.py                    (create — main translation pipeline)
│   └── validate.py                     (create — compare translations)
tests/
├── test_translation/
│   ├── __init__.py                     (create)
│   ├── test_glossary.py                (create)
│   ├── test_prompt.py                  (create)
│   ├── test_client.py                  (create)
│   ├── test_validate.py               (create)
│   └── test_translate_integration.py   (create)
notebooks/
└── 01_translation_report.ipynb         (create — after pipeline runs)
```

---

### Task 1: Create BI-RADS glossary ES↔PT

**Files:**
- Create: `configs/birads_glossary_es_pt.json`

- [ ] **Step 1: Write the bilingual BI-RADS glossary**

This glossary contains the official BI-RADS terminology that MUST be preserved during translation. Terms are grouped by category.

```json
{
  "metadata": {
    "source": "ACR BI-RADS Atlas, 5th Edition",
    "description": "Bilingual glossary ES↔PT for BI-RADS mammography terminology"
  },
  "terms": {
    "anatomy": [
      {"es": "mama derecha", "pt": "mama direita"},
      {"es": "mama izquierda", "pt": "mama esquerda"},
      {"es": "cuadrante superior externo", "pt": "quadrante superior externo"},
      {"es": "cuadrante superior interno", "pt": "quadrante superior interno"},
      {"es": "cuadrante inferior externo", "pt": "quadrante inferior externo"},
      {"es": "cuadrante inferior interno", "pt": "quadrante inferior interno"},
      {"es": "retroareolar", "pt": "retroareolar"},
      {"es": "prolongación axilar", "pt": "prolongamento axilar"},
      {"es": "región axilar", "pt": "região axilar"},
      {"es": "pezón", "pt": "mamilo"},
      {"es": "mamelón", "pt": "mamilo"},
      {"es": "areola", "pt": "aréola"},
      {"es": "conducto", "pt": "ducto"},
      {"es": "piel", "pt": "pele"},
      {"es": "tejido glandular", "pt": "tecido glandular"},
      {"es": "tejido adiposo", "pt": "tecido adiposo"},
      {"es": "plano posterior", "pt": "plano posterior"},
      {"es": "región pectoaxilar", "pt": "região pectoaxilar"}
    ],
    "findings_mass": [
      {"es": "nódulo", "pt": "nódulo"},
      {"es": "masa", "pt": "massa"},
      {"es": "imagen nodular", "pt": "imagem nodular"},
      {"es": "formación nodular", "pt": "formação nodular"},
      {"es": "lesión nodular", "pt": "lesão nodular"},
      {"es": "asimetría", "pt": "assimetria"},
      {"es": "asimetría focal", "pt": "assimetria focal"},
      {"es": "asimetría global", "pt": "assimetria global"},
      {"es": "distorsión arquitectural", "pt": "distorção arquitetural"},
      {"es": "densidad asimétrica", "pt": "densidade assimétrica"}
    ],
    "findings_calcification": [
      {"es": "calcificación", "pt": "calcificação"},
      {"es": "calcificaciones", "pt": "calcificações"},
      {"es": "microcalcificación", "pt": "microcalcificação"},
      {"es": "microcalcificaciones", "pt": "microcalcificações"},
      {"es": "macrocalcificación", "pt": "macrocalcificação"}
    ],
    "morphology": [
      {"es": "espiculado", "pt": "espiculado"},
      {"es": "espiculada", "pt": "espiculada"},
      {"es": "circunscrito", "pt": "circunscrito"},
      {"es": "circunscrita", "pt": "circunscrita"},
      {"es": "irregular", "pt": "irregular"},
      {"es": "ovalado", "pt": "ovalado"},
      {"es": "ovalada", "pt": "ovalada"},
      {"es": "redondo", "pt": "redondo"},
      {"es": "redonda", "pt": "redonda"},
      {"es": "lobulado", "pt": "lobulado"},
      {"es": "lobulada", "pt": "lobulada"},
      {"es": "microlobulado", "pt": "microlobulado"},
      {"es": "obscurecido", "pt": "obscurecido"},
      {"es": "indistinto", "pt": "indistinto"},
      {"es": "isodenso", "pt": "isodenso"},
      {"es": "isodensos", "pt": "isodensos"},
      {"es": "hipodenso", "pt": "hipodenso"},
      {"es": "hiperdenso", "pt": "hiperdenso"},
      {"es": "heterogéneo", "pt": "heterogêneo"},
      {"es": "homogéneo", "pt": "homogêneo"},
      {"es": "pleomórfico", "pt": "pleomórfico"},
      {"es": "amorfo", "pt": "amorfo"},
      {"es": "puntiforme", "pt": "puntiforme"},
      {"es": "lineal fino", "pt": "linear fino"},
      {"es": "ramificado", "pt": "ramificado"}
    ],
    "distribution": [
      {"es": "agrupada", "pt": "agrupada"},
      {"es": "segmentaria", "pt": "segmentar"},
      {"es": "lineal", "pt": "linear"},
      {"es": "regional", "pt": "regional"},
      {"es": "difusa", "pt": "difusa"},
      {"es": "ductal", "pt": "ductal"}
    ],
    "density": [
      {"es": "composición mamaria", "pt": "composição mamária"},
      {"es": "predominantemente adiposa", "pt": "predominantemente adiposa"},
      {"es": "densidades fibroglandulares dispersas", "pt": "densidades fibroglandulares dispersas"},
      {"es": "heterogéneamente densa", "pt": "heterogeneamente densa"},
      {"es": "extremadamente densa", "pt": "extremamente densa"},
      {"es": "tipo A", "pt": "tipo A"},
      {"es": "tipo B", "pt": "tipo B"},
      {"es": "tipo C", "pt": "tipo C"},
      {"es": "tipo D", "pt": "tipo D"}
    ],
    "assessment": [
      {"es": "BI-RADS", "pt": "BI-RADS"},
      {"es": "benigno", "pt": "benigno"},
      {"es": "benigna", "pt": "benigna"},
      {"es": "maligno", "pt": "maligno"},
      {"es": "maligna", "pt": "maligna"},
      {"es": "sospechoso", "pt": "suspeito"},
      {"es": "sospechosa", "pt": "suspeita"},
      {"es": "probablemente benigno", "pt": "provavelmente benigno"},
      {"es": "hallazgo", "pt": "achado"},
      {"es": "hallazgos", "pt": "achados"}
    ],
    "procedure": [
      {"es": "mamografía", "pt": "mamografia"},
      {"es": "ecografía", "pt": "ecografia"},
      {"es": "ultrasonido", "pt": "ultrassonografia"},
      {"es": "biopsia", "pt": "biópsia"},
      {"es": "incidencia", "pt": "incidência"},
      {"es": "cráneo-caudal", "pt": "craniocaudal"},
      {"es": "medio lateral oblicua", "pt": "médio-lateral oblíqua"},
      {"es": "prótesis", "pt": "prótese"},
      {"es": "implante", "pt": "implante"},
      {"es": "ganglio linfático", "pt": "linfonodo"},
      {"es": "ganglios linfáticos", "pt": "linfonodos"},
      {"es": "ganglio linfático intramamario", "pt": "linfonodo intramamário"}
    ]
  }
}
```

- [ ] **Step 2: Validate JSON**

Run:
```bash
python -c "import json; d=json.load(open('configs/birads_glossary_es_pt.json', encoding='utf-8')); total=sum(len(v) for v in d['terms'].values()); print(f'Valid JSON: {len(d[\"terms\"])} categories, {total} term pairs')"
```
Expected: `Valid JSON: 8 categories, ~80 term pairs`

- [ ] **Step 3: Commit**

Run:
```bash
git add configs/birads_glossary_es_pt.json
git commit -m "feat: add bilingual BI-RADS glossary ES↔PT"
```

---

### Task 2: Create translation config module

**Files:**
- Create: `src/translation/config.py`
- Test: `tests/test_translation/test_config.py` (deferred — tested implicitly)

- [ ] **Step 1: Write config.py with CONFIG object + argparse CLI**

```python
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
```

- [ ] **Step 2: Commit**

Run:
```bash
git add src/translation/config.py
git commit -m "feat(translation): add config module with CLI + object pattern"
```

---

### Task 3: Create glossary loader

**Files:**
- Create: `src/translation/glossary.py`
- Create: `tests/test_translation/__init__.py`
- Create: `tests/test_translation/test_glossary.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for glossary loading and formatting."""

import json
import tempfile
from pathlib import Path

from src.translation.glossary import load_glossary, format_glossary_for_prompt


def test_load_glossary_returns_term_pairs():
    """Loading the glossary returns a flat list of (es, pt) term pairs."""
    glossary_data = {
        "metadata": {"source": "test"},
        "terms": {
            "anatomy": [
                {"es": "mama derecha", "pt": "mama direita"},
                {"es": "mama izquierda", "pt": "mama esquerda"},
            ],
            "morphology": [
                {"es": "espiculado", "pt": "espiculado"},
            ],
        },
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(glossary_data, f, ensure_ascii=False)
        tmp_path = f.name

    pairs = load_glossary(tmp_path)
    assert len(pairs) == 3
    assert ("mama derecha", "mama direita") in pairs
    assert ("espiculado", "espiculado") in pairs
    Path(tmp_path).unlink()


def test_format_glossary_for_prompt():
    """Glossary formatted for prompt contains ES→PT mappings."""
    pairs = [
        ("mama derecha", "mama direita"),
        ("calcificación", "calcificação"),
    ]
    text = format_glossary_for_prompt(pairs)
    assert "mama derecha → mama direita" in text
    assert "calcificación → calcificação" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
python -m pytest tests/test_translation/test_glossary.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'src.translation.glossary'`

- [ ] **Step 3: Implement glossary.py**

```python
"""Load and format the BI-RADS glossary for translation prompts."""

import json
from pathlib import Path


def load_glossary(glossary_path: str) -> list[tuple[str, str]]:
    """Load glossary JSON and return flat list of (es, pt) term pairs."""
    with open(glossary_path, encoding="utf-8") as f:
        data = json.load(f)

    pairs = []
    for category_terms in data["terms"].values():
        for entry in category_terms:
            pairs.append((entry["es"], entry["pt"]))
    return pairs


def format_glossary_for_prompt(pairs: list[tuple[str, str]]) -> str:
    """Format term pairs as a readable glossary block for the LLM prompt."""
    lines = ["Glossário de termos BI-RADS (Espanhol → Português):"]
    for es, pt in pairs:
        lines.append(f"  {es} → {pt}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m pytest tests/test_translation/test_glossary.py -v
```
Expected: 2 passed

- [ ] **Step 5: Commit**

Run:
```bash
git add src/translation/glossary.py tests/test_translation/__init__.py tests/test_translation/test_glossary.py
git commit -m "feat(translation): add glossary loader with tests"
```

---

### Task 4: Create translation prompt builder

**Files:**
- Create: `src/translation/prompt.py`
- Create: `tests/test_translation/test_prompt.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for translation prompt construction."""

from src.translation.prompt import build_translation_prompt


def test_prompt_contains_report_text():
    """The prompt must include the original report text."""
    report = "Se observa un nódulo espiculado en mama derecha."
    glossary_text = "mama derecha → mama direita"
    prompt = build_translation_prompt(report, glossary_text)
    assert "Se observa un nódulo espiculado en mama derecha." in prompt


def test_prompt_contains_glossary():
    """The prompt must include the glossary."""
    report = "Texto de ejemplo."
    glossary_text = "mama derecha → mama direita\ncalcificación → calcificação"
    prompt = build_translation_prompt(report, glossary_text)
    assert "mama derecha → mama direita" in prompt
    assert "calcificación → calcificação" in prompt


def test_prompt_contains_fidelity_instructions():
    """The prompt must contain explicit fidelity instructions."""
    report = "Texto."
    glossary_text = ""
    prompt = build_translation_prompt(report, glossary_text)
    # Check for key fidelity instructions
    prompt_lower = prompt.lower()
    assert "fielmente" in prompt_lower or "fiel" in prompt_lower
    assert "não omit" in prompt_lower or "no omit" in prompt_lower or "sem omitir" in prompt_lower


def test_prompt_instructs_birads_preservation():
    """The prompt must instruct to preserve BI-RADS terminology."""
    report = "Texto."
    glossary_text = ""
    prompt = build_translation_prompt(report, glossary_text)
    assert "BI-RADS" in prompt
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
python -m pytest tests/test_translation/test_prompt.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement prompt.py**

```python
"""Build the translation prompt for ES→PT mammography report translation."""


def build_translation_prompt(report_text: str, glossary_text: str) -> str:
    """Build a translation prompt that ensures fidelity and BI-RADS lexicon preservation.

    Args:
        report_text: The original Spanish mammography report.
        glossary_text: Formatted glossary of BI-RADS terms ES→PT.

    Returns:
        Complete prompt string for the LLM.
    """
    prompt = f"""Você é um tradutor médico especializado em radiologia mamária e no sistema BI-RADS.

Sua tarefa é traduzir fielmente o seguinte laudo de mamografia do espanhol para o português.

REGRAS OBRIGATÓRIAS:
1. Traduzir fielmente o texto completo, sem omitir, resumir, interpretar ou adicionar informações.
2. Preservar exatamente a estrutura, formatação, parágrafos e pontuação do texto original.
3. Utilizar OBRIGATORIAMENTE a terminologia oficial BI-RADS em português conforme o glossário abaixo.
4. Não traduzir siglas que são universais (BI-RADS, CSE, CSI, CIE, CII).
5. Manter unidades de medida e valores numéricos exatamente como no original.
6. Retornar APENAS o texto traduzido, sem explicações, comentários ou notas adicionais.

{glossary_text}

LAUDO ORIGINAL (Espanhol):
{report_text}

TRADUÇÃO (Português):"""
    return prompt
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m pytest tests/test_translation/test_prompt.py -v
```
Expected: 4 passed

- [ ] **Step 5: Commit**

Run:
```bash
git add src/translation/prompt.py tests/test_translation/test_prompt.py
git commit -m "feat(translation): add prompt builder with fidelity instructions"
```

---

### Task 5: Create LLM API client wrapper

**Files:**
- Create: `src/translation/client.py`
- Create: `tests/test_translation/test_client.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for LLM client wrapper."""

from unittest.mock import patch, MagicMock
from src.translation.client import LLMClient, create_client


def test_create_client_gemini():
    """create_client returns an LLMClient for gemini provider."""
    model_config = {
        "provider": "google",
        "model_id": "gemini-2.0-flash",
        "env_key": "GOOGLE_API_KEY",
    }
    with patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-key"}):
        client = create_client("gemini-2.0-flash", model_config)
    assert isinstance(client, LLMClient)
    assert client.provider == "google"


def test_create_client_openai_compatible():
    """create_client returns an LLMClient for openai_compatible provider."""
    model_config = {
        "provider": "openai_compatible",
        "model_id": "deepseek-chat",
        "api_base": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
    }
    with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "fake-key"}):
        client = create_client("deepseek-v3", model_config)
    assert isinstance(client, LLMClient)
    assert client.provider == "openai_compatible"


def test_llm_client_tracks_token_usage():
    """LLMClient accumulates token usage across calls."""
    client = LLMClient(
        name="test",
        provider="google",
        model_id="test-model",
        api_key="fake",
    )
    client._update_usage(input_tokens=100, output_tokens=50)
    client._update_usage(input_tokens=200, output_tokens=100)
    assert client.total_input_tokens == 300
    assert client.total_output_tokens == 150
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
python -m pytest tests/test_translation/test_client.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement client.py**

```python
"""LLM API client wrapper supporting multiple providers."""

import os
import time
from dataclasses import dataclass, field


@dataclass
class LLMClient:
    """Unified client for LLM API calls with token tracking."""

    name: str
    provider: str
    model_id: str
    api_key: str
    api_base: str | None = None
    cost_per_1m_input: float = 0.0
    cost_per_1m_output: float = 0.0
    cost_limit_usd: float = 50.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0

    def _update_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Track token usage and cost."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        cost = (
            input_tokens * self.cost_per_1m_input / 1_000_000
            + output_tokens * self.cost_per_1m_output / 1_000_000
        )
        self.total_cost_usd += cost

    def check_cost_limit(self) -> bool:
        """Return True if cost is within limit."""
        return self.total_cost_usd < self.cost_limit_usd

    def generate(self, prompt: str, temperature: float = 0) -> str:
        """Send prompt to LLM and return response text.

        Raises:
            RuntimeError: If cost limit exceeded.
            Exception: On API errors (after retries handled by caller).
        """
        if not self.check_cost_limit():
            raise RuntimeError(
                f"Cost limit reached for {self.name}: "
                f"${self.total_cost_usd:.2f} >= ${self.cost_limit_usd:.2f}"
            )

        if self.provider == "google":
            return self._generate_google(prompt, temperature)
        elif self.provider in ("openai", "openai_compatible", "together"):
            return self._generate_openai(prompt, temperature)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _generate_google(self, prompt: str, temperature: float) -> str:
        """Generate via Google Generative AI SDK."""
        import google.generativeai as genai

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model_id)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=temperature),
        )
        # Track usage
        usage = response.usage_metadata
        self._update_usage(
            input_tokens=usage.prompt_token_count,
            output_tokens=usage.candidates_token_count,
        )
        return response.text

    def _generate_openai(self, prompt: str, temperature: float) -> str:
        """Generate via OpenAI-compatible API."""
        from openai import OpenAI

        client_kwargs = {"api_key": self.api_key}
        if self.api_base:
            client_kwargs["base_url"] = self.api_base

        client = OpenAI(**client_kwargs)
        response = client.chat.completions.create(
            model=self.model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        # Track usage
        usage = response.usage
        self._update_usage(
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
        )
        return response.choices[0].message.content

    def get_usage_report(self) -> dict:
        """Return usage statistics."""
        return {
            "model": self.name,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "cost_limit_usd": self.cost_limit_usd,
        }


def create_client(name: str, model_config: dict) -> LLMClient:
    """Create an LLMClient from model config and environment variables."""
    api_key = os.environ.get(model_config["env_key"], "")
    return LLMClient(
        name=name,
        provider=model_config["provider"],
        model_id=model_config["model_id"],
        api_key=api_key,
        api_base=model_config.get("api_base"),
        cost_per_1m_input=model_config.get("cost_per_1m_input", 0.0),
        cost_per_1m_output=model_config.get("cost_per_1m_output", 0.0),
        cost_limit_usd=model_config.get("cost_limit_usd", 50.0),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m pytest tests/test_translation/test_client.py -v
```
Expected: 3 passed

- [ ] **Step 5: Commit**

Run:
```bash
git add src/translation/client.py tests/test_translation/test_client.py
git commit -m "feat(translation): add LLM client wrapper with token tracking"
```

---

### Task 6: Create translation validation module

**Files:**
- Create: `src/translation/validate.py`
- Create: `tests/test_translation/test_validate.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for translation validation (similarity + BI-RADS lexicon check)."""

from src.translation.validate import (
    check_birads_terms_match,
    classify_divergence,
)


def test_birads_terms_match_identical():
    """Identical translations should have all terms matching."""
    glossary_pt = ["mama direita", "calcificação", "nódulo"]
    text_a = "Observa-se um nódulo na mama direita com calcificação."
    text_b = "Observa-se um nódulo na mama direita com calcificação."
    result = check_birads_terms_match(text_a, text_b, glossary_pt)
    assert result["match_ratio"] == 1.0


def test_birads_terms_match_divergent():
    """Different BI-RADS terms should be flagged."""
    glossary_pt = ["mama direita", "mama esquerda", "nódulo"]
    text_a = "Observa-se um nódulo na mama direita."
    text_b = "Observa-se um nódulo na mama esquerda."
    result = check_birads_terms_match(text_a, text_b, glossary_pt)
    assert result["match_ratio"] < 1.0
    assert len(result["mismatched_terms"]) > 0


def test_classify_divergence_ok():
    """High similarity + high term match = OK."""
    result = classify_divergence(similarity=0.98, term_match_ratio=1.0, threshold=0.95)
    assert result == "ok"


def test_classify_divergence_review():
    """Low similarity = needs review."""
    result = classify_divergence(similarity=0.90, term_match_ratio=1.0, threshold=0.95)
    assert result == "review"


def test_classify_divergence_term_mismatch():
    """High similarity but low term match = needs review."""
    result = classify_divergence(similarity=0.98, term_match_ratio=0.5, threshold=0.95)
    assert result == "review"
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
python -m pytest tests/test_translation/test_validate.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement validate.py**

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
python -m pytest tests/test_translation/test_validate.py -v
```
Expected: 5 passed

- [ ] **Step 5: Commit**

Run:
```bash
git add src/translation/validate.py tests/test_translation/test_validate.py
git commit -m "feat(translation): add validation module (similarity + BI-RADS terms)"
```

---

### Task 7: Create main translation pipeline

**Files:**
- Create: `src/translation/translate.py`
- Modify: `src/translation/__init__.py`

- [ ] **Step 1: Implement translate.py**

```python
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
```

- [ ] **Step 2: Update __init__.py**

```python
"""Translation module: ES→PT mammography report translation with dual-LLM validation."""
```

- [ ] **Step 3: Commit**

Run:
```bash
git add src/translation/translate.py src/translation/__init__.py
git commit -m "feat(translation): add main translation pipeline with resume and validation"
```

---

### Task 8: Create integration test with mocked APIs

**Files:**
- Create: `tests/test_translation/test_translate_integration.py`

- [ ] **Step 1: Write integration test**

```python
"""Integration test for the translation pipeline with mocked LLM APIs."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pandas as pd

from src.translation.translate import run_translation


def _create_test_fixtures(tmp_dir: Path) -> dict:
    """Create minimal test data and configs for integration test."""
    # Minimal CSV with 2 reports
    reports = pd.DataFrame({
        "report_id": ["RPT_001", "RPT_002"],
        "report_text_raw": [
            "Se observa un nódulo en mama derecha.",
            "No se observan calcificaciones sospechosas.",
        ],
        "birads_label": [2, 1],
    })
    source_path = tmp_dir / "test_reports.csv"
    reports.to_csv(source_path, index=False, encoding="utf-8")

    # Minimal glossary
    glossary = {
        "metadata": {"source": "test"},
        "terms": {
            "anatomy": [{"es": "mama derecha", "pt": "mama direita"}],
            "findings": [{"es": "nódulo", "pt": "nódulo"}],
        },
    }
    glossary_path = tmp_dir / "glossary.json"
    with open(glossary_path, "w", encoding="utf-8") as f:
        json.dump(glossary, f, ensure_ascii=False)

    # Minimal models.yaml
    models_yaml = {
        "models": {
            "gemini-2.0-flash": {
                "provider": "google",
                "model_id": "gemini-2.0-flash",
                "env_key": "GOOGLE_API_KEY",
                "cost_per_1m_input": 0.0,
                "cost_per_1m_output": 0.0,
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
    import yaml
    models_path = tmp_dir / "models.yaml"
    with open(models_path, "w", encoding="utf-8") as f:
        yaml.dump(models_yaml, f)

    config = {
        "source_path": str(source_path),
        "output_path": str(tmp_dir / "translated.csv"),
        "output_primary_path": str(tmp_dir / "primary.csv"),
        "output_secondary_path": str(tmp_dir / "secondary.csv"),
        "divergences_path": str(tmp_dir / "results" / "divergences.json"),
        "stats_path": str(tmp_dir / "results" / "stats.json"),
        "llm_primary": "gemini-2.0-flash",
        "llm_secondary": "deepseek-v3",
        "similarity_threshold": 0.95,
        "temperature": 0,
        "birads_glossary_path": str(glossary_path),
        "models_config_path": str(models_path),
        "batch_size": 10,
        "max_retries": 1,
        "resume": False,
    }
    return config


@patch("src.translation.client.LLMClient.generate")
@patch("src.translation.validate.compute_similarity")
def test_pipeline_produces_output_files(mock_similarity, mock_generate, tmp_path):
    """Full pipeline with mocked APIs produces expected output files."""
    config = _create_test_fixtures(tmp_path)

    # Mock LLM responses
    mock_generate.return_value = "Observa-se um nódulo na mama direita."
    mock_similarity.return_value = 0.98

    with patch.dict("os.environ", {
        "GOOGLE_API_KEY": "fake",
        "DEEPSEEK_API_KEY": "fake",
    }):
        run_translation(config)

    # Check output files exist
    assert Path(config["output_path"]).exists()
    assert Path(config["divergences_path"]).exists()
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
    assert stats["translated_reports"] == 2
```

- [ ] **Step 2: Run integration test**

Run:
```bash
python -m pytest tests/test_translation/test_translate_integration.py -v
```
Expected: 1 passed

- [ ] **Step 3: Commit**

Run:
```bash
git add tests/test_translation/test_translate_integration.py
git commit -m "test(translation): add integration test with mocked LLM APIs"
```

---

### Task 9: Run all translation tests

- [ ] **Step 1: Run full test suite**

Run:
```bash
python -m pytest tests/test_translation/ -v
```
Expected: All tests pass (11 total)

- [ ] **Step 2: Commit if any fixes were needed**

---

### Task 10: Test with real APIs (small sample)

**Prerequisites:** API keys configured in `.env` file.

- [ ] **Step 1: Create .env with real API keys**

Create `.env` (NOT tracked by git — already in .gitignore):
```env
GOOGLE_API_KEY=your-real-key
DEEPSEEK_API_KEY=your-real-key
```

- [ ] **Step 2: Create a small test CSV (3 reports)**

Run:
```bash
python -c "
import pandas as pd
df = pd.read_csv('data/reports_raw_canonical.csv', encoding='utf-8', nrows=3)
df.to_csv('data/test_sample_3.csv', index=False, encoding='utf-8')
print(f'Created sample with {len(df)} reports')
"
```

- [ ] **Step 3: Run translation on sample**

Run:
```bash
python -m src.translation.translate --source-path data/test_sample_3.csv --output-path data/test_translated_3.csv --batch-size 3
```

- [ ] **Step 4: Inspect results**

Run:
```bash
python -c "
import pandas as pd
import json

# Check translated reports
df = pd.read_csv('data/test_translated_3.csv', encoding='utf-8')
print('=== Translated Reports ===')
for _, row in df.iterrows():
    print(f'\nID: {row[\"report_id\"]}')
    print(f'Text: {row[\"report_text_raw\"][:200]}...')

# Check stats
with open('results/translation/stats.json', encoding='utf-8') as f:
    stats = json.load(f)
print('\n=== Stats ===')
print(json.dumps(stats, indent=2))
"
```

Verify:
- Translations are in Portuguese
- BI-RADS terminology is preserved
- Stats show similarity scores

- [ ] **Step 5: Clean up test files**

Run:
```bash
rm data/test_sample_3.csv data/test_translated_3.csv
```

- [ ] **Step 6: Commit any fixes from real API testing**

Run:
```bash
git add -u
git commit -m "fix(translation): adjustments from real API testing"
```

---

### Task 11: Run full translation (4,357 reports)

**Note:** This will take significant time and cost. Ensure API keys are configured and cost limits are appropriate.

- [ ] **Step 1: Run full translation**

Run:
```bash
python -m src.translation.translate
```

Monitor progress in console. The pipeline saves periodically and supports resume if interrupted.

- [ ] **Step 2: Verify output**

Run:
```bash
python -c "
import pandas as pd
import json

df_es = pd.read_csv('data/reports_raw_canonical.csv', encoding='utf-8')
df_pt = pd.read_csv('data/reports_translated_pt.csv', encoding='utf-8')
print(f'Original ES: {len(df_es)} reports')
print(f'Translated PT: {len(df_pt)} reports')
print(f'Match: {len(df_es) == len(df_pt)}')

with open('results/translation/stats.json', encoding='utf-8') as f:
    stats = json.load(f)
print(f'Avg similarity: {stats[\"avg_similarity\"]}')
print(f'Needs review: {stats[\"review_count\"]}')
"
```

- [ ] **Step 3: Commit results**

Run:
```bash
git add data/reports_translated_pt.csv results/translation/
git commit -m "data: add complete PT translated dataset (4357 reports)"
```

---

### Task 12: Generate translation report notebook

**Files:**
- Create: `notebooks/01_translation_report.ipynb`

- [ ] **Step 1: Create the notebook**

Create a Jupyter notebook `notebooks/01_translation_report.ipynb` with the following cells:

**Cell 1 (Markdown):**
```markdown
# 01 — Translation Report: ES → PT

**Objetivo:** Traduzir a base completa de laudos de mamografia do espanhol para o português usando dois LLMs (Gemini 2.0 Flash + DeepSeek-V3) com validação cruzada de fidelidade.

**Data de execução:** [data atual]
```

**Cell 2 (Code):**
```python
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df_es = pd.read_csv("../data/reports_raw_canonical.csv", encoding="utf-8")
df_pt = pd.read_csv("../data/reports_translated_pt.csv", encoding="utf-8")

with open("../results/translation/stats.json", encoding="utf-8") as f:
    stats = json.load(f)

with open("../results/translation/divergences.json", encoding="utf-8") as f:
    divergences = json.load(f)

print(f"Reports originais (ES): {len(df_es)}")
print(f"Reports traduzidos (PT): {len(df_pt)}")
print(f"Similaridade média: {stats['avg_similarity']:.4f}")
print(f"OK: {stats['ok_count']}")
print(f"Para revisão: {stats['review_count']}")
```

**Cell 3 (Markdown):**
```markdown
## Distribuição de Similaridade
```

**Cell 4 (Code):**
```python
# Load validation details for histogram
primary = pd.read_csv("../results/translation/translations_primary.csv", encoding="utf-8")
secondary = pd.read_csv("../results/translation/translations_secondary.csv", encoding="utf-8")

# If validation results are available, plot similarity distribution
if divergences or stats["ok_count"] > 0:
    fig, ax = plt.subplots(figsize=(10, 5))
    # Note: full similarity data should be loaded from validation results
    ax.set_xlabel("Cosine Similarity")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of Translation Similarity (Primary vs Secondary LLM)")
    plt.tight_layout()
    plt.show()
```

**Cell 5 (Markdown):**
```markdown
## Exemplos de Traduções
```

**Cell 6 (Code):**
```python
# Show side-by-side examples
for i in range(min(3, len(df_es))):
    report_id = df_es.iloc[i]["report_id"]
    print(f"{'='*60}")
    print(f"Report ID: {report_id}")
    print(f"{'='*60}")
    print(f"\n--- ORIGINAL (ES) ---")
    print(df_es.iloc[i]["report_text_raw"][:500])
    pt_row = df_pt[df_pt["report_id"] == report_id]
    if not pt_row.empty:
        print(f"\n--- TRADUÇÃO (PT) ---")
        print(pt_row.iloc[0]["report_text_raw"][:500])
    print()
```

**Cell 7 (Markdown):**
```markdown
## Custos e Uso de Tokens
```

**Cell 8 (Code):**
```python
print("Primary LLM:")
print(json.dumps(stats["primary_usage"], indent=2))
print("\nSecondary LLM:")
print(json.dumps(stats["secondary_usage"], indent=2))
```

**Cell 9 (Markdown):**
```markdown
## Divergências para Revisão
```

**Cell 10 (Code):**
```python
if divergences:
    div_df = pd.DataFrame(divergences)
    print(f"Total divergências: {len(div_df)}")
    print(f"\nSimilaridade média das divergências: {div_df['similarity'].mean():.4f}")
    print(f"Similaridade mínima: {div_df['similarity'].min():.4f}")
    print("\nPrimeiras 5 divergências:")
    for _, row in div_df.head(5).iterrows():
        print(f"  {row['report_id']}: sim={row['similarity']:.4f}, terms={row['mismatched_terms']}")
else:
    print("Nenhuma divergência encontrada.")
```

**Cell 11 (Markdown):**
```markdown
## Próximos Passos
- [ ] Revisar manualmente os relatórios com divergência
- [ ] Prosseguir para o pré-processamento (filtro de achado único)
```

- [ ] **Step 2: Commit notebook**

Run:
```bash
git add notebooks/01_translation_report.ipynb
git commit -m "docs: add translation report notebook"
```

- [ ] **Step 3: Push all progress**

Run:
```bash
git push
```
