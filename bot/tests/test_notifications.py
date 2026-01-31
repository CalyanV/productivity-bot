import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from src.notifications import NotificationManager

@pytest.mark.asyncio
async def test_notification_manager_initialization(tmp_path):
    """Test NotificationManager initializes correctly"""
    db_path = tmp_path / "test.db"

    manager = NotificationManager(
        db_path=str(db_path),
        ntfy_url="https://ntfy.sh",
        ntfy_topic="test-topic"
    )

    assert manager.db_path == str(db_path)
    assert manager.ntfy_url == "https://ntfy.sh"
    assert manager.ntfy_topic == "test-topic"

@pytest.mark.asyncio
async def test_send_notification(tmp_path):
    """Test sending a notification via ntfy.sh"""
    db_path = tmp_path / "test.db"

    manager = NotificationManager(
        db_path=str(db_path),
        ntfy_url="https://ntfy.sh",
        ntfy_topic="test-topic"
    )

    await manager.initialize()

    with patch('requests.post') as mock_post:
        mock_post.return_value = MagicMock(status_code=200)

        result = await manager.send_notification(
            title="Test Notification",
            message="This is a test",
            priority="default"
        )

        assert result is not None
        assert "notification_id" in result
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_track_notification(tmp_path):
    """Test tracking notification in database"""
    db_path = tmp_path / "test.db"

    manager = NotificationManager(
        db_path=str(db_path),
        ntfy_url="https://ntfy.sh",
        ntfy_topic="test-topic"
    )

    await manager.initialize()

    notification_id = await manager.track_notification(
        notification_type="morning_checkin",
        scheduled_for=datetime.now()
    )

    assert notification_id is not None

@pytest.mark.asyncio
async def test_acknowledge_notification(tmp_path):
    """Test acknowledging a notification"""
    db_path = tmp_path / "test.db"

    manager = NotificationManager(
        db_path=str(db_path),
        ntfy_url="https://ntfy.sh",
        ntfy_topic="test-topic"
    )

    await manager.initialize()

    # Track notification
    notification_id = await manager.track_notification(
        notification_type="test",
        scheduled_for=datetime.now()
    )

    # Acknowledge it
    await manager.acknowledge_notification(notification_id)

    # Verify acknowledgment
    notification = await manager.get_notification(notification_id)
    assert notification["acknowledged_at"] is not None
