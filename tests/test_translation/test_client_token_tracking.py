"""Tests para T14.A — fix de tracking de tokens (thoughts + thinking_budget)."""

from unittest.mock import MagicMock, patch

import pytest

from src.translation.client import LLMClient, create_client


# --- thoughts_token_count somado ao output ---

def test_thoughts_tokens_added_to_output_count():
    """Thoughts cobrados como output e devem ser contados."""
    client = LLMClient(
        name="test", provider="google", model_id="gemini-2.5-flash",
        api_key="fake",
        cost_per_1m_input=0.30, cost_per_1m_output=2.50,
    )

    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 100
    mock_usage.candidates_token_count = 200
    mock_usage.thoughts_token_count = 500
    mock_response = MagicMock()
    mock_response.usage_metadata = mock_usage
    mock_response.text = "translated"

    with patch("google.genai.Client") as MockClient:
        instance = MockClient.return_value
        instance.models.generate_content.return_value = mock_response
        client.generate("hello", temperature=0)

    # input: 100, output: 200 + 500 = 700
    assert client.total_input_tokens == 100
    assert client.total_output_tokens == 700
    assert client.total_thoughts_tokens == 500
    expected_cost = 100 * 0.30 / 1e6 + 700 * 2.50 / 1e6
    assert abs(client.total_cost_usd - expected_cost) < 1e-9


def test_thoughts_absent_handles_zero():
    """Se a API não retornar thoughts_token_count, output é só candidates."""
    client = LLMClient(
        name="test", provider="google", model_id="gemini-2.5-flash",
        api_key="fake", cost_per_1m_input=0.30, cost_per_1m_output=2.50,
    )

    mock_usage = MagicMock(spec=["prompt_token_count", "candidates_token_count"])
    mock_usage.prompt_token_count = 100
    mock_usage.candidates_token_count = 200
    mock_response = MagicMock()
    mock_response.usage_metadata = mock_usage
    mock_response.text = "x"

    with patch("google.genai.Client") as MockClient:
        instance = MockClient.return_value
        instance.models.generate_content.return_value = mock_response
        client.generate("hi", temperature=0)

    # Sem thoughts → 200 output
    assert client.total_output_tokens == 200
    assert client.total_thoughts_tokens == 0


# --- thinking_budget propagado para ThinkingConfig ---

def test_thinking_budget_zero_propagated_to_config():
    """Quando thinking_budget=0, ThinkingConfig é passado ao Google SDK."""
    client = LLMClient(
        name="test", provider="google", model_id="gemini-2.5-flash",
        api_key="fake", thinking_budget=0,
    )

    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 10
    mock_usage.candidates_token_count = 5
    mock_usage.thoughts_token_count = 0
    mock_response = MagicMock()
    mock_response.usage_metadata = mock_usage
    mock_response.text = "ok"

    with patch("google.genai.Client") as MockClient, \
         patch("google.genai.types.ThinkingConfig") as MockTC, \
         patch("google.genai.types.GenerateContentConfig") as MockGCC:
        instance = MockClient.return_value
        instance.models.generate_content.return_value = mock_response

        client.generate("hi", temperature=0)

        MockTC.assert_called_once_with(thinking_budget=0)


def test_thinking_budget_none_no_thinking_config():
    """thinking_budget=None: ThinkingConfig NÃO deve ser instanciada."""
    client = LLMClient(
        name="test", provider="google", model_id="gemini-2.5-flash",
        api_key="fake", thinking_budget=None,
    )

    mock_usage = MagicMock()
    mock_usage.prompt_token_count = 1
    mock_usage.candidates_token_count = 1
    mock_usage.thoughts_token_count = 0
    mock_response = MagicMock()
    mock_response.usage_metadata = mock_usage
    mock_response.text = "x"

    with patch("google.genai.Client") as MockClient, \
         patch("google.genai.types.ThinkingConfig") as MockTC:
        instance = MockClient.return_value
        instance.models.generate_content.return_value = mock_response
        client.generate("hi", temperature=0)
        MockTC.assert_not_called()


# --- create_client lê thinking_budget do yaml ---

def test_create_client_reads_thinking_budget():
    config = {
        "provider": "google", "model_id": "gemini-2.5-flash",
        "env_key": "GOOGLE_API_KEY",
        "cost_per_1m_input": 0.30, "cost_per_1m_output": 2.50,
        "thinking_budget": 0,
    }
    client = create_client("test", config)
    assert client.thinking_budget == 0


def test_create_client_no_thinking_budget_default_none():
    config = {
        "provider": "google", "model_id": "gemini-2.5-flash",
        "env_key": "GOOGLE_API_KEY",
        "cost_per_1m_input": 0.30, "cost_per_1m_output": 2.50,
    }
    client = create_client("test", config)
    assert client.thinking_budget is None


# --- Recálculo retroativo Phase A ---

def test_phase_a_retroactive_estimate():
    """Documenta o cálculo retroativo do gap real R$160 vs $0.20 reportado.

    Sample da última sessão (517 laudos):
      - input visível:  963525 tokens
      - output visível: 92795 tokens (sem thoughts)
      - reportado em stats.json: $0.2002 (com preços antigos $0.15/$0.60)

    Recálculo apenas com preços corretos $0.30/$2.50 (sem thoughts):
      input:  963525 * 0.30 / 1e6  = 0.289
      output:  92795 * 2.50 / 1e6  = 0.232
      total:                         0.521
    """
    in_tok_517 = 963525
    out_tok_517 = 92795
    cost_no_thoughts = (
        in_tok_517 * 0.30 / 1_000_000 + out_tok_517 * 2.50 / 1_000_000
    )
    assert abs(cost_no_thoughts - 0.5210) < 0.001

    # Multiplicador escopo (517 -> 4357 laudos)
    multiplier = 4357 / 517
    cost_4357_no_thoughts = cost_no_thoughts * multiplier
    # Esperado ~$4.40 sem thoughts
    assert 4.0 < cost_4357_no_thoughts < 5.0
