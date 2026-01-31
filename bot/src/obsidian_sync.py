import frontmatter
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import logging
import aiosqlite

logger = logging.getLogger(__name__)


class ObsidianSync:
    """Manage Obsidian vault files and sync with SQLite"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.templates_path = self.vault_path / "templates"

    async def create_task_file(self, task_data: Dict) -> str:
        """Create a task markdown file with YAML frontmatter"""
        task_id = task_data["id"]
        status = task_data.get("status", "active")

        # Determine folder based on status
        if status == "completed":
            # Create year-month folder
            now = datetime.now()
            folder = self.vault_path / "01-tasks" / "completed" / f"{now.year}-{now.month:02d}"
        elif status == "someday":
            folder = self.vault_path / "01-tasks" / "someday"
        else:
            folder = self.vault_path / "01-tasks" / "active"

        folder.mkdir(parents=True, exist_ok=True)

        # Create file
        file_path = folder / f"task-{task_id}.md"

        # Build frontmatter
        frontmatter_data = {
            "id": task_data["id"],
            "type": "task",
            "title": task_data["title"],
            "status": task_data.get("status", "active"),
            "created_at": task_data["created_at"],
            "updated_at": task_data["updated_at"],
            "due_date": task_data.get("due_date"),
            "priority": task_data.get("priority", "medium"),
            "project_id": task_data.get("project_id"),
            "project_name": task_data.get("project_name"),
            "people_ids": task_data.get("people_ids", []),
            "time_estimate_minutes": task_data.get("time_estimate_minutes"),
            "time_estimate_source": task_data.get("time_estimate_source"),
            "time_actual_minutes": task_data.get("time_actual_minutes"),
            "calendar_event_id": task_data.get("calendar_event_id"),
            "scheduled_start": task_data.get("scheduled_start"),
            "scheduled_end": task_data.get("scheduled_end"),
            "tags": task_data.get("tags", [])
        }

        # Build content
        content = f"# {task_data['title']}\n\n"
        content += "## Description\n\n"

        if task_data.get("context"):
            content += f"{task_data['context']}\n\n"

        content += "## Notes\n\n"
        content += "## Subtasks\n\n"
        content += "## Related\n\n"

        # Create post
        post = frontmatter.Post(content, **frontmatter_data)

        # Write file
        with open(file_path, 'w') as f:
            f.write(frontmatter.dumps(post))

        logger.info(f"Created task file: {file_path}")
        return str(file_path)

    async def update_task_file(self, task_id: str, updates: Dict) -> str:
        """Update task file with new data"""
        # Find task file
        task_file = await self._find_task_file(task_id)

        if not task_file:
            raise FileNotFoundError(f"Task file not found for ID: {task_id}")

        # Load existing file
        with open(task_file) as f:
            post = frontmatter.load(f)

        # Update frontmatter
        for key, value in updates.items():
            if key != "id":  # Don't allow ID changes
                post[key] = value

        # Update timestamp
        post["updated_at"] = datetime.now().isoformat()

        # Write back
        with open(task_file, 'w') as f:
            f.write(frontmatter.dumps(post))

        logger.info(f"Updated task file: {task_file}")
        return str(task_file)

    async def _find_task_file(self, task_id: str) -> Optional[Path]:
        """Find task file by ID"""
        for folder in ["active", "completed", "someday"]:
            search_path = self.vault_path / "01-tasks" / folder
            if not search_path.exists():
                continue

            # Search recursively (for completed with year-month folders)
            for file_path in search_path.rglob(f"task-{task_id}.md"):
                return file_path

        return None

    async def rebuild_index(self, db_path: str):
        """Rebuild SQLite index from vault files"""
        from .database import Database

        db = Database(db_path)
        conn = await db.connect()

        try:
            # Clear existing index
            await conn.execute("DELETE FROM tasks")
            await conn.execute("DELETE FROM projects")
            await conn.execute("DELETE FROM people")
            await conn.execute("DELETE FROM daily_logs")
            await conn.commit()

            # Index tasks
            await self._index_tasks(conn)

            # Index projects
            await self._index_projects(conn)

            # Index people
            await self._index_people(conn)

            # Index daily logs
            await self._index_daily_logs(conn)

            await conn.commit()
            logger.info("Rebuilt index from vault")

        finally:
            await db.close()

    async def _index_tasks(self, conn: aiosqlite.Connection):
        """Index all task files"""
        tasks_path = self.vault_path / "01-tasks"

        for task_file in tasks_path.rglob("task-*.md"):
            with open(task_file) as f:
                post = frontmatter.load(f)

            await conn.execute("""
                INSERT INTO tasks (
                    id, title, status, created_at, updated_at, due_date,
                    priority, project_id, project_name, time_estimate_minutes,
                    time_estimate_source, time_actual_minutes, calendar_event_id,
                    scheduled_start, scheduled_end, context, completed_at, file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                post.get("id"),
                post.get("title"),
                post.get("status"),
                post.get("created_at"),
                post.get("updated_at"),
                post.get("due_date"),
                post.get("priority"),
                post.get("project_id"),
                post.get("project_name"),
                post.get("time_estimate_minutes"),
                post.get("time_estimate_source"),
                post.get("time_actual_minutes"),
                post.get("calendar_event_id"),
                post.get("scheduled_start"),
                post.get("scheduled_end"),
                post.get("context"),
                post.get("completed_at"),
                str(task_file)
            ))

            # Index tags
            for tag in post.get("tags", []):
                await conn.execute(
                    "INSERT INTO task_tags (task_id, tag) VALUES (?, ?)",
                    (post.get("id"), tag)
                )

            # Index people
            for person_id in post.get("people_ids", []):
                await conn.execute(
                    "INSERT INTO task_people (task_id, person_id) VALUES (?, ?)",
                    (post.get("id"), person_id)
                )

    async def _index_projects(self, conn: aiosqlite.Connection):
        """Index all project files"""
        projects_path = self.vault_path / "02-projects"

        if not projects_path.exists():
            return

        for project_file in projects_path.glob("project-*.md"):
            with open(project_file) as f:
                post = frontmatter.load(f)

            await conn.execute("""
                INSERT INTO projects (
                    id, title, status, created_at, updated_at, deadline, file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                post.get("id"),
                post.get("title"),
                post.get("status"),
                post.get("created_at"),
                post.get("updated_at"),
                post.get("deadline"),
                str(project_file)
            ))

    async def _index_people(self, conn: aiosqlite.Connection):
        """Index all people files"""
        people_path = self.vault_path / "03-people"

        if not people_path.exists():
            return

        for person_file in people_path.glob("person-*.md"):
            with open(person_file) as f:
                post = frontmatter.load(f)

            await conn.execute("""
                INSERT INTO people (
                    id, name, role, company, email, phone,
                    created_at, updated_at, last_contact,
                    contact_frequency_days, file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                post.get("id"),
                post.get("name"),
                post.get("role"),
                post.get("company"),
                post.get("email"),
                post.get("phone"),
                post.get("created_at"),
                post.get("updated_at"),
                post.get("last_contact"),
                post.get("contact_frequency_days"),
                str(person_file)
            ))

    async def _index_daily_logs(self, conn: aiosqlite.Connection):
        """Index all daily log files"""
        logs_path = self.vault_path / "04-daily-logs"

        if not logs_path.exists():
            return

        for log_file in logs_path.rglob("*.md"):
            if log_file.name.startswith("2"):  # YYYY-MM-DD format
                with open(log_file) as f:
                    post = frontmatter.load(f)

                await conn.execute("""
                    INSERT INTO daily_logs (
                        id, date, created_at, morning_checkin_at,
                        evening_review_at, total_planned_minutes,
                        total_actual_minutes, energy_level_morning,
                        energy_level_evening, file_path
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    post.get("id"),
                    post.get("date"),
                    post.get("created_at"),
                    post.get("morning_checkin_at"),
                    post.get("evening_review_at"),
                    post.get("total_planned_minutes", 0),
                    post.get("total_actual_minutes", 0),
                    post.get("energy_level_morning"),
                    post.get("energy_level_evening"),
                    str(log_file)
                ))
