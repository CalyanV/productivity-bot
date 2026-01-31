import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict, List
import logging
from .database import Database
from .obsidian_sync import ObsidianSync

logger = logging.getLogger(__name__)


class GitSync:
    """Manage git synchronization for Obsidian vault"""

    def __init__(
        self,
        vault_path: str,
        db_path: str,
        remote_name: str = "origin",
        branch_name: str = "master"
    ):
        self.vault_path = vault_path
        self.db_path = db_path
        self.remote_name = remote_name
        self.branch_name = branch_name
        self.db = Database(db_path)
        self.vault_sync = ObsidianSync(vault_path)

    async def initialize(self):
        """Initialize database"""
        await self.db.initialize()

    async def check_for_changes(self) -> bool:
        """
        Check if there are uncommitted changes in the vault

        Returns:
            True if there are changes, False otherwise
        """
        try:
            result = await self._run_git_command(["status", "--porcelain"])
            return bool(result.strip())
        except Exception as e:
            logger.error(f"Error checking for changes: {e}")
            return False

    async def commit_changes(self, message: str = "Auto-sync from bot") -> bool:
        """
        Commit all changes in the vault

        Args:
            message: Commit message

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add all changes
            await self._run_git_command(["add", "."])

            # Check if there's anything to commit
            has_changes = await self.check_for_changes()
            if not has_changes:
                logger.info("No changes to commit")
                return False

            # Commit
            await self._run_git_command(["commit", "-m", message])
            logger.info(f"Committed changes: {message}")
            return True

        except Exception as e:
            logger.error(f"Error committing changes: {e}", exc_info=True)
            return False

    async def pull_changes(self) -> Dict:
        """
        Pull changes from remote repository

        Returns:
            Dictionary with status and any conflicts
        """
        try:
            # Fetch from remote
            await self._run_git_command(["fetch", self.remote_name])

            # Check if we're behind
            local_rev = await self._run_git_command(["rev-parse", self.branch_name])
            remote_rev = await self._run_git_command([
                "rev-parse",
                f"{self.remote_name}/{self.branch_name}"
            ])

            if local_rev.strip() == remote_rev.strip():
                logger.info("Already up to date")
                return {"status": "up_to_date", "conflicts": []}

            # Pull changes
            result = await self._run_git_command([
                "pull",
                self.remote_name,
                self.branch_name
            ])

            # Check for conflicts
            conflicts = await self._check_for_conflicts()

            if conflicts:
                logger.warning(f"Conflicts detected: {len(conflicts)} files")
                return {
                    "status": "conflict",
                    "conflicts": conflicts,
                    "message": result
                }

            logger.info("Successfully pulled changes")
            return {"status": "success", "conflicts": [], "message": result}

        except Exception as e:
            logger.error(f"Error pulling changes: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    async def push_changes(self) -> bool:
        """
        Push committed changes to remote repository

        Returns:
            True if successful, False otherwise
        """
        try:
            # Push to remote
            await self._run_git_command([
                "push",
                self.remote_name,
                self.branch_name
            ])

            logger.info("Successfully pushed changes")
            return True

        except Exception as e:
            logger.error(f"Error pushing changes: {e}", exc_info=True)
            return False

    async def sync(self) -> Dict:
        """
        Full sync cycle: commit local changes, pull, resolve conflicts, push

        Returns:
            Dictionary with sync status
        """
        result = {
            "committed": False,
            "pulled": False,
            "pushed": False,
            "conflicts": [],
            "errors": []
        }

        try:
            # Commit local changes
            if await self.check_for_changes():
                result["committed"] = await self.commit_changes("Auto-sync before pull")

            # Pull from remote
            pull_result = await self.pull_changes()
            result["pulled"] = pull_result["status"] == "success"

            if pull_result["status"] == "conflict":
                result["conflicts"] = pull_result["conflicts"]
                # Auto-resolve conflicts
                resolved = await self._auto_resolve_conflicts(pull_result["conflicts"])
                if resolved:
                    # Commit resolution
                    await self.commit_changes("Auto-resolved conflicts")
                    result["conflict_resolved"] = True

            # Push changes
            if result["pulled"] and not result["conflicts"]:
                result["pushed"] = await self.push_changes()

            # Rebuild index after sync
            if result["pulled"]:
                await self.vault_sync.rebuild_index(self.db_path)
                logger.info("Rebuilt database index after sync")

        except Exception as e:
            logger.error(f"Error during sync: {e}", exc_info=True)
            result["errors"].append(str(e))

        return result

    async def _run_git_command(self, args: List[str]) -> str:
        """
        Run a git command in the vault directory

        Args:
            args: Git command arguments

        Returns:
            Command output
        """
        cmd = ["git"] + args

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                cmd,
                cwd=self.vault_path,
                capture_output=True,
                text=True,
                check=True
            )
        )

        return result.stdout

    async def _check_for_conflicts(self) -> List[str]:
        """
        Check for merge conflicts

        Returns:
            List of conflicted file paths
        """
        try:
            result = await self._run_git_command([
                "diff",
                "--name-only",
                "--diff-filter=U"
            ])

            conflicts = [line.strip() for line in result.split('\n') if line.strip()]
            return conflicts

        except Exception as e:
            logger.error(f"Error checking for conflicts: {e}")
            return []

    async def _auto_resolve_conflicts(self, conflicts: List[str]) -> bool:
        """
        Auto-resolve simple conflicts using last-write-wins strategy

        Args:
            conflicts: List of conflicted file paths

        Returns:
            True if all conflicts resolved, False otherwise
        """
        try:
            for file_path in conflicts:
                # Use 'ours' strategy (keep local changes)
                # This is simplistic - a real implementation would be more sophisticated
                await self._run_git_command([
                    "checkout",
                    "--ours",
                    file_path
                ])

                # Stage the resolution
                await self._run_git_command(["add", file_path])

                logger.info(f"Auto-resolved conflict in {file_path}")

            return True

        except Exception as e:
            logger.error(f"Error auto-resolving conflicts: {e}", exc_info=True)
            return False
