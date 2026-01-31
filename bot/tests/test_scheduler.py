import pytest
from datetime import datetime, time
from unittest.mock import AsyncMock, MagicMock, patch
from src.scheduler import Scheduler

@pytest.fixture
def mock_bot():
    """Mock bot instance"""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    return bot

def test_scheduler_initialization(mock_bot):
    """Test scheduler initializes correctly"""
    scheduler = Scheduler(
        bot=mock_bot,
        telegram_chat_id=12345,
        timezone="America/New_York"
    )

    assert scheduler.bot == mock_bot
    assert scheduler.telegram_chat_id == 12345
    assert scheduler.timezone == "America/New_York"

def test_add_morning_checkin_job(mock_bot):
    """Test adding morning check-in job"""
    scheduler = Scheduler(
        bot=mock_bot,
        telegram_chat_id=12345,
        timezone="America/New_York"
    )

    # Add morning check-in at 4:30 AM
    job = scheduler.add_morning_checkin(time(4, 30))

    assert job is not None
    assert job.id == "morning_checkin"

def test_add_periodic_checkin_job(mock_bot):
    """Test adding periodic check-in job"""
    scheduler = Scheduler(
        bot=mock_bot,
        telegram_chat_id=12345,
        timezone="America/New_York"
    )

    # Add periodic check-in every 2 hours
    job = scheduler.add_periodic_checkin(interval_hours=2)

    assert job is not None
    assert job.id == "periodic_checkin"

def test_add_evening_review_job(mock_bot):
    """Test adding evening review job"""
    scheduler = Scheduler(
        bot=mock_bot,
        telegram_chat_id=12345,
        timezone="America/New_York"
    )

    # Add evening review at 10:00 PM
    job = scheduler.add_evening_review(time(22, 0))

    assert job is not None
    assert job.id == "evening_review"

@pytest.mark.asyncio
async def test_start_and_shutdown_scheduler(mock_bot):
    """Test starting and shutting down scheduler"""
    scheduler = Scheduler(
        bot=mock_bot,
        telegram_chat_id=12345,
        timezone="America/New_York"
    )

    # Start scheduler
    scheduler.start()

    # Verify scheduler is running
    assert scheduler._scheduler is not None
    assert scheduler._scheduler.running

    # Shutdown scheduler
    scheduler.shutdown()

    # Verify scheduler is stopped
    assert not scheduler._scheduler.running
