import pytest
import json
from pathlib import Path
from src.settings import UserSettings


@pytest.mark.asyncio
async def test_settings_initialization(tmp_path):
    """Test UserSettings initializes correctly"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    # Verify table was created
    import aiosqlite
    async with aiosqlite.connect(str(db_path)) as conn:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'"
        )
        result = await cursor.fetchone()
        assert result is not None


@pytest.mark.asyncio
async def test_get_default_settings(tmp_path):
    """Test getting default settings for new user"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    # Get settings for new user
    user_settings = await settings.get_settings(123456)

    # Should return defaults
    assert user_settings["timezone"] == "America/New_York"
    assert user_settings["morning_checkin_time"] == "04:30"
    assert user_settings["periodic_checkin_enabled"] is True


@pytest.mark.asyncio
async def test_update_settings(tmp_path):
    """Test updating user settings"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    # Update settings
    updated = await settings.update_settings(
        123456,
        {
            "timezone": "America/Los_Angeles",
            "morning_checkin_time": "05:00"
        }
    )

    assert updated["timezone"] == "America/Los_Angeles"
    assert updated["morning_checkin_time"] == "05:00"

    # Verify persisted
    retrieved = await settings.get_settings(123456)
    assert retrieved["timezone"] == "America/Los_Angeles"
    assert retrieved["morning_checkin_time"] == "05:00"


@pytest.mark.asyncio
async def test_update_settings_preserves_others(tmp_path):
    """Test that updating one setting preserves others"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    # Update timezone
    await settings.update_settings(123456, {"timezone": "Europe/London"})

    # Update different setting
    updated = await settings.update_settings(
        123456,
        {"work_hours_start": 10}
    )

    # Both should be present
    assert updated["timezone"] == "Europe/London"
    assert updated["work_hours_start"] == 10


@pytest.mark.asyncio
async def test_reset_settings(tmp_path):
    """Test resetting settings to defaults"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    # Update settings
    await settings.update_settings(
        123456,
        {"timezone": "Asia/Tokyo", "work_hours_start": 10}
    )

    # Reset
    reset = await settings.reset_settings(123456)

    # Should be defaults
    assert reset["timezone"] == "America/New_York"
    assert reset["work_hours_start"] == 9


@pytest.mark.asyncio
async def test_validate_time_format(tmp_path):
    """Test validation of time format"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    # Valid time
    updated = await settings.update_settings(
        123456,
        {"morning_checkin_time": "06:30"}
    )
    assert updated["morning_checkin_time"] == "06:30"

    # Invalid time - should revert to default
    updated = await settings.update_settings(
        123456,
        {"morning_checkin_time": "invalid"}
    )
    assert updated["morning_checkin_time"] == "04:30"


@pytest.mark.asyncio
async def test_validate_hours(tmp_path):
    """Test validation of hour values (0-23)"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    # Valid hour
    updated = await settings.update_settings(
        123456,
        {"work_hours_start": 8}
    )
    assert updated["work_hours_start"] == 8

    # Invalid hour (too high)
    updated = await settings.update_settings(
        123456,
        {"work_hours_start": 25}
    )
    assert updated["work_hours_start"] == 9  # reverts to default

    # Invalid hour (negative)
    updated = await settings.update_settings(
        123456,
        {"work_hours_end": -1}
    )
    assert updated["work_hours_end"] == 17  # reverts to default


@pytest.mark.asyncio
async def test_validate_interval(tmp_path):
    """Test validation of interval hours (1-12)"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    # Valid interval
    updated = await settings.update_settings(
        123456,
        {"periodic_checkin_interval_hours": 3}
    )
    assert updated["periodic_checkin_interval_hours"] == 3

    # Invalid interval (too high)
    updated = await settings.update_settings(
        123456,
        {"periodic_checkin_interval_hours": 20}
    )
    assert updated["periodic_checkin_interval_hours"] == 2  # reverts to default


@pytest.mark.asyncio
async def test_validate_notification_priority(tmp_path):
    """Test validation of notification priority"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    # Valid priorities
    for priority in ["min", "low", "default", "high", "urgent"]:
        updated = await settings.update_settings(
            123456,
            {"notification_priority": priority}
        )
        assert updated["notification_priority"] == priority

    # Invalid priority
    updated = await settings.update_settings(
        123456,
        {"notification_priority": "invalid"}
    )
    assert updated["notification_priority"] == "default"


@pytest.mark.asyncio
async def test_validate_booleans(tmp_path):
    """Test validation of boolean fields"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    # Valid boolean
    updated = await settings.update_settings(
        123456,
        {"periodic_checkin_enabled": False}
    )
    assert updated["periodic_checkin_enabled"] is False

    # Invalid boolean (string)
    updated = await settings.update_settings(
        123456,
        {"exclude_weekends": "yes"}
    )
    assert updated["exclude_weekends"] is True  # reverts to default


@pytest.mark.asyncio
async def test_format_settings_message(tmp_path):
    """Test formatting settings as message"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    user_settings = await settings.get_settings(123456)
    message = settings.format_settings_message(user_settings)

    # Should contain key information
    assert "Settings" in message
    assert "America/New_York" in message
    assert "04:30" in message
    assert "20:00" in message
    assert "9:00 - 17:00" in message


@pytest.mark.asyncio
async def test_multiple_users(tmp_path):
    """Test settings for multiple users are independent"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    # User 1
    await settings.update_settings(111, {"timezone": "America/New_York"})

    # User 2
    await settings.update_settings(222, {"timezone": "Europe/London"})

    # Verify independence
    user1_settings = await settings.get_settings(111)
    user2_settings = await settings.get_settings(222)

    assert user1_settings["timezone"] == "America/New_York"
    assert user2_settings["timezone"] == "Europe/London"


@pytest.mark.asyncio
async def test_update_multiple_settings_at_once(tmp_path):
    """Test updating multiple settings in one call"""
    db_path = tmp_path / "test.db"
    settings = UserSettings(str(db_path))

    await settings.initialize()

    # Update multiple settings
    updated = await settings.update_settings(
        123456,
        {
            "timezone": "Asia/Tokyo",
            "work_hours_start": 10,
            "work_hours_end": 19,
            "exclude_weekends": False
        }
    )

    assert updated["timezone"] == "Asia/Tokyo"
    assert updated["work_hours_start"] == 10
    assert updated["work_hours_end"] == 19
    assert updated["exclude_weekends"] is False
