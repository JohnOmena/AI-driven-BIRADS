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
