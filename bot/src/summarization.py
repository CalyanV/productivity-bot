import aiosqlite
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import logging
from .database import Database
from .llm_client import LLMClient

logger = logging.getLogger(__name__)


class ConversationSummary(BaseModel):
    """Structured conversation summary"""

    summary: str = Field(description="Brief summary of the conversation in 1-2 sentences")
    key_points: List[str] = Field(
        default_factory=list,
        description="Key points and topics discussed"
    )
    action_items: List[str] = Field(
        default_factory=list,
        description="Action items or tasks mentioned"
    )
    people_mentioned: List[str] = Field(
        default_factory=list,
        description="Names of people mentioned in the conversation"
    )
    sentiment: str = Field(
        default="neutral",
        description="Overall sentiment: positive, neutral, or negative"
    )


class ConversationSummarizer:
    """Summarize conversations using LLM to save storage"""

    def __init__(
        self,
        db_path: str,
        llm_api_key: str,
        primary_model: str = "deepseek/deepseek-chat",
        fallback_model: str = "anthropic/claude-3.5-sonnet"
    ):
        self.db_path = db_path
        self.llm_api_key = llm_api_key
        self.db = Database(db_path)
        self.llm = LLMClient(
            api_key=llm_api_key,
            primary_model=primary_model,
            fallback_model=fallback_model
        )

    async def initialize(self):
        """Initialize database"""
        await self.db.initialize()

    async def summarize_conversation(
        self,
        messages: List[Dict],
        include_context: bool = True
    ) -> Dict:
        """
        Summarize a conversation using LLM

        Args:
            messages: List of message dicts with role and content
            include_context: Include additional context in summary

        Returns:
            Dictionary with summary, key_points, action_items, etc.
        """
        # Build conversation text
        conversation_text = self._format_conversation(messages)

        # Create prompt for summarization
        system_prompt = """You are a conversation summarization assistant.
Analyze the conversation and provide:
1. A brief summary (1-2 sentences)
2. Key points discussed
3. Action items or tasks mentioned
4. People mentioned by name
5. Overall sentiment

Be concise and focus on actionable information."""

        user_prompt = f"""Summarize this conversation:

{conversation_text}

Provide a structured summary."""

        messages_for_llm = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # Use LLM for summarization
            result = await self.llm.complete(
                response_model=ConversationSummary,
                messages=messages_for_llm
            )

            summary_dict = {
                "summary": result.summary,
                "key_points": result.key_points,
                "action_items": result.action_items,
                "people_mentioned": result.people_mentioned,
                "sentiment": result.sentiment
            }

            logger.info(f"Summarized conversation: {result.summary[:50]}...")
            return summary_dict

        except Exception as e:
            logger.error(f"Error summarizing conversation: {e}", exc_info=True)
            # Fallback to simple summary
            return {
                "summary": "Conversation summary unavailable",
                "key_points": [],
                "action_items": [],
                "people_mentioned": [],
                "sentiment": "neutral",
                "error": str(e)
            }

    async def store_summary(
        self,
        telegram_user_id: int,
        date: str,
        summary_data: Dict
    ) -> str:
        """
        Store conversation summary in database

        Args:
            telegram_user_id: Telegram user ID
            date: Date of conversation (YYYY-MM-DD)
            summary_data: Summary dictionary from summarize_conversation

        Returns:
            Summary ID
        """
        summary_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # Convert summary_data to JSON
        summary_json = json.dumps(summary_data)

        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT INTO conversation_summaries (
                    id, telegram_user_id, date, summary, created_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                summary_id,
                telegram_user_id,
                date,
                summary_json,
                now
            ))
            await conn.commit()

        logger.info(f"Stored conversation summary: {summary_id}")
        return summary_id

    async def get_recent_summaries(
        self,
        telegram_user_id: int,
        days: int = 7
    ) -> List[Dict]:
        """
        Get recent conversation summaries

        Args:
            telegram_user_id: Telegram user ID
            days: Number of days to look back

        Returns:
            List of summary dictionaries
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT * FROM conversation_summaries
                WHERE telegram_user_id = ?
                  AND date >= ?
                ORDER BY date DESC
            """, (telegram_user_id, cutoff_date))
            rows = await cursor.fetchall()

            summaries = []
            for row in rows:
                summary_dict = dict(row)
                # Parse JSON summary
                summary_dict["summary"] = json.loads(summary_dict["summary"])
                summaries.append(summary_dict)

            return summaries

    async def summarize_session(
        self,
        session_id: str
    ) -> Optional[Dict]:
        """
        Summarize a conversation session

        Args:
            session_id: Session ID from conversation manager

        Returns:
            Summary dictionary or None if session not found
        """
        # Get messages from session
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row

            # Get session info
            cursor = await conn.execute("""
                SELECT telegram_user_id FROM bot_sessions
                WHERE session_id = ?
            """, (session_id,))
            session = await cursor.fetchone()

            if not session:
                logger.warning(f"Session not found: {session_id}")
                return None

            telegram_user_id = session["telegram_user_id"]

            # Get messages
            cursor = await conn.execute("""
                SELECT role, content FROM conversation_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
            """, (session_id,))
            messages = [dict(row) for row in await cursor.fetchall()]

        if not messages:
            return None

        # Summarize
        summary_data = await self.summarize_conversation(messages)

        # Store summary
        today = datetime.now().strftime("%Y-%m-%d")
        await self.store_summary(telegram_user_id, today, summary_data)

        logger.info(f"Summarized session: {session_id}")

        return summary_data

    async def cleanup_old_messages(
        self,
        days_to_keep: int = 30
    ) -> int:
        """
        Delete old conversation messages (summaries are kept)

        Args:
            days_to_keep: Number of days to keep full messages

        Returns:
            Number of messages deleted
        """
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        async with aiosqlite.connect(self.db_path) as conn:
            # Get count before deletion
            cursor = await conn.execute("""
                SELECT COUNT(*) FROM conversation_messages
                WHERE created_at < ?
            """, (cutoff_date,))
            count = (await cursor.fetchone())[0]

            # Delete old messages
            await conn.execute("""
                DELETE FROM conversation_messages
                WHERE created_at < ?
            """, (cutoff_date,))
            await conn.commit()

        logger.info(f"Deleted {count} old conversation messages")
        return count

    def _format_conversation(self, messages: List[Dict]) -> str:
        """Format conversation messages for summarization"""
        formatted_lines = []

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            role_label = {
                "user": "User",
                "assistant": "Assistant",
                "system": "System"
            }.get(role, role.title())

            formatted_lines.append(f"{role_label}: {content}")

        return "\n".join(formatted_lines)
