import pytest
from src.llm_client import LLMClient

@pytest.mark.asyncio
async def test_llm_client_initialization():
    """Test LLM client initializes with OpenRouter"""
    client = LLMClient(
        api_key="test_key",
        primary_model="deepseek/deepseek-chat",
        fallback_model="anthropic/claude-3.5-sonnet"
    )

    assert client.api_key == "test_key"
    assert client.primary_model == "deepseek/deepseek-chat"
    assert client.fallback_model == "anthropic/claude-3.5-sonnet"
