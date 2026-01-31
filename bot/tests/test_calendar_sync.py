import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from src.calendar_sync import CalendarSync

@pytest.mark.asyncio
async def test_calendar_sync_initialization(tmp_path):
    """Test CalendarSync initializes correctly"""
    db_path = tmp_path / "test.db"

    sync = CalendarSync(
        db_path=str(db_path),
        vault_path="/tmp/vault",
        calendar_client_id="test_id",
        calendar_client_secret="test_secret",
        calendar_refresh_token="test_token"
    )

    assert sync.db_path == str(db_path)
    assert sync.vault_path == "/tmp/vault"

@pytest.mark.asyncio
async def test_get_last_sync_time(tmp_path):
    """Test retrieving last sync time"""
    db_path = tmp_path / "test.db"

    sync = CalendarSync(
        db_path=str(db_path),
        vault_path="/tmp/vault",
        calendar_client_id="test_id",
        calendar_client_secret="test_secret",
        calendar_refresh_token="test_token"
    )

    await sync.initialize()

    # First sync should return None
    last_sync = await sync.get_last_sync_time()
    assert last_sync is None

@pytest.mark.asyncio
async def test_update_sync_time(tmp_path):
    """Test updating sync time"""
    db_path = tmp_path / "test.db"

    sync = CalendarSync(
        db_path=str(db_path),
        vault_path="/tmp/vault",
        calendar_client_id="test_id",
        calendar_client_secret="test_secret",
        calendar_refresh_token="test_token"
    )

    await sync.initialize()

    now = datetime.now()
    await sync.update_sync_time(now, "test_sync_token")

    # Verify it was saved
    last_sync = await sync.get_last_sync_time()
    assert last_sync is not None
