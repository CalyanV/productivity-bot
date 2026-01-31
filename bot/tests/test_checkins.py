import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from src.checkins import CheckinManager

@pytest.mark.asyncio
async def test_checkin_manager_initialization(tmp_path):
    """Test CheckinManager initializes correctly"""
    db_path = tmp_path / "test.db"

    manager = CheckinManager(
        db_path=str(db_path),
        vault_path="/tmp/vault"
    )

    assert manager.db_path == str(db_path)
    assert manager.vault_path == "/tmp/vault"

@pytest.mark.asyncio
async def test_create_morning_checkin(tmp_path):
    """Test creating a morning check-in"""
    db_path = tmp_path / "test.db"

    manager = CheckinManager(
        db_path=str(db_path),
        vault_path="/tmp/vault"
    )

    await manager.initialize()

    checkin_data = {
        "date": "2026-01-31",
        "energy_level": 7,
        "mood": "energized",
        "habits": {
            "exercise": True,
            "meditation": False
        },
        "priorities": [
            "Complete project proposal",
            "Team standup",
            "Review PRs"
        ]
    }

    result = await manager.create_morning_checkin(checkin_data)

    assert result is not None
    assert "log_id" in result

@pytest.mark.asyncio
async def test_get_todays_checkin(tmp_path):
    """Test retrieving today's check-in"""
    db_path = tmp_path / "test.db"

    manager = CheckinManager(
        db_path=str(db_path),
        vault_path="/tmp/vault"
    )

    await manager.initialize()

    # Create a check-in
    today = datetime.now().strftime("%Y-%m-%d")
    checkin_data = {
        "date": today,
        "energy_level": 8,
        "mood": "focused"
    }

    await manager.create_morning_checkin(checkin_data)

    # Retrieve it
    retrieved = await manager.get_todays_checkin()

    assert retrieved is not None
    assert retrieved["date"] == today

@pytest.mark.asyncio
async def test_morning_checkin_prompt():
    """Test generating morning check-in prompt"""
    manager = CheckinManager(
        db_path=":memory:",
        vault_path="/tmp/vault"
    )

    prompt = manager.get_morning_checkin_prompt()

    assert "morning" in prompt.lower()
    assert "energy" in prompt.lower()
    assert "habits" in prompt.lower()
