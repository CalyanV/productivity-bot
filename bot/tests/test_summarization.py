import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from src.summarization import ConversationSummarizer

@pytest.mark.asyncio
async def test_summarizer_initialization(tmp_path):
    """Test ConversationSummarizer initializes correctly"""
    db_path = tmp_path / "test.db"

    summarizer = ConversationSummarizer(
        db_path=str(db_path),
        llm_api_key="test_key"
    )

    assert summarizer.db_path == str(db_path)
    assert summarizer.llm_api_key == "test_key"

@pytest.mark.asyncio
async def test_summarize_conversation(tmp_path):
    """Test summarizing a conversation"""
    db_path = tmp_path / "test.db"

    summarizer = ConversationSummarizer(
        db_path=str(db_path),
        llm_api_key="test_key"
    )

    await summarizer.initialize()

    messages = [
        {"role": "user", "content": "I need to finish the project proposal"},
        {"role": "assistant", "content": "I'll create a task for that"},
        {"role": "user", "content": "It's due Friday"},
        {"role": "assistant", "content": "Got it, due Friday"}
    ]

    # Mock LLM call
    with patch.object(summarizer.llm, 'complete', new_callable=AsyncMock) as mock_llm:
        mock_summary = MagicMock()
        mock_summary.summary = "User requested task: complete project proposal, due Friday"
        mock_summary.key_points = ["Project proposal task", "Due Friday"]
        mock_summary.action_items = ["Complete project proposal by Friday"]

        mock_llm.return_value = mock_summary

        result = await summarizer.summarize_conversation(messages)

        assert result is not None
        assert "summary" in result
        assert "key_points" in result
        mock_llm.assert_called_once()

@pytest.mark.asyncio
async def test_store_summary(tmp_path):
    """Test storing conversation summary"""
    db_path = tmp_path / "test.db"

    summarizer = ConversationSummarizer(
        db_path=str(db_path),
        llm_api_key="test_key"
    )

    await summarizer.initialize()

    summary_data = {
        "summary": "Discussed project deadlines",
        "key_points": ["Deadline Friday", "Need resources"],
        "action_items": ["Complete proposal"]
    }

    summary_id = await summarizer.store_summary(
        telegram_user_id=12345,
        date=datetime.now().strftime("%Y-%m-%d"),
        summary_data=summary_data
    )

    assert summary_id is not None

@pytest.mark.asyncio
async def test_get_recent_summaries(tmp_path):
    """Test retrieving recent summaries"""
    db_path = tmp_path / "test.db"

    summarizer = ConversationSummarizer(
        db_path=str(db_path),
        llm_api_key="test_key"
    )

    await summarizer.initialize()

    # Store a summary
    await summarizer.store_summary(
        telegram_user_id=12345,
        date=datetime.now().strftime("%Y-%m-%d"),
        summary_data={"summary": "Test summary"}
    )

    # Retrieve it
    summaries = await summarizer.get_recent_summaries(
        telegram_user_id=12345,
        days=7
    )

    assert len(summaries) == 1
