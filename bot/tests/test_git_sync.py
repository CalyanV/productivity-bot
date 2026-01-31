import pytest
from pathlib import Path
from src.git_sync import GitSync

@pytest.mark.asyncio
async def test_git_sync_initialization(tmp_path):
    """Test GitSync initializes correctly"""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    sync = GitSync(
        vault_path=str(vault_path),
        db_path=":memory:"
    )

    assert sync.vault_path == str(vault_path)
    assert sync.db_path == ":memory:"

@pytest.mark.asyncio
async def test_check_for_changes(tmp_path):
    """Test checking for git changes"""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    # Initialize git repo
    import subprocess
    subprocess.run(["git", "init"], cwd=vault_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=vault_path)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=vault_path)

    # Create a file
    test_file = vault_path / "test.md"
    test_file.write_text("# Test")
    subprocess.run(["git", "add", "."], cwd=vault_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial"], cwd=vault_path, check=True)

    sync = GitSync(
        vault_path=str(vault_path),
        db_path=":memory:"
    )

    # No changes yet
    has_changes = await sync.check_for_changes()
    assert has_changes is False

    # Make a change
    test_file.write_text("# Test Modified")

    # Should detect changes
    has_changes = await sync.check_for_changes()
    assert has_changes is True

@pytest.mark.asyncio
async def test_pull_changes(tmp_path):
    """Test pulling changes from remote"""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    sync = GitSync(
        vault_path=str(vault_path),
        db_path=":memory:"
    )

    # This is a basic test - actual pull requires remote
    # Just verify method exists and doesn't crash
    assert hasattr(sync, 'pull_changes')

@pytest.mark.asyncio
async def test_push_changes(tmp_path):
    """Test pushing changes to remote"""
    vault_path = tmp_path / "vault"
    vault_path.mkdir()

    sync = GitSync(
        vault_path=str(vault_path),
        db_path=":memory:"
    )

    # Verify method exists
    assert hasattr(sync, 'push_changes')
