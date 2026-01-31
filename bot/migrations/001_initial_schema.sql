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
