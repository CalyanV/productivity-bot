import pytest
from pathlib import Path
from datetime import datetime
import frontmatter
from src.obsidian_sync import ObsidianSync

@pytest.mark.asyncio
async def test_create_task_file(tmp_path):
    """Test creating a task markdown file"""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    sync = ObsidianSync(str(vault_path))

    task_data = {
        "id": "test-task-123",
        "title": "Test Task",
        "status": "active",
        "created_at": "2026-01-31T10:00:00-05:00",
        "updated_at": "2026-01-31T10:00:00-05:00",
        "priority": "medium",
        "tags": ["test"]
    }

    file_path = await sync.create_task_file(task_data)

    # Verify file exists
    assert Path(file_path).exists()

    # Verify content
    with open(file_path) as f:
        post = frontmatter.load(f)

    assert post["id"] == "test-task-123"
    assert post["title"] == "Test Task"
    assert post["status"] == "active"
    assert "Test Task" in post.content
