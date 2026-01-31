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

@pytest.mark.asyncio
async def test_bot_with_calendar():
    """Test bot initialization with calendar integration"""
    bot = ProductivityBot(
        token="test_token",
        db_path=":memory:",
        vault_path="/tmp/vault",
        calendar_client_id="test_client_id",
        calendar_client_secret="test_client_secret",
        calendar_refresh_token="test_refresh_token"
    )

    assert bot.calendar is not None
    assert bot.calendar.client_id == "test_client_id"

@pytest.mark.asyncio
async def test_bot_without_calendar():
    """Test bot initialization without calendar integration"""
    bot = ProductivityBot(
        token="test_token",
        db_path=":memory:",
        vault_path="/tmp/vault"
    )

    assert bot.calendar is None

@pytest.mark.asyncio
async def test_schedule_command_without_calendar():
    """Test /schedule command when calendar not configured"""
    bot = ProductivityBot(
        token="test_token",
        db_path=":memory:",
        vault_path="/tmp/vault"
    )

    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = ["task-123"]

    await bot.cmd_schedule(update, context)

    # Verify error message sent
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "not configured" in call_args.lower()
