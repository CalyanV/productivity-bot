import pytest
import aiosqlite
from pathlib import Path
from src.database import Database

@pytest.mark.asyncio
async def test_database_initialization(tmp_path):
    """Test that database initializes with correct schema"""
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))

    await db.initialize()

    # Check tables exist
    async with aiosqlite.connect(str(db_path)) as conn:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in await cursor.fetchall()]

    assert "tasks" in tables
    assert "projects" in tables
    assert "people" in tables
    assert "daily_logs" in tables
    assert "bot_sessions" in tables
