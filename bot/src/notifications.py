import aiosqlite
import uuid
import requests
import asyncio
from datetime import datetime
from typing import Dict, Optional
import logging
from .database import Database

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manage push notifications via ntfy.sh"""

    def __init__(
        self,
        db_path: str,
        ntfy_url: str = "https://ntfy.sh",
        ntfy_topic: str = "productivity"
    ):
        self.db_path = db_path
        self.ntfy_url = ntfy_url.rstrip('/')
        self.ntfy_topic = ntfy_topic
        self.db = Database(db_path)

    async def initialize(self):
        """Initialize database"""
        await self.db.initialize()

    async def send_notification(
        self,
        title: str,
        message: str,
        priority: str = "default",
        tags: Optional[list] = None,
        click_url: Optional[str] = None
    ) -> Dict:
        """
        Send a push notification via ntfy.sh

        Args:
            title: Notification title
            message: Notification message
            priority: Priority level (min, low, default, high, urgent)
            tags: Optional list of emoji tags
            click_url: Optional URL to open when clicked

        Returns:
            Notification info with ID
        """
        notification_id = str(uuid.uuid4())

        # Build ntfy.sh request
        url = f"{self.ntfy_url}/{self.ntfy_topic}"

        headers = {
            "Title": title,
            "Priority": priority,
            "Tags": ",".join(tags) if tags else "loudspeaker"
        }

        if click_url:
            headers["Click"] = click_url

        try:
            # Send notification in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    url,
                    data=message.encode('utf-8'),
                    headers=headers
                )
            )

            if response.status_code == 200:
                logger.info(f"Sent notification: {title}")
                return {
                    "notification_id": notification_id,
                    "sent": True,
                    "title": title
                }
            else:
                logger.error(f"Failed to send notification: {response.status_code}")
                return {
                    "notification_id": notification_id,
                    "sent": False,
                    "error": response.text
                }

        except Exception as e:
            logger.error(f"Error sending notification: {e}", exc_info=True)
            return {
                "notification_id": notification_id,
                "sent": False,
                "error": str(e)
            }

    async def track_notification(
        self,
        notification_type: str,
        scheduled_for: datetime,
        priority: str = "default"
    ) -> str:
        """
        Track a notification in the database

        Args:
            notification_type: Type of notification (morning_checkin, etc.)
            scheduled_for: When notification should be sent
            priority: Priority level

        Returns:
            Notification ID
        """
        notification_id = str(uuid.uuid4())

        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT INTO notifications (
                    id, type, scheduled_for
                ) VALUES (?, ?, ?)
            """, (
                notification_id,
                notification_type,
                scheduled_for.isoformat()
            ))
            await conn.commit()

        logger.info(f"Tracked notification: {notification_id} ({notification_type})")
        return notification_id

    async def mark_as_sent(self, notification_id: str):
        """Mark notification as sent"""
        now = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                UPDATE notifications
                SET sent_at = ?
                WHERE id = ?
            """, (now, notification_id))
            await conn.commit()

        logger.info(f"Marked notification as sent: {notification_id}")

    async def acknowledge_notification(
        self,
        notification_id: str,
        response_summary: Optional[str] = None
    ):
        """
        Mark notification as acknowledged

        Args:
            notification_id: Notification ID
            response_summary: Optional summary of user's response
        """
        now = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                UPDATE notifications
                SET acknowledged_at = ?,
                    response_summary = ?
                WHERE id = ?
            """, (now, response_summary, notification_id))
            await conn.commit()

        logger.info(f"Acknowledged notification: {notification_id}")

    async def get_notification(self, notification_id: str) -> Optional[Dict]:
        """Get notification by ID"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT * FROM notifications
                WHERE id = ?
            """, (notification_id,))
            row = await cursor.fetchone()

            if row:
                return dict(row)
            return None

    async def get_pending_notifications(self) -> list:
        """Get all pending (sent but not acknowledged) notifications"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT * FROM notifications
                WHERE sent_at IS NOT NULL
                  AND acknowledged_at IS NULL
                ORDER BY sent_at DESC
            """)
            rows = await cursor.fetchall()

            return [dict(row) for row in rows]

    async def send_morning_checkin_notification(self) -> Dict:
        """Send morning check-in notification"""
        return await self.send_notification(
            title="🌅 Morning Check-in",
            message="Good morning! Time for your daily check-in.",
            priority="high",
            tags=["sunrise", "calendar"]
        )

    async def send_periodic_checkin_notification(self) -> Dict:
        """Send periodic check-in notification"""
        return await self.send_notification(
            title="⏰ Quick Check-in",
            message="What are you working on right now?",
            priority="default",
            tags=["clock"]
        )

    async def send_evening_review_notification(self) -> Dict:
        """Send evening review notification"""
        return await self.send_notification(
            title="🌙 Evening Review",
            message="Time to reflect on your day!",
            priority="high",
            tags=["moon", "checkered_flag"]
        )

    async def send_task_reminder(self, task_title: str, due_time: str) -> Dict:
        """Send task reminder notification"""
        return await self.send_notification(
            title=f"📋 Reminder: {task_title}",
            message=f"This task is due {due_time}",
            priority="high",
            tags=["alarm_clock", "memo"]
        )
