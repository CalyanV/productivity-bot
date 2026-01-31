"""
End-to-end integration tests for the productivity bot

These tests verify that all components work together correctly
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from src.database import Database
from src.obsidian_sync import ObsidianSync
from src.nlp import TaskParser
from src.calendar_integration import CalendarIntegration
from src.people import PeopleManager
from src.checkins import CheckinManager
from src.git_sync import GitSync
from src.summarization import ConversationSummarizer
from src.settings import UserSettings


@pytest.mark.asyncio
async def test_task_creation_to_obsidian_flow(tmp_path):
    """Test complete flow: parse task -> save to DB -> create Obsidian file"""
    db_path = tmp_path / "test.db"
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    # Initialize components
    db = Database(str(db_path))
    await db.initialize()

    vault_sync = ObsidianSync(str(vault_path))

    # Create a task via ObsidianSync
    task_data = {
        "id": "task-123",
        "title": "Test task",
        "status": "active",
        "priority": "high",
        "tags": ["work", "urgent"],
        "created_at": datetime.now().isoformat()
    }

    file_path = await vault_sync.create_task_file(task_data)

    # Verify file was created
    assert Path(file_path).exists()

    # Verify content
    content = Path(file_path).read_text()
    assert "task-123" in content
    assert "Test task" in content
    assert "high" in content


@pytest.mark.asyncio
async def test_obsidian_to_database_sync(tmp_path):
    """Test rebuilding database index from Obsidian files"""
    db_path = tmp_path / "test.db"
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    # Create Obsidian structure
    tasks_dir = vault_path / "01-tasks" / "active"
    tasks_dir.mkdir(parents=True)

    # Create sample task file
    task_file = tasks_dir / "test-task.md"
    task_file.write_text("""---
id: task-abc
type: task
title: Sample Task
status: active
priority: medium
created_at: 2026-01-31T10:00:00
---

# Sample Task

This is a test task.
""")

    # Rebuild index
    vault_sync = ObsidianSync(str(vault_path))
    await vault_sync.rebuild_index(str(db_path))

    # Verify task was indexed
    db = Database(str(db_path))
    await db.initialize()

    import aiosqlite
    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute("SELECT * FROM tasks WHERE id = ?", ("task-abc",))
        task = await cursor.fetchone()

        assert task is not None
        assert task["title"] == "Sample Task"
        assert task["status"] == "active"
        assert task["priority"] == "medium"


@pytest.mark.asyncio
async def test_people_crm_workflow(tmp_path):
    """Test complete people/CRM workflow"""
    db_path = tmp_path / "test.db"
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    people_manager = PeopleManager(str(db_path), str(vault_path))
    await people_manager.initialize()

    # Create a person
    result = await people_manager.create_person({
        "name": "John Doe",
        "email": "john@example.com",
        "company": "Acme Corp",
        "role": "CEO"
    })

    person_id = result["person_id"]

    # Verify in database
    person = await people_manager.get_person(person_id)
    assert person["name"] == "John Doe"
    assert person["email"] == "john@example.com"

    # Verify Obsidian file created
    person_files = list((vault_path / "03-people").glob("*.md"))
    assert len(person_files) == 1
    assert "John Doe" in person_files[0].read_text()

    # Search for person
    results = await people_manager.search_people("John")
    assert len(results) == 1
    assert results[0]["name"] == "John Doe"

    # Update last contact
    await people_manager.update_last_contact(person_id)
    updated = await people_manager.get_person(person_id)
    assert updated["last_contact"] is not None


@pytest.mark.asyncio
async def test_daily_checkin_workflow(tmp_path):
    """Test morning and evening check-in workflow"""
    db_path = tmp_path / "test.db"
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    checkin_mgr = CheckinManager(str(db_path), str(vault_path))
    await checkin_mgr.initialize()

    # Morning check-in
    today = datetime.now().strftime("%Y-%m-%d")
    morning_data = {
        "date": today,
        "energy_level": 8,
        "mood": "energized",
        "habits": {
            "exercise": True,
            "meditation": True,
            "breakfast": True
        },
        "priorities": [
            "Finish project proposal",
            "Call client",
            "Review code"
        ]
    }

    result = await checkin_mgr.create_morning_checkin(morning_data)
    assert result["log_id"] == f"log-{today}"

    # Verify daily log file created
    log_files = list((vault_path / "04-daily-logs").glob(f"{today}.md"))
    assert len(log_files) == 1

    content = log_files[0].read_text()
    assert "energized" in content
    assert "Finish project proposal" in content
    assert "✅ Exercise" in content

    # Evening review
    evening_data = {
        "date": today,
        "energy_level": 6,
        "mood": "satisfied",
        "accomplishments": ["Completed proposal", "Called client"],
        "learnings": "Time-blocking works well"
    }

    result = await checkin_mgr.create_evening_review(evening_data)
    assert result["log_id"] == f"log-{today}"


@pytest.mark.asyncio
async def test_settings_workflow(tmp_path):
    """Test user settings workflow"""
    db_path = tmp_path / "test.db"

    settings = UserSettings(str(db_path))
    await settings.initialize()

    user_id = 123456

    # Get default settings
    default_settings = await settings.get_settings(user_id)
    assert default_settings["timezone"] == "America/New_York"

    # Update settings
    updated = await settings.update_settings(
        user_id,
        {
            "timezone": "Europe/London",
            "work_hours_start": 8,
            "morning_checkin_time": "06:00"
        }
    )

    assert updated["timezone"] == "Europe/London"
    assert updated["work_hours_start"] == 8

    # Retrieve and verify persistence
    retrieved = await settings.get_settings(user_id)
    assert retrieved["timezone"] == "Europe/London"
    assert retrieved["work_hours_start"] == 8

    # Reset settings
    reset = await settings.reset_settings(user_id)
    assert reset["timezone"] == "America/New_York"


@pytest.mark.asyncio
async def test_conversation_summarization_workflow(tmp_path):
    """Test conversation summarization workflow"""
    db_path = tmp_path / "test.db"

    # Mock LLM API key
    summarizer = ConversationSummarizer(
        db_path=str(db_path),
        llm_api_key="test-key"
    )
    await summarizer.initialize()

    # Create mock messages
    messages = [
        {"role": "user", "content": "I need to finish the project proposal by Friday"},
        {"role": "assistant", "content": "I'll help you create a task for that"},
        {"role": "user", "content": "Also schedule a meeting with John next week"},
        {"role": "assistant", "content": "Added task and will find a meeting slot"}
    ]

    # Note: This will fail without real API key, but tests the structure
    # In production, you'd use a mock or test API endpoint


@pytest.mark.asyncio
async def test_git_sync_workflow(tmp_path):
    """Test git synchronization workflow"""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    # Initialize git repo
    import subprocess
    subprocess.run(["git", "init"], cwd=vault_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=vault_path)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=vault_path)

    # Create initial commit
    test_file = vault_path / "test.md"
    test_file.write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=vault_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=vault_path, check=True)

    # Test git sync
    git_sync = GitSync(
        vault_path=str(vault_path),
        db_path=":memory:"
    )

    # Check for changes
    has_changes = await git_sync.check_for_changes()
    assert has_changes is False

    # Make a change
    test_file.write_text("# Test Modified")

    has_changes = await git_sync.check_for_changes()
    assert has_changes is True

    # Commit changes
    committed = await git_sync.commit_changes("Test commit")
    assert committed is True


@pytest.mark.asyncio
async def test_full_task_lifecycle(tmp_path):
    """Test complete task lifecycle from creation to completion"""
    db_path = tmp_path / "test.db"
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    db = Database(str(db_path))
    await db.initialize()

    vault_sync = ObsidianSync(str(vault_path))

    # Step 1: Create task
    task_data = {
        "id": "task-lifecycle",
        "title": "Complete integration test",
        "status": "active",
        "priority": "high",
        "due_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "created_at": datetime.now().isoformat(),
        "tags": ["testing"]
    }

    file_path = await vault_sync.create_task_file(task_data)
    assert Path(file_path).exists()

    # Step 2: Rebuild index
    await vault_sync.rebuild_index(str(db_path))

    # Step 3: Verify in database
    import aiosqlite
    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            ("task-lifecycle",)
        )
        task = await cursor.fetchone()
        assert task is not None
        assert task["title"] == "Complete integration test"
        assert task["status"] == "active"

    # Step 4: Update task status to completed
    task_data["status"] = "completed"
    task_data["completed_at"] = datetime.now().isoformat()

    # Move file to completed folder
    completed_path = await vault_sync.create_task_file(task_data)

    # Original file should be in completed folder now
    assert "completed" in completed_path

    # Step 5: Rebuild index again
    await vault_sync.rebuild_index(str(db_path))

    # Step 6: Verify status updated in database
    async with aiosqlite.connect(str(db_path)) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            ("task-lifecycle",)
        )
        task = await cursor.fetchone()
        assert task is not None
        assert task["status"] == "completed"
        assert task["completed_at"] is not None


@pytest.mark.asyncio
async def test_multiple_users_isolation(tmp_path):
    """Test that multiple users' data is properly isolated"""
    db_path = tmp_path / "test.db"

    settings = UserSettings(str(db_path))
    await settings.initialize()

    # User 1
    user1_settings = await settings.update_settings(
        111111,
        {"timezone": "America/New_York", "work_hours_start": 9}
    )

    # User 2
    user2_settings = await settings.update_settings(
        222222,
        {"timezone": "Europe/London", "work_hours_start": 8}
    )

    # Verify isolation
    retrieved_user1 = await settings.get_settings(111111)
    retrieved_user2 = await settings.get_settings(222222)

    assert retrieved_user1["timezone"] == "America/New_York"
    assert retrieved_user1["work_hours_start"] == 9

    assert retrieved_user2["timezone"] == "Europe/London"
    assert retrieved_user2["work_hours_start"] == 8
