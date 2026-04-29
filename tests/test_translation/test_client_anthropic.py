"""Tests para Anthropic provider no LLMClient — Step 5b."""

from unittest.mock import MagicMock, patch
from src.translation.client import LLMClient, create_client


def test_create_client_anthropic():
    """create_client retorna LLMClient para provider anthropic."""
    model_config = {
        "provider": "anthropic",
        "model_id": "claude-haiku-4-5-20251001",
        "env_key": "HAIKU_API_KEY",
    }
    with patch.dict("os.environ", {"HAIKU_API_KEY": "fake-key"}):
        client = create_client("claude-haiku", model_config)
    assert isinstance(client, LLMClient)
    assert client.provider == "anthropic"
    assert client.api_key == "fake-key"


def test_anthropic_generate_calls_messages_api():
    """provider=anthropic dispatcha para _generate_anthropic e usa messages API."""
    client = LLMClient(
        name="claude-haiku", provider="anthropic",
        model_id="claude-haiku-4-5-20251001",
        api_key="fake",
        cost_per_1m_input=1.00, cost_per_1m_output=5.00,
    )

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="resposta do haiku")]
    mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

    with patch("anthropic.Anthropic") as MockClient:
        instance = MockClient.return_value
        instance.messages.create.return_value = mock_response
        text = client.generate("hello", temperature=0)

    assert text == "resposta do haiku"
    assert client.total_input_tokens == 100
    assert client.total_output_tokens == 50
    expected_cost = 100 * 1.00 / 1e6 + 50 * 5.00 / 1e6
    assert abs(client.total_cost_usd - expected_cost) < 1e-9


def test_anthropic_unknown_provider_still_raises():
    """Regression: providers fora dos suportados ainda raise ValueError."""
    client = LLMClient(name="x", provider="unknown_provider",
                       model_id="x", api_key="x")
    try:
        client.generate("hi", temperature=0)
        assert False, "Esperava ValueError"
    except ValueError as e:
        assert "Unknown provider" in str(e)
