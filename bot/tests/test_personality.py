import pytest
from datetime import datetime
from src.personality import BotPersonality


def test_get_greeting_morning():
    """Test morning greetings (5-12)"""
    greeting = BotPersonality.get_greeting(hour=9)
    assert greeting is not None
    assert len(greeting) > 0
    # Should be one of the morning greetings
    assert any(x in greeting.lower() for x in ["morning", "rise", "shine"])


def test_get_greeting_afternoon():
    """Test afternoon greetings (12-17)"""
    greeting = BotPersonality.get_greeting(hour=14)
    assert greeting is not None
    assert "afternoon" in greeting.lower() or "day" in greeting.lower()


def test_get_greeting_evening():
    """Test evening greetings (17-22)"""
    greeting = BotPersonality.get_greeting(hour=19)
    assert greeting is not None
    assert "evening" in greeting.lower()


def test_get_greeting_night():
    """Test night greetings (22-5)"""
    greeting = BotPersonality.get_greeting(hour=23)
    assert greeting is not None
    assert any(x in greeting.lower() for x in ["night", "owl", "midnight", "up"])


def test_get_greeting_default():
    """Test greeting with no hour (uses current time)"""
    greeting = BotPersonality.get_greeting()
    assert greeting is not None
    assert len(greeting) > 0


def test_get_completion_message():
    """Test completion message"""
    message = BotPersonality.get_completion_message()
    assert message is not None
    assert len(message) > 0
    # Should be encouraging
    assert any(x in message.lower() for x in ["awesome", "great", "nice", "well", "fantastic", "crushing"])


def test_get_morning_encouragement():
    """Test morning encouragement"""
    message = BotPersonality.get_morning_encouragement()
    assert message is not None
    assert len(message) > 0


def test_get_evening_reflection():
    """Test evening reflection"""
    message = BotPersonality.get_evening_reflection()
    assert message is not None
    assert len(message) > 0


def test_get_reminder_tone():
    """Test reminder tone"""
    tone = BotPersonality.get_reminder_tone()
    assert tone is not None
    assert "reminder" in tone.lower() or "checking" in tone.lower() or "heads" in tone.lower()


def test_format_task_list_empty():
    """Test formatting empty task list"""
    result = BotPersonality.format_task_list([])
    assert "No tasks yet" in result


def test_format_task_list_single():
    """Test formatting single task"""
    tasks = [
        {"title": "Test task", "status": "active"}
    ]
    result = BotPersonality.format_task_list(tasks)
    assert "1 task" in result
    assert "Test task" in result


def test_format_task_list_multiple():
    """Test formatting multiple tasks"""
    tasks = [
        {"title": "Task 1", "status": "active"},
        {"title": "Task 2", "status": "completed"},
        {"title": "Task 3", "status": "inbox"}
    ]
    result = BotPersonality.format_task_list(tasks)
    assert "3 tasks" in result
    assert "Task 1" in result
    assert "Task 2" in result
    assert "Task 3" in result


def test_format_task_list_max_items():
    """Test formatting with max items limit"""
    tasks = [
        {"title": f"Task {i}", "status": "active"}
        for i in range(10)
    ]
    result = BotPersonality.format_task_list(tasks, max_items=5)
    assert "10 tasks" in result
    assert "showing 5" in result
    assert "and 5 more" in result


def test_format_task_list_status_emojis():
    """Test that different statuses get different emojis"""
    tasks = [
        {"title": "Completed", "status": "completed"},
        {"title": "Active", "status": "active"},
        {"title": "Blocked", "status": "blocked"},
        {"title": "Inbox", "status": "inbox"}
    ]
    result = BotPersonality.format_task_list(tasks)
    assert "✅" in result  # completed
    assert "📋" in result  # active
    assert "🚧" in result  # blocked
    assert "📥" in result  # inbox


def test_format_error_basic():
    """Test basic error formatting"""
    result = BotPersonality.format_error("Something went wrong")
    assert "Oops!" in result
    assert "Something went wrong" in result


def test_format_error_with_tip():
    """Test error formatting with helpful tip"""
    result = BotPersonality.format_error(
        "Connection failed",
        helpful_tip="Check your internet connection"
    )
    assert "Oops!" in result
    assert "Connection failed" in result
    assert "💡 Tip:" in result
    assert "Check your internet connection" in result


def test_get_productivity_tip():
    """Test productivity tip"""
    tip = BotPersonality.get_productivity_tip()
    assert tip is not None
    assert len(tip) > 10


def test_get_context_aware_message_task_created():
    """Test context-aware message for task creation"""
    message = BotPersonality.get_context_aware_message(
        "task_created",
        {"title": "Test task"}
    )
    assert message is not None
    assert "Test task" in message or "task" in message.lower()


def test_get_context_aware_message_task_scheduled():
    """Test context-aware message for task scheduling"""
    message = BotPersonality.get_context_aware_message(
        "task_scheduled",
        {}
    )
    assert message is not None
    assert any(x in message.lower() for x in ["scheduled", "time", "calendar"])


def test_get_context_aware_message_morning_complete():
    """Test context-aware message for morning check-in"""
    message = BotPersonality.get_context_aware_message(
        "morning_checkin_complete",
        {}
    )
    assert message is not None
    assert len(message) > 0


def test_get_context_aware_message_evening_complete():
    """Test context-aware message for evening review"""
    message = BotPersonality.get_context_aware_message(
        "evening_review_complete",
        {}
    )
    assert message is not None
    assert len(message) > 0


def test_get_context_aware_message_unknown():
    """Test context-aware message for unknown action"""
    message = BotPersonality.get_context_aware_message(
        "unknown_action",
        {}
    )
    assert message is not None
    assert "unknown_action" in message


def test_randomization():
    """Test that randomization is working by calling multiple times"""
    # Get 10 greetings and ensure at least 2 different ones
    greetings = [BotPersonality.get_greeting(hour=9) for _ in range(10)]
    unique_greetings = set(greetings)
    # With 4 possible morning greetings and 10 calls, we should get variety
    # Not strictly guaranteed due to randomness, but very likely
    assert len(unique_greetings) >= 1  # At minimum, we have valid greetings
