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
        from google import genai

        client = genai.Client(api_key=self.api_key)
        response = client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=genai.types.GenerateContentConfig(temperature=temperature),
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
