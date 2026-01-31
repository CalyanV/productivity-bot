import pytest
from datetime import datetime, timedelta
from src.conversation import ConversationManager

@pytest.mark.asyncio
async def test_create_session(tmp_path):
    """Test creating a new conversation session"""
    db_path = tmp_path / "test.db"
    conv_mgr = ConversationManager(str(db_path))
    await conv_mgr.initialize()

    session_id = await conv_mgr.create_session(
        telegram_user_id=12345,
        telegram_chat_id=67890,
        context_type="task_creation"
    )

    assert session_id is not None
    assert isinstance(session_id, str)

    # Verify session exists
    session = await conv_mgr.get_session(session_id)
    assert session is not None
    assert session["telegram_user_id"] == 12345
    assert session["context_type"] == "task_creation"
    assert session["message_count"] == 0

@pytest.mark.asyncio
async def test_add_message_to_session(tmp_path):
    """Test adding messages to a session"""
    db_path = tmp_path / "test.db"
    conv_mgr = ConversationManager(str(db_path))
    await conv_mgr.initialize()

    session_id = await conv_mgr.create_session(
        telegram_user_id=12345,
        telegram_chat_id=67890,
        context_type="task_creation"
    )

    await conv_mgr.add_message(session_id, "user", "Create a task")
    await conv_mgr.add_message(session_id, "assistant", "What should I call it?")

    session = await conv_mgr.get_session(session_id)
    assert session["message_count"] == 2

    messages = await conv_mgr.get_messages(session_id)
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

@pytest.mark.asyncio
async def test_session_expiry(tmp_path):
    """Test session expiration"""
    db_path = tmp_path / "test.db"
    conv_mgr = ConversationManager(str(db_path), timeout_minutes=0.01)  # 0.6 seconds
    await conv_mgr.initialize()

    session_id = await conv_mgr.create_session(
        telegram_user_id=12345,
        telegram_chat_id=67890,
        context_type="general"
    )

    # Check session is active
    session = await conv_mgr.get_session(session_id)
    assert session is not None

    # Wait for expiry
    import asyncio
    await asyncio.sleep(1)

    # Session should be expired
    session = await conv_mgr.get_session(session_id)
    assert session is None

@pytest.mark.asyncio
async def test_message_limit(tmp_path):
    """Test message count limit enforcement"""
    db_path = tmp_path / "test.db"
    conv_mgr = ConversationManager(str(db_path), max_messages=3)
    await conv_mgr.initialize()

    session_id = await conv_mgr.create_session(
        telegram_user_id=12345,
        telegram_chat_id=67890,
        context_type="task_creation"
    )

    # Add messages up to limit
    await conv_mgr.add_message(session_id, "user", "Message 1")
    await conv_mgr.add_message(session_id, "assistant", "Response 1")
    await conv_mgr.add_message(session_id, "user", "Message 2")

    session = await conv_mgr.get_session(session_id)
    assert session["message_count"] == 3

    # Check if session is at limit
    is_at_limit = await conv_mgr.is_at_message_limit(session_id)
    assert is_at_limit is True
