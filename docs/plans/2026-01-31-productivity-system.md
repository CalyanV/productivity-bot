# Self-Auditing Productivity System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Telegram-based conversational productivity system with task management, calendar time-blocking, personal CRM, and impossible-to-ignore check-ins running on VPS.

**Architecture:** Dual storage (Obsidian markdown files for human access + SQLite for bot queries), Git-based vault sync, stateless bot with bounded conversations, calendar as time authority, scheduled check-ins via APScheduler.

**Tech Stack:** Python 3.11+, python-telegram-bot, SQLite (aiosqlite), APScheduler, Google Calendar API, OpenRouter (DeepSeek V3.2 primary, Claude fallback), ntfy.sh, Whisper/Deepgram, Git

---

## Phase 1: Core Infrastructure (Days 1-3)

### Task 1.1: Project Setup & Dependencies

**Files:**
- Create: `bot/requirements.txt`
- Create: `bot/pyproject.toml`
- Create: `bot/.env.example`
- Create: `bot/.gitignore`

**Step 1: Create project structure**

```bash
mkdir -p bot
mkdir -p bot/tests
mkdir -p bot/src
mkdir -p obsidian-vault
mkdir -p data
mkdir -p config
mkdir -p docs/plans
```

**Step 2: Create requirements.txt**

```txt
# bot/requirements.txt
python-telegram-bot[webhooks]==20.7
google-api-python-client==2.111.0
google-auth-httplib2==0.2.0
google-auth-oauthlib==1.2.0
openai==1.12.0
instructor==0.6.0
pydantic==2.6.0
apscheduler==3.10.4
pytz==2024.1
pyyaml==6.0.1
python-dotenv==1.0.0
aiosqlite==0.19.0
python-frontmatter==1.1.0
openai-whisper==20230314
requests==2.31.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
black==23.12.1
ruff==0.1.9
```

**Step 3: Create pyproject.toml**

```toml
# bot/pyproject.toml
[project]
name = "productivity-bot"
version = "0.1.0"
description = "Self-auditing productivity system"
requires-python = ">=3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "N"]
ignore = ["E501"]
```

**Step 4: Create .env.example**

```bash
# bot/.env.example
TELEGRAM_BOT_TOKEN=your_bot_token_here
OPENROUTER_API_KEY=your_openrouter_key_here
LLM_MODEL_PRIMARY=deepseek/deepseek-chat
LLM_MODEL_FALLBACK=anthropic/claude-3.5-sonnet
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token
NTFY_URL=https://ntfy.yourdomain.com
NTFY_TOPIC=productivity-user
TIMEZONE=America/New_York
DATABASE_PATH=../data/productivity.db
VAULT_PATH=../obsidian-vault
LOG_LEVEL=INFO
```

**Step 5: Create .gitignore**

```
# bot/.gitignore
__pycache__/
*.py[cod]
*$py.class
.env
.venv/
venv/
*.db
*.log
.coverage
htmlcov/
.pytest_cache/
.ruff_cache/
```

**Step 6: Commit project setup**

```bash
git add .
git commit -m "chore: initialize project structure and dependencies"
```

---

### Task 1.2: Database Schema & Models

**Files:**
- Create: `bot/src/database.py`
- Create: `bot/tests/test_database.py`
- Create: `bot/migrations/001_initial_schema.sql`

**Step 1: Write failing test for database initialization**

```python
# bot/tests/test_database.py
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
```

**Step 2: Run test to verify it fails**

```bash
cd bot
pytest tests/test_database.py::test_database_initialization -v
```

Expected: FAIL with "No module named 'src.database'"

**Step 3: Create database schema SQL**

```sql
-- bot/migrations/001_initial_schema.sql

-- Core entities (indexed from Obsidian files)
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('inbox', 'active', 'blocked', 'completed', 'cancelled')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    due_date TEXT,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'urgent')),
    project_id TEXT,
    project_name TEXT,
    time_estimate_minutes INTEGER,
    time_estimate_source TEXT CHECK(time_estimate_source IN ('user', 'ai', 'historical')),
    time_actual_minutes INTEGER,
    calendar_event_id TEXT,
    scheduled_start TEXT,
    scheduled_end TEXT,
    context TEXT,
    completed_at TEXT,
    file_path TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS task_people (
    task_id TEXT,
    person_id TEXT,
    PRIMARY KEY (task_id, person_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (person_id) REFERENCES people(id)
);

CREATE TABLE IF NOT EXISTS task_tags (
    task_id TEXT,
    tag TEXT,
    PRIMARY KEY (task_id, tag),
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS task_subtasks (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    description TEXT NOT NULL,
    completed INTEGER DEFAULT 0,
    position INTEGER NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('planning', 'active', 'on-hold', 'completed', 'cancelled')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deadline TEXT,
    file_path TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_people (
    project_id TEXT,
    person_id TEXT,
    PRIMARY KEY (project_id, person_id),
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (person_id) REFERENCES people(id)
);

CREATE TABLE IF NOT EXISTS people (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT,
    company TEXT,
    email TEXT,
    phone TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_contact TEXT,
    contact_frequency_days INTEGER,
    file_path TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_logs (
    id TEXT PRIMARY KEY,
    date TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL,
    morning_checkin_at TEXT,
    evening_review_at TEXT,
    total_planned_minutes INTEGER DEFAULT 0,
    total_actual_minutes INTEGER DEFAULT 0,
    energy_level_morning INTEGER CHECK(energy_level_morning BETWEEN 1 AND 10),
    energy_level_evening INTEGER CHECK(energy_level_evening BETWEEN 1 AND 10),
    file_path TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_log_habits (
    log_id TEXT,
    habit_key TEXT,
    completed INTEGER,
    PRIMARY KEY (log_id, habit_key),
    FOREIGN KEY (log_id) REFERENCES daily_logs(id)
);

-- Bot session management
CREATE TABLE IF NOT EXISTS bot_sessions (
    session_id TEXT PRIMARY KEY,
    telegram_user_id INTEGER NOT NULL,
    telegram_chat_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    context_type TEXT CHECK(context_type IN ('task_creation', 'review', 'checkin', 'general')),
    context_data TEXT,
    message_count INTEGER DEFAULT 0
);

-- Conversation summaries
CREATE TABLE IF NOT EXISTS conversation_summaries (
    id TEXT PRIMARY KEY,
    telegram_user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- Notification tracking
CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL CHECK(type IN ('morning_checkin', 'periodic_checkin', 'evening_review', 'reminder')),
    scheduled_for TEXT NOT NULL,
    sent_at TEXT,
    acknowledged_at TEXT,
    response_summary TEXT
);

-- Google Calendar sync state
CREATE TABLE IF NOT EXISTS calendar_sync (
    id INTEGER PRIMARY KEY CHECK(id = 1),
    last_sync_at TEXT NOT NULL,
    sync_token TEXT
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_start ON tasks(scheduled_start);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_people_last_contact ON people(last_contact);
CREATE INDEX IF NOT EXISTS idx_daily_logs_date ON daily_logs(date);
CREATE INDEX IF NOT EXISTS idx_bot_sessions_expires ON bot_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_notifications_scheduled ON notifications(scheduled_for);
```

**Step 4: Write database.py implementation**

```python
# bot/src/database.py
import aiosqlite
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Database:
    """SQLite database manager for productivity system"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def initialize(self):
        """Initialize database with schema"""
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Read schema
        schema_path = Path(__file__).parent.parent / "migrations" / "001_initial_schema.sql"
        with open(schema_path) as f:
            schema = f.read()

        # Execute schema
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.executescript(schema)
            await conn.commit()

        logger.info(f"Database initialized at {self.db_path}")

    async def connect(self) -> aiosqlite.Connection:
        """Get database connection"""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            self._connection.row_factory = aiosqlite.Row
        return self._connection

    async def close(self):
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_database.py::test_database_initialization -v
```

Expected: PASS

**Step 6: Commit database implementation**

```bash
git add bot/src/database.py bot/tests/test_database.py bot/migrations/
git commit -m "feat: add database schema and initialization"
```

---

### Task 1.3: Obsidian Vault Structure & Templates

**Files:**
- Create: `obsidian-vault/.obsidian/config`
- Create: `obsidian-vault/templates/task-template.md`
- Create: `obsidian-vault/templates/person-template.md`
- Create: `obsidian-vault/templates/project-template.md`
- Create: `obsidian-vault/templates/daily-log-template.md`

**Step 1: Create vault folder structure**

```bash
mkdir -p obsidian-vault/{00-inbox,01-tasks/{active,completed,someday},02-projects,03-people,04-daily-logs,05-habits,templates,.obsidian}
```

**Step 2: Create task template**

```markdown
<!-- obsidian-vault/templates/task-template.md -->
---
id: {{id}}
type: task
title: "{{title}}"
status: active
created_at: {{created_at}}
updated_at: {{updated_at}}
due_date:
priority: medium
project_id:
project_name:
people_ids: []
time_estimate_minutes:
time_estimate_source:
time_actual_minutes:
calendar_event_id:
scheduled_start:
scheduled_end:
tags: []
---

# {{title}}

## Description


## Notes


## Subtasks
- [ ]

## Related

```

**Step 3: Create person template**

```markdown
<!-- obsidian-vault/templates/person-template.md -->
---
id: {{id}}
type: person
name: "{{name}}"
role:
company:
email:
phone:
created_at: {{created_at}}
updated_at: {{updated_at}}
last_contact:
contact_frequency_days: 14
tags: []
---

# {{name}}

## Quick Info
- **Role**:
- **Company**:
- **Email**:
- **Phone**:

## Interaction History


## Related Tasks
\`\`\`dataview
LIST
FROM "01-tasks"
WHERE contains(people_ids, "{{id}}")
SORT due_date
\`\`\`

## Notes

```

**Step 4: Create project template**

```markdown
<!-- obsidian-vault/templates/project-template.md -->
---
id: {{id}}
type: project
title: "{{title}}"
status: active
created_at: {{created_at}}
updated_at: {{updated_at}}
deadline:
people_ids: []
tags: []
---

# {{title}}

## Overview


## Tasks
\`\`\`dataview
LIST
FROM "01-tasks"
WHERE project_id = "{{id}}"
SORT status, due_date
\`\`\`

## People


## Notes

```

**Step 5: Create daily log template**

```markdown
<!-- obsidian-vault/templates/daily-log-template.md -->
---
id: {{id}}
type: daily_log
date: {{date}}
created_at: {{created_at}}
morning_checkin_at:
evening_review_at:
habits: {}
planned_tasks: []
completed_tasks: []
total_planned_minutes: 0
total_actual_minutes: 0
energy_level_morning:
energy_level_evening:
---

# Daily Log - {{formatted_date}}

## Morning Check-in
**Energy**: /10
**Mood**:

### Habits


### Today's Plan


**Total Planned**:

## Check-ins Throughout Day


## Evening Review
**Energy**: /10
**Mood**:

### Completed


### Not Completed


### Learnings


### Tomorrow's Priorities

```

**Step 6: Initialize git repo for vault**

```bash
cd obsidian-vault
git init
git add .
git commit -m "Initial vault structure with templates"
```

**Step 7: Commit vault structure**

```bash
cd ..
git add obsidian-vault/
git commit -m "feat: create Obsidian vault structure and templates"
```

---

### Task 1.4: Obsidian Sync Module

**Files:**
- Create: `bot/src/obsidian_sync.py`
- Create: `bot/tests/test_obsidian_sync.py`

**Step 1: Write failing test for task file creation**

```python
# bot/tests/test_obsidian_sync.py
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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_obsidian_sync.py::test_create_task_file -v
```

Expected: FAIL with "No module named 'src.obsidian_sync'"

**Step 3: Write ObsidianSync implementation**

```python
# bot/src/obsidian_sync.py
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
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_obsidian_sync.py::test_create_task_file -v
```

Expected: PASS

**Step 5: Commit ObsidianSync implementation**

```bash
git add bot/src/obsidian_sync.py bot/tests/test_obsidian_sync.py
git commit -m "feat: add Obsidian vault sync module"
```

---

### Task 1.5: Basic Telegram Bot Setup

**Files:**
- Create: `bot/src/bot.py`
- Create: `bot/src/config.py`
- Create: `bot/tests/test_bot.py`
- Create: `bot/main.py`

**Step 1: Write config module**

```python
# bot/src/config.py
from pathlib import Path
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Logging setup
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Google Calendar
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

# ntfy.sh
NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "productivity")

# Paths
BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR.parent / "data" / "productivity.db"))
VAULT_PATH = os.getenv("VAULT_PATH", str(BASE_DIR.parent / "obsidian-vault"))

# Timezone
TIMEZONE = os.getenv("TIMEZONE", "America/New_York")

# Bot Settings
SESSION_TIMEOUT_MINUTES = 30
MAX_CONVERSATION_MESSAGES = 5
```

**Step 2: Write failing test for bot initialization**

```python
# bot/tests/test_bot.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.bot import ProductivityBot

@pytest.mark.asyncio
async def test_bot_initialization():
    """Test that bot initializes correctly"""
    bot = ProductivityBot(
        token="test_token",
        db_path=":memory:",
        vault_path="/tmp/vault"
    )

    assert bot.token == "test_token"
    assert bot.db_path == ":memory:"
    assert bot.vault_path == "/tmp/vault"

@pytest.mark.asyncio
async def test_start_command():
    """Test /start command handler"""
    bot = ProductivityBot(
        token="test_token",
        db_path=":memory:",
        vault_path="/tmp/vault"
    )

    # Mock update and context
    update = MagicMock()
    update.effective_user.first_name = "Test User"
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await bot.cmd_start(update, context)

    # Verify welcome message sent
    update.message.reply_text.assert_called_once()
    call_args = update.message.reply_text.call_args[0][0]
    assert "Test User" in call_args
    assert "productivity" in call_args.lower()
```

**Step 3: Run test to verify it fails**

```bash
pytest tests/test_bot.py -v
```

Expected: FAIL with "No module named 'src.bot'"

**Step 4: Write bot.py implementation**

```python
# bot/src/bot.py
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import logging
from .database import Database
from .obsidian_sync import ObsidianSync

logger = logging.getLogger(__name__)


class ProductivityBot:
    """Main Telegram bot for productivity system"""

    def __init__(self, token: str, db_path: str, vault_path: str):
        self.token = token
        self.db_path = db_path
        self.vault_path = vault_path

        self.db = Database(db_path)
        self.vault_sync = ObsidianSync(vault_path)

        # Build application
        self.app = Application.builder().token(token).build()

        # Register handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register command and message handlers"""
        # Commands
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        self.app.add_handler(CommandHandler("add", self.cmd_add))
        self.app.add_handler(CommandHandler("tasks", self.cmd_tasks))

        # Messages (for conversation flow)
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user

        message = f"""Welcome {user.first_name}! 👋

I'm your productivity assistant. I'll help you:
• Capture tasks quickly with natural language
• Schedule time blocks on your calendar
• Track important relationships
• Stay on top of your goals with daily check-ins

Get started:
/add - Add a new task
/tasks - View your tasks
/help - See all commands

Let's get organized!"""

        await update.message.reply_text(message)
        logger.info(f"New user started bot: {user.id} ({user.first_name})")

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        message = """**Commands:**

**Quick Capture:**
/add - Add a task (or just send me a message)

**Task Management:**
/tasks - List your tasks
/tasks today - Today's tasks
/tasks week - This week
/tasks overdue - Overdue tasks

**Daily Workflow:**
/morning - Morning check-in
/evening - Evening review

**More commands coming soon!**"""

        await update.message.reply_text(message, parse_mode="Markdown")

    async def cmd_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add command"""
        # Get task text from command args
        task_text = " ".join(context.args) if context.args else None

        if not task_text:
            await update.message.reply_text(
                "What task would you like to add?\n\n"
                "Example: /add Call John about proposal tomorrow"
            )
            return

        # For now, just acknowledge (will implement NLP parsing later)
        await update.message.reply_text(
            f"Got it! I'll add:\n\n📋 {task_text}\n\n"
            "(Task parsing coming in Phase 2!)"
        )

        logger.info(f"Task add requested: {task_text}")

    async def cmd_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tasks command"""
        filter_arg = context.args[0] if context.args else "all"

        # For now, just acknowledge (will implement task listing later)
        await update.message.reply_text(
            f"Listing tasks: {filter_arg}\n\n"
            "(Task listing coming in Phase 2!)"
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle non-command messages"""
        # For now, treat as task add
        text = update.message.text

        await update.message.reply_text(
            f"I heard:\n\n\"{text}\"\n\n"
            "I'll treat this as a task. Use /add for now!"
        )

    async def initialize(self):
        """Initialize bot (database, etc.)"""
        await self.db.initialize()
        logger.info("Bot initialized")

    async def start(self):
        """Start the bot"""
        await self.initialize()
        await self.app.run_polling(drop_pending_updates=True)
        logger.info("Bot started")

    async def stop(self):
        """Stop the bot"""
        await self.db.close()
        await self.app.stop()
        logger.info("Bot stopped")
```

**Step 5: Write main.py entry point**

```python
# bot/main.py
import asyncio
import logging
from src.bot import ProductivityBot
from src.config import TELEGRAM_BOT_TOKEN, DATABASE_PATH, VAULT_PATH

logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    logger.info("Starting Productivity Bot...")

    bot = ProductivityBot(
        token=TELEGRAM_BOT_TOKEN,
        db_path=DATABASE_PATH,
        vault_path=VAULT_PATH
    )

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await bot.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await bot.stop()
        raise


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 6: Run test to verify it passes**

```bash
pytest tests/test_bot.py -v
```

Expected: PASS

**Step 7: Commit bot implementation**

```bash
git add bot/src/bot.py bot/src/config.py bot/tests/test_bot.py bot/main.py
git commit -m "feat: add basic Telegram bot with commands"
```

---

## Phase 2: NLP & Time Estimation (Days 4-5)

**LLM Strategy:**
- **OpenRouter** as unified API gateway
- **DeepSeek V3.2-Exp** for primary tasks (parsing, simple completions)
  - Cost: $0.028 per 1M input tokens
  - Fast, cheap, good enough for task parsing
- **Claude 3.5 Sonnet** as fallback for complex reasoning (time estimation)
  - Cost: ~$3 per 1M input tokens
  - Better reasoning, used selectively
- **Estimated monthly cost**: $1-3 for single user (1000 tasks/month)

**Why OpenRouter:**
- Single API for multiple models
- Easy model switching without code changes
- Often better pricing than direct APIs
- Built-in fallback and routing support

---

### Task 2.1: OpenRouter LLM Client with DeepSeek Primary

**Files:**
- Create: `bot/src/llm_client.py`
- Create: `bot/tests/test_llm_client.py`

**Step 1: Write failing test for LLM client**

```python
# bot/tests/test_llm_client.py
import pytest
from src.llm_client import LLMClient

@pytest.mark.asyncio
async def test_llm_client_initialization():
    """Test LLM client initializes with OpenRouter"""
    client = LLMClient(
        api_key="test_key",
        primary_model="deepseek/deepseek-chat",
        fallback_model="anthropic/claude-3.5-sonnet"
    )

    assert client.api_key == "test_key"
    assert client.primary_model == "deepseek/deepseek-chat"
    assert client.fallback_model == "anthropic/claude-3.5-sonnet"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_llm_client.py::test_llm_client_initialization -v
```

Expected: FAIL with "No module named 'src.llm_client'"

**Step 3: Write LLMClient implementation**

```python
# bot/src/llm_client.py
from openai import AsyncOpenAI
import instructor
from typing import Dict, Type, TypeVar, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """OpenRouter LLM client with DeepSeek primary and Claude fallback"""

    def __init__(
        self,
        api_key: str,
        primary_model: str = "deepseek/deepseek-chat",
        fallback_model: str = "anthropic/claude-3.5-sonnet"
    ):
        self.api_key = api_key
        self.primary_model = primary_model
        self.fallback_model = fallback_model

        # Initialize OpenRouter client with instructor
        self.client = instructor.from_openai(
            AsyncOpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        )

    async def complete(
        self,
        response_model: Type[T],
        messages: list[Dict[str, str]],
        use_fallback: bool = False,
        **kwargs
    ) -> T:
        """
        Complete with structured output using instructor

        Args:
            response_model: Pydantic model for structured output
            messages: Chat messages
            use_fallback: Use fallback model (Claude) instead of primary
            **kwargs: Additional completion parameters

        Returns:
            Parsed response matching response_model
        """
        model = self.fallback_model if use_fallback else self.primary_model

        try:
            result = await self.client.chat.completions.create(
                model=model,
                response_model=response_model,
                messages=messages,
                **kwargs
            )

            logger.info(f"LLM completion successful with {model}")
            return result

        except Exception as e:
            if not use_fallback and self.fallback_model:
                logger.warning(
                    f"Primary model {self.primary_model} failed: {e}. "
                    f"Trying fallback {self.fallback_model}"
                )
                return await self.complete(
                    response_model=response_model,
                    messages=messages,
                    use_fallback=True,
                    **kwargs
                )
            raise
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_llm_client.py::test_llm_client_initialization -v
```

Expected: PASS

**Step 5: Commit LLM client**

```bash
git add bot/src/llm_client.py bot/tests/test_llm_client.py
git commit -m "feat: add OpenRouter LLM client with DeepSeek primary"
```

---

### Task 2.2: Task Parsing with Structured Output

**Files:**
- Create: `bot/src/nlp.py`
- Create: `bot/tests/test_nlp.py`

**Step 1: Write failing test for task parsing**

```python
# bot/tests/test_nlp.py
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
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_nlp.py::test_parse_task_basic -v
```

Expected: FAIL

**Step 3: Create Pydantic models**

```python
# bot/src/models.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ParsedTask(BaseModel):
    """Structured task data from NLP parsing"""

    title: str = Field(description="Clear, actionable task title")
    time_estimate_minutes: Optional[int] = Field(
        None,
        description="Time estimate in minutes if mentioned"
    )
    due_date: Optional[str] = Field(
        None,
        description="Due date in YYYY-MM-DD format"
    )
    project_name: Optional[str] = Field(
        None,
        description="Project name if mentioned or inferred"
    )
    people_names: list[str] = Field(
        default_factory=list,
        description="Names of people mentioned"
    )
    priority: str = Field(
        default="medium",
        description="Priority: low, medium, high, or urgent"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Relevant tags inferred from content"
    )
    context: Optional[str] = Field(
        None,
        description="Additional context or description"
    )


class TimeEstimate(BaseModel):
    """AI time estimation result"""

    estimate_minutes: int = Field(description="Estimated time in minutes")
    confidence: str = Field(description="Confidence level: low, medium, high")
    reasoning: str = Field(description="Brief explanation of estimate")
    suggestion: str = Field(description="Helpful message for user")
```

**Step 4: Implement TaskParser**

```python
# bot/src/nlp.py
from datetime import datetime
from typing import Dict, List, Optional
import logging
from .llm_client import LLMClient
from .models import ParsedTask, TimeEstimate

logger = logging.getLogger(__name__)


class TaskParser:
    """Parse natural language task input using LLM"""

    def __init__(self, api_key: str):
        self.llm = LLMClient(api_key=api_key)

    async def parse_task(
        self,
        user_input: str,
        context: Dict
    ) -> ParsedTask:
        """
        Parse natural language into structured task

        Args:
            user_input: Raw text from user
            context: Available projects, people, today's date

        Returns:
            ParsedTask with structured data
        """
        today = datetime.now().strftime('%Y-%m-%d')

        # Build context string
        context_str = f"Today's date: {today}\n"

        if context.get('projects'):
            projects = [p['title'] for p in context['projects']]
            context_str += f"Available projects: {', '.join(projects)}\n"

        if context.get('people'):
            people = [p['name'] for p in context['people']]
            context_str += f"Known people: {', '.join(people)}\n"

        # Create prompt
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a task parsing assistant. Extract structured data "
                    "from natural language task descriptions. Parse relative dates "
                    "like 'tomorrow', 'next Friday' into YYYY-MM-DD format. "
                    "Infer people, projects, and tags from context."
                )
            },
            {
                "role": "user",
                "content": f"{context_str}\nTask: {user_input}"
            }
        ]

        # Call LLM with structured output
        result = await self.llm.complete(
            response_model=ParsedTask,
            messages=messages
        )

        logger.info(f"Parsed task: {result.title}")
        return result

    async def estimate_time(
        self,
        task_title: str,
        task_context: Optional[str] = None,
        historical_data: Optional[List[Dict]] = None
    ) -> TimeEstimate:
        """
        Estimate task time using LLM

        Args:
            task_title: Task description
            task_context: Additional context
            historical_data: Similar past tasks with actual times

        Returns:
            TimeEstimate with estimate and reasoning
        """
        # Build prompt with historical data
        history_text = ""
        if historical_data:
            history_text = "Similar past tasks:\n"
            for task in historical_data[-10:]:
                history_text += (
                    f"- '{task['title']}': "
                    f"estimated {task['estimate']}min, "
                    f"actual {task['actual']}min\n"
                )
        else:
            history_text = "No historical data available"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a time estimation assistant. Estimate how long "
                    "tasks will take based on their description and historical "
                    "data. Be realistic and account for complexity."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Task: {task_title}\n"
                    f"Context: {task_context or 'None'}\n\n"
                    f"{history_text}\n\n"
                    "Provide time estimate, confidence level, reasoning, "
                    "and a helpful suggestion for the user."
                )
            }
        ]

        # Use fallback model (Claude) for time estimation
        # as it requires better reasoning
        result = await self.llm.complete(
            response_model=TimeEstimate,
            messages=messages,
            use_fallback=True  # Use Claude for complex reasoning
        )

        logger.info(
            f"Estimated {result.estimate_minutes}min "
            f"with {result.confidence} confidence"
        )
        return result
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_nlp.py::test_parse_task_basic -v
```

Expected: PASS (or skip if no API key for testing)

**Step 6: Commit NLP implementation**

```bash
git add bot/src/nlp.py bot/src/models.py bot/tests/test_nlp.py
git commit -m "feat: add task parsing with OpenRouter structured output"
```

---

### Task 2.3: AI Time Estimation

**Already included in Task 2.2** - The `estimate_time()` method uses Claude (fallback model) for better reasoning on time estimation while DeepSeek handles simpler task parsing.

**Strategy:**
- **DeepSeek (primary)**: Fast, cheap task parsing
- **Claude (fallback)**: Complex reasoning like time estimation

---

### Task 2.3: Update Config for OpenRouter

**Files:**
- Modify: `bot/src/config.py`

**Step 1: Update config.py**

```python
# bot/src/config.py
from pathlib import Path
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

# Logging setup
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment")

# OpenRouter LLM
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not set in environment")

LLM_MODEL_PRIMARY = os.getenv("LLM_MODEL_PRIMARY", "deepseek/deepseek-chat")
LLM_MODEL_FALLBACK = os.getenv("LLM_MODEL_FALLBACK", "anthropic/claude-3.5-sonnet")

# Google Calendar
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

# ntfy.sh
NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "productivity")

# Paths
BASE_DIR = Path(__file__).parent.parent
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR.parent / "data" / "productivity.db"))
VAULT_PATH = os.getenv("VAULT_PATH", str(BASE_DIR.parent / "obsidian-vault"))

# Timezone
TIMEZONE = os.getenv("TIMEZONE", "America/New_York")

# Bot Settings
SESSION_TIMEOUT_MINUTES = 30
MAX_CONVERSATION_MESSAGES = 5
```

**Step 2: Commit config updates**

```bash
git add bot/src/config.py
git commit -m "feat: add OpenRouter configuration"
```

---

### Task 2.4: Multi-Turn Conversation Support

**Files:**
- Create: `bot/src/conversation.py`
- Create: `bot/tests/test_conversation.py`

**Implementation:** Session management in SQLite with TTL, handle clarifying questions during task creation. Track conversation state, limit to 3-5 messages per session, auto-expire after 30 minutes.

**TDD Steps:** Write test for session creation → session expiry → message counting → context retrieval → implement ConversationManager class.

---

### Task 2.5: Voice Message Transcription

**Files:**
- Create: `bot/src/voice.py`
- Create: `bot/tests/test_voice.py`

**Implementation:** Integrate Whisper for voice transcription, add voice message handler to bot. Download voice file from Telegram → transcribe with Whisper → parse as task → show transcription to user for confirmation.

**TDD Steps:** Write test for voice file handling → transcription → error handling → implement VoiceHandler class.

---

## Phase 3: Calendar Integration (Days 6-8)

### Task 3.1: Google Calendar API Setup

**Files:**
- Create: `bot/src/calendar_integration.py`
- Create: `bot/tests/test_calendar.py`
- Create: `bot/scripts/setup_google_auth.py`

**Implementation:** OAuth2 flow, refresh token storage, API client wrapper.

### Task 3.2: Free/Busy Query & Time Blocking Logic

**Files:**
- Modify: `bot/src/calendar_integration.py`
- Modify: `bot/tests/test_calendar.py`

**Implementation:** Query Google Calendar for free/busy times, find available slots based on task duration and due date.

### Task 3.3: Calendar Event Creation

**Files:**
- Modify: `bot/src/calendar_integration.py`
- Modify: `bot/tests/test_calendar.py`

**Implementation:** Create calendar events with task details, link back to Obsidian via event description.

### Task 3.4: Bot Commands for Scheduling

**Files:**
- Modify: `bot/src/bot.py`
- Modify: `bot/tests/test_bot.py`

**Implementation:** Add /schedule, /suggest, /calendar commands with interactive time slot selection.

### Task 3.5: Bidirectional Calendar Sync

**Files:**
- Modify: `bot/src/calendar_integration.py`
- Modify: `bot/tests/test_calendar.py`

**Implementation:** Poll calendar for external changes, update tasks in Obsidian when calendar events modified.

---

## Phase 4: Scheduling & Notifications (Days 9-11)

### Task 4.1: APScheduler Setup

**Files:**
- Create: `bot/src/scheduler.py`
- Create: `bot/tests/test_scheduler.py`

**Implementation:** Configure APScheduler with timezone support, add cron jobs for check-ins.

### Task 4.2: Morning Check-in Logic

**Files:**
- Modify: `bot/src/scheduler.py`
- Create: `bot/src/checkins.py`
- Create: `bot/tests/test_checkins.py`

**Implementation:** 4:30 AM check-in with habit tracking, today's plan, energy level.

### Task 4.3: Periodic Check-ins

**Files:**
- Modify: `bot/src/scheduler.py`
- Modify: `bot/src/checkins.py`

**Implementation:** Every 2-3 hours during work day, "What are you working on?" prompts.

### Task 4.4: Evening Review

**Files:**
- Modify: `bot/src/scheduler.py`
- Modify: `bot/src/checkins.py`

**Implementation:** Flexible evening review triggered by "going to sleep" or 10 PM reminder.

### Task 4.5: ntfy.sh Push Notifications

**Files:**
- Create: `bot/src/notifications.py`
- Create: `bot/tests/test_notifications.py`

**Implementation:** Send push via ntfy.sh with priority levels, track acknowledgment.

### Task 4.6: Notification Escalation

**Files:**
- Modify: `bot/src/notifications.py`
- Modify: `bot/tests/test_notifications.py`

**Implementation:** Escalate priority if no response (normal → high → urgent at 5, 10, 15 min).

---

## Phase 5: Personal CRM & Daily Logs (Days 12-14)

### Task 5.1: People Management Commands

**Files:**
- Create: `bot/src/people.py`
- Create: `bot/tests/test_people.py`
- Modify: `bot/src/bot.py`

**Implementation:** /people, /person, /contact commands, create person files in Obsidian.

### Task 5.2: Task-People Linking

**Files:**
- Modify: `bot/src/obsidian_sync.py`
- Modify: `bot/tests/test_obsidian_sync.py`

**Implementation:** Track people_ids in tasks, query tasks by person.

### Task 5.3: Daily Log Generation

**Files:**
- Create: `bot/src/daily_log.py`
- Create: `bot/tests/test_daily_log.py`

**Implementation:** Auto-create daily log files, aggregate tasks/check-ins/habits.

### Task 5.4: Habit Tracking

**Files:**
- Modify: `bot/src/checkins.py`
- Modify: `bot/tests/test_checkins.py`

**Implementation:** Morning habit check-in, track completion, calculate streaks.

### Task 5.5: Conversation Summarization

**Files:**
- Create: `bot/src/summarization.py`
- Create: `bot/tests/test_summarization.py`

**Implementation:** Use Claude API to summarize daily conversations, store summaries not full history.

---

## Phase 6: Sync & Polish (Days 15-17)

### Task 6.1: Git Sync Setup

**Files:**
- Create: `obsidian-vault/.git/hooks/post-receive`
- Create: `bot/scripts/setup_git_sync.sh`

**Implementation:** Bare repo on VPS, post-receive hook to update working dir and rebuild index.

### Task 6.2: Conflict Resolution

**Files:**
- Create: `bot/src/git_sync.py`
- Create: `bot/tests/test_git_sync.py`

**Implementation:** Auto-resolve simple conflicts (last-write-wins), notify user via Telegram.

### Task 6.3: Bot Personality Refinement

**Files:**
- Modify: `bot/src/bot.py`
- Modify: `bot/src/checkins.py`

**Implementation:** Add encouraging messages, context awareness, improve tone.

### Task 6.4: Settings Command

**Files:**
- Create: `bot/src/settings.py`
- Create: `bot/tests/test_settings.py`
- Modify: `bot/src/bot.py`

**Implementation:** /settings command to configure timezone, check-in times, notification preferences.

---

## Phase 7: Testing & Deployment (Days 18-21)

### Task 7.1: End-to-End Tests

**Files:**
- Create: `bot/tests/test_e2e.py`

**Implementation:** Full workflow tests (task creation → scheduling → check-ins → completion).

### Task 7.2: Dockerfile & Docker Compose

**Files:**
- Create: `bot/Dockerfile`
- Create: `docker-compose.yml`

**Implementation:** Production-ready Docker image, docker-compose for local testing.

### Task 7.3: Coolify Deployment Config

**Files:**
- Create: `bot/coolify.json`
- Create: `docs/deployment.md`

**Implementation:** Coolify configuration, environment variables, volumes, health checks.

### Task 7.4: Backup Strategy

**Files:**
- Create: `bot/scripts/backup.sh`
- Create: `bot/scripts/restore.sh`

**Implementation:** Automated backups (git vault, SQLite database), recovery procedures.

### Task 7.5: Documentation

**Files:**
- Create: `docs/user-guide.md`
- Create: `docs/admin-guide.md`
- Create: `README.md`

**Implementation:** User guide for bot commands, admin guide for setup/maintenance, README for project overview.

---

## Pre-Implementation Setup

### Getting API Keys

**1. OpenRouter API Key (Required)**
- Sign up at: https://openrouter.ai/
- Go to Keys section
- Create new API key
- Add $5-10 credit (should last months)
- Set in `.env`: `OPENROUTER_API_KEY=sk-or-...`

**2. Telegram Bot Token (Required)**
- Message @BotFather on Telegram
- Create new bot with `/newbot`
- Copy token
- Set in `.env`: `TELEGRAM_BOT_TOKEN=...`

**3. Google Calendar API (Phase 3)**
- Setup instructions in Phase 3, Task 3.1

**4. ntfy.sh (Phase 4)**
- Can use public ntfy.sh or self-host
- Setup instructions in Phase 4

---

## Post-Implementation

### Verification Checklist

Use @superpowers:verification-before-completion before marking complete:

- [ ] All tests pass (`pytest -v`)
- [ ] Code coverage >80% (`pytest --cov`)
- [ ] Linting passes (`ruff check .`, `black --check .`)
- [ ] Can create task via Telegram
- [ ] Can schedule task on Google Calendar
- [ ] Morning check-in triggers at 4:30 AM
- [ ] Notifications sent via ntfy.sh
- [ ] Obsidian vault syncs bidirectionally
- [ ] Bot runs for 3 days without crashes
- [ ] Documentation complete

### Code Review

Use @superpowers:requesting-code-review after:
- Phase 3 (Calendar integration)
- Phase 4 (Scheduling & notifications)
- Phase 5 (CRM & daily logs)

### Finishing

Use @superpowers:finishing-a-development-branch when all phases complete and verified.

---

## Execution Options

**Ready to build? Two ways to execute this plan:**

**1. Subagent-Driven (this session)**
- I dispatch fresh subagent per task
- Review between tasks
- Fast iteration with guidance

**2. Parallel Session (separate)**
- Open new Claude Code session in worktree
- Use @superpowers:executing-plans
- Batch execution with checkpoints

**Which approach would you like?**
