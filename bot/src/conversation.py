import aiosqlite
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
import json

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manage multi-turn conversations with session tracking"""

    def __init__(self, db_path: str, timeout_minutes: int = 30, max_messages: int = 5):
        self.db_path = db_path
        self.timeout_minutes = timeout_minutes
        self.max_messages = max_messages

    async def initialize(self):
        """Initialize database tables"""
        from .database import Database
        db = Database(self.db_path)
        await db.initialize()

        # Create conversation messages table
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES bot_sessions(session_id)
                )
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_messages_session
                ON conversation_messages(session_id, created_at)
            """)
            await conn.commit()

    async def create_session(
        self,
        telegram_user_id: int,
        telegram_chat_id: int,
        context_type: str = "general",
        context_data: Optional[Dict] = None
    ) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        expires_at = now + timedelta(minutes=self.timeout_minutes)

        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT INTO bot_sessions (
                    session_id, telegram_user_id, telegram_chat_id,
                    created_at, updated_at, expires_at,
                    context_type, context_data, message_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                telegram_user_id,
                telegram_chat_id,
                now.isoformat(),
                now.isoformat(),
                expires_at.isoformat(),
                context_type,
                json.dumps(context_data) if context_data else None,
                0
            ))
            await conn.commit()

        logger.info(f"Created conversation session: {session_id}")
        return session_id

    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID, returns None if expired"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT * FROM bot_sessions
                WHERE session_id = ?
            """, (session_id,))
            row = await cursor.fetchone()

            if not row:
                return None

            session = dict(row)

            # Check if expired
            expires_at = datetime.fromisoformat(session["expires_at"])
            if datetime.now() > expires_at:
                logger.info(f"Session {session_id} expired")
                return None

            # Parse context_data JSON
            if session["context_data"]:
                session["context_data"] = json.loads(session["context_data"])

            return session

    async def add_message(self, session_id: str, role: str, content: str):
        """Add a message to the session"""
        message_id = str(uuid.uuid4())
        now = datetime.now()

        async with aiosqlite.connect(self.db_path) as conn:
            # Insert message
            await conn.execute("""
                INSERT INTO conversation_messages (
                    id, session_id, role, content, created_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (message_id, session_id, role, content, now.isoformat()))

            # Update session message count and updated_at
            await conn.execute("""
                UPDATE bot_sessions
                SET message_count = message_count + 1,
                    updated_at = ?
                WHERE session_id = ?
            """, (now.isoformat(), session_id))

            await conn.commit()

        logger.debug(f"Added {role} message to session {session_id}")

    async def get_messages(self, session_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get all messages for a session"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row

            query = """
                SELECT id, role, content, created_at
                FROM conversation_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor = await conn.execute(query, (session_id,))
            rows = await cursor.fetchall()

            return [dict(row) for row in rows]

    async def is_at_message_limit(self, session_id: str) -> bool:
        """Check if session has reached message limit"""
        session = await self.get_session(session_id)
        if not session:
            return True

        return session["message_count"] >= self.max_messages

    async def get_or_create_session(
        self,
        telegram_user_id: int,
        telegram_chat_id: int,
        context_type: str = "general"
    ) -> str:
        """Get active session for user or create new one"""
        # Check for active session
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT session_id, expires_at FROM bot_sessions
                WHERE telegram_user_id = ?
                  AND context_type = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (telegram_user_id, context_type))
            row = await cursor.fetchone()

            if row:
                expires_at = datetime.fromisoformat(row["expires_at"])
                if datetime.now() < expires_at:
                    logger.info(f"Reusing existing session: {row['session_id']}")
                    return row["session_id"]

        # Create new session
        return await self.create_session(
            telegram_user_id=telegram_user_id,
            telegram_chat_id=telegram_chat_id,
            context_type=context_type
        )

    async def end_session(self, session_id: str):
        """End a session by setting expiry to now"""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                UPDATE bot_sessions
                SET expires_at = ?
                WHERE session_id = ?
            """, (datetime.now().isoformat(), session_id))
            await conn.commit()

        logger.info(f"Ended session: {session_id}")

    async def cleanup_expired_sessions(self):
        """Remove expired sessions and their messages"""
        now = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_path) as conn:
            # Get expired session IDs
            cursor = await conn.execute("""
                SELECT session_id FROM bot_sessions
                WHERE expires_at < ?
            """, (now,))
            expired_sessions = [row[0] for row in await cursor.fetchall()]

            if expired_sessions:
                # Delete messages
                placeholders = ','.join('?' * len(expired_sessions))
                await conn.execute(f"""
                    DELETE FROM conversation_messages
                    WHERE session_id IN ({placeholders})
                """, expired_sessions)

                # Delete sessions
                await conn.execute(f"""
                    DELETE FROM bot_sessions
                    WHERE session_id IN ({placeholders})
                """, expired_sessions)

                await conn.commit()
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
