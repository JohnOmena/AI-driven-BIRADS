"""LLM API client wrapper supporting multiple providers."""

import os
import time
from dataclasses import dataclass, field


@dataclass
class LLMClient:
    """Unified client for LLM API calls with token tracking.

    T14.A: tracking de tokens corrigido. Phase A custou ~R$160 (vs $0.20
    reportado) por dois bugs combinados:
      1. `thoughts_token_count` não era contado (Gemini 2.5 Flash thinking ON
         gera tokens internos cobrados como output)
      2. preços yaml desatualizados ($0.15/$0.60 vs reais $0.30/$2.50)

    Fix:
      - Soma `thoughts_token_count` ao output em _generate_google
      - Suporta `thinking_budget` configurável (0 desativa thinking)
      - Preços yaml já atualizados (commit aa17c1d, fora desta branch)
    """

    name: str
    provider: str
    model_id: str
    api_key: str
    api_base: str | None = None
    cost_per_1m_input: float = 0.0
    cost_per_1m_output: float = 0.0
    cost_limit_usd: float = 50.0
    thinking_budget: int | None = None  # T14.A: 0 desativa thinking; None = padrão Google
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_thoughts_tokens: int = 0       # T14.A: campo separado para auditoria
    total_cost_usd: float = 0.0

    _last_cost_alert_usd: float = 0.0

    def _update_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Track token usage and cost. Alerts every $10 spent."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        cost = (
            input_tokens * self.cost_per_1m_input / 1_000_000
            + output_tokens * self.cost_per_1m_output / 1_000_000
        )
        self.total_cost_usd += cost

        # Alert every $10 milestone
        current_milestone = int(self.total_cost_usd / 10) * 10
        if current_milestone > 0 and current_milestone > self._last_cost_alert_usd:
            self._last_cost_alert_usd = current_milestone
            print(f"\n⚠ ALERTA DE CUSTO [{self.name}]: ${self.total_cost_usd:.2f} atingidos (limite: ${self.cost_limit_usd:.2f})")

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
        """Generate via Google Generative AI SDK.

        T14.A:
          - Soma `thoughts_token_count` ao output (cobrado como output)
          - Suporta `thinking_budget` (0 desativa thinking; None = padrão)
        """
        from google import genai

        client = genai.Client(api_key=self.api_key)

        config_kwargs = {"temperature": temperature}
        if self.thinking_budget is not None:
            config_kwargs["thinking_config"] = genai.types.ThinkingConfig(
                thinking_budget=self.thinking_budget
            )

        response = client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=genai.types.GenerateContentConfig(**config_kwargs),
        )
        # T14.A: track all token types — thoughts cobrados como output
        usage = response.usage_metadata
        if usage:
            thoughts = getattr(usage, "thoughts_token_count", 0) or 0
            candidates = usage.candidates_token_count or 0
            self.total_thoughts_tokens += thoughts
            self._update_usage(
                input_tokens=usage.prompt_token_count or 0,
                output_tokens=candidates + thoughts,
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
        if usage:
            self._update_usage(
                input_tokens=usage.prompt_tokens or 0,
                output_tokens=usage.completion_tokens or 0,
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
    """Create an LLMClient from model config and environment variables.

    T14.A: lê `thinking_budget` do yaml (None se ausente).
    """
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
        thinking_budget=model_config.get("thinking_budget"),  # T14.A
    )
