import pytest
from datetime import datetime
from src.nlp import TaskParser
from src.models import ParsedTask

@pytest.mark.asyncio
async def test_parse_task_basic():
    """Test parsing simple task input"""
    parser = TaskParser(api_key="test_key")

    result = await parser.parse_task(
        user_input="Call John about proposal tomorrow",
        context={}
    )

    assert isinstance(result, ParsedTask)
    assert "call" in result.title.lower()
    assert "john" in result.title.lower()
    assert result.due_date is not None
    assert "john" in [p.lower() for p in result.people_names]
