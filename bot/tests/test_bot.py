import pytest
from unittest.mock import AsyncMock, MagicMock
from src.bot import ProductivityBot

@pytest.mark.asyncio
async def test_bot_initialization():
    """Test that bot initializes correctly"""
    bot = ProductivityBot(
        token="test_token",
        db_path=":memory:",
        vault_path="/tmp/vault"
    )

    assert bot.token == "test_token"
    assert bot.db_path == ":memory:"
    assert bot.vault_path == "/tmp/vault"

@pytest.mark.asyncio
async def test_start_command():
    """Test /start command handler"""
    bot = ProductivityBot(
        token="test_token",
        db_path=":memory:",
        vault_path="/tmp/vault"
    )

    # Mock update and context
    update = MagicMock()
    update.effective_user.first_name = "Test User"
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await bot.cmd_start(update, context)

    # Verify welcome message sent
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Test User" in call_args
    assert "productivity" in call_args.lower()
