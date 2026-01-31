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

@pytest.mark.asyncio
async def test_escalate_notification(tmp_path):
    """Test escalating notification priority"""
    from datetime import timedelta

    db_path = tmp_path / "test.db"

    manager = NotificationManager(
        db_path=str(db_path),
        ntfy_url="https://ntfy.sh",
        ntfy_topic="test-topic"
    )

    await manager.initialize()

    # Track notification sent 6 minutes ago (should escalate to high)
    six_minutes_ago = datetime.now() - timedelta(minutes=6)
    notification_id = await manager.track_notification(
        notification_type="morning_checkin",
        scheduled_for=six_minutes_ago
    )

    await manager.mark_as_sent(notification_id)

    # Check if it needs escalation
    needs_escalation = await manager.needs_escalation(notification_id)
    assert needs_escalation is True

    # Get escalation priority
    priority = await manager.get_escalation_priority(notification_id)
    assert priority == "high"

@pytest.mark.asyncio
async def test_escalation_levels(tmp_path):
    """Test different escalation levels based on time"""
    from datetime import timedelta

    db_path = tmp_path / "test.db"

    manager = NotificationManager(
        db_path=str(db_path),
        ntfy_url="https://ntfy.sh",
        ntfy_topic="test-topic"
    )

    await manager.initialize()

    # Test each escalation level
    test_cases = [
        (3, "default"),   # 3 minutes: no escalation
        (6, "high"),      # 6 minutes: high priority
        (11, "urgent"),   # 11 minutes: urgent priority
        (16, "urgent"),   # 16 minutes: max urgent
    ]

    for minutes, expected_priority in test_cases:
        time_ago = datetime.now() - timedelta(minutes=minutes)
        notification_id = await manager.track_notification(
            notification_type="test",
            scheduled_for=time_ago
        )
        await manager.mark_as_sent(notification_id)

        priority = await manager.get_escalation_priority(notification_id)
        assert priority == expected_priority, f"Failed for {minutes} minutes"
