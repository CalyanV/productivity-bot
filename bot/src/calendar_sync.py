import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
from .calendar_integration import CalendarIntegration
from .obsidian_sync import ObsidianSync
from .database import Database

logger = logging.getLogger(__name__)


class CalendarSync:
    """Bidirectional sync between Google Calendar and Obsidian tasks"""

    def __init__(
        self,
        db_path: str,
        vault_path: str,
        calendar_client_id: str,
        calendar_client_secret: str,
        calendar_refresh_token: str,
        timezone: str = "America/New_York"
    ):
        self.db_path = db_path
        self.vault_path = vault_path
        self.timezone = timezone

        self.db = Database(db_path)
        self.vault_sync = ObsidianSync(vault_path)
        self.calendar = CalendarIntegration(
            client_id=calendar_client_id,
            client_secret=calendar_client_secret,
            refresh_token=calendar_refresh_token,
            timezone=timezone
        )

    async def initialize(self):
        """Initialize database and ensure sync table exists"""
        await self.db.initialize()

        # calendar_sync table is already created in the schema
        logger.info("Calendar sync initialized")

    async def get_last_sync_time(self) -> Optional[datetime]:
        """Get the last successful sync time"""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT last_sync_at FROM calendar_sync WHERE id = 1"
            )
            row = await cursor.fetchone()

            if row and row[0]:
                return datetime.fromisoformat(row[0])
            return None

    async def get_sync_token(self) -> Optional[str]:
        """Get the stored sync token for incremental sync"""
        async with aiosqlite.connect(self.db_path) as conn:
            cursor = await conn.execute(
                "SELECT sync_token FROM calendar_sync WHERE id = 1"
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def update_sync_time(self, sync_time: datetime, sync_token: Optional[str] = None):
        """Update the last sync time and token"""
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT OR REPLACE INTO calendar_sync (id, last_sync_at, sync_token)
                VALUES (1, ?, ?)
            """, (sync_time.isoformat(), sync_token))
            await conn.commit()

        logger.info(f"Updated sync time to {sync_time}")

    async def sync_calendar_to_tasks(self, calendar_id: str = 'primary'):
        """
        Poll calendar for changes and update tasks in Obsidian

        This detects:
        - Events that were rescheduled
        - Events that were deleted
        - Events that were modified
        """
        logger.info("Starting calendar -> tasks sync")

        try:
            last_sync = await self.get_last_sync_time()
            sync_token = await self.get_sync_token()

            # Get events since last sync
            time_min = last_sync or (datetime.now() - timedelta(days=7))
            time_max = datetime.now() + timedelta(days=30)

            events = await self.calendar.get_events(
                calendar_id=calendar_id,
                time_min=time_min,
                time_max=time_max,
                max_results=500
            )

            updates_count = 0

            for event in events:
                # Check if this event is linked to a task
                description = event.get('description', '')

                if 'Task ID:' not in description:
                    continue  # Not a task-linked event

                # Extract task ID from description
                task_id = self._extract_task_id(description)
                if not task_id:
                    continue

                # Get current task data
                task = await self._get_task(task_id)
                if not task:
                    logger.warning(f"Task {task_id} not found for event {event['id']}")
                    continue

                # Check if event was modified
                event_start = event.get('start', {}).get('dateTime')
                event_end = event.get('end', {}).get('dateTime')

                if not event_start or not event_end:
                    continue  # Skip all-day events

                # Parse event times
                start_dt = datetime.fromisoformat(event_start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(event_end.replace('Z', '+00:00'))

                # Update task if calendar event changed
                needs_update = False
                updates = {}

                if task['scheduled_start'] != start_dt.isoformat():
                    updates['scheduled_start'] = start_dt.isoformat()
                    needs_update = True

                if task['scheduled_end'] != end_dt.isoformat():
                    updates['scheduled_end'] = end_dt.isoformat()
                    needs_update = True

                if task['calendar_event_id'] != event['id']:
                    updates['calendar_event_id'] = event['id']
                    needs_update = True

                if needs_update:
                    # Update task in Obsidian
                    await self.vault_sync.update_task_file(task_id, updates)

                    # Update in database
                    await self._update_task_in_db(task_id, updates)

                    updates_count += 1
                    logger.info(f"Updated task {task_id} from calendar changes")

            # Update sync time
            await self.update_sync_time(datetime.now(), sync_token)

            logger.info(f"Calendar sync completed: {updates_count} tasks updated")
            return updates_count

        except Exception as e:
            logger.error(f"Error syncing calendar to tasks: {e}", exc_info=True)
            raise

    async def sync_tasks_to_calendar(self, calendar_id: str = 'primary'):
        """
        Check tasks for changes and update calendar events

        This detects:
        - Tasks that were completed (mark event)
        - Tasks that were deleted (remove event)
        - Tasks whose details changed (update event)
        """
        logger.info("Starting tasks -> calendar sync")

        try:
            # Get all tasks with calendar events
            async with aiosqlite.connect(self.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute("""
                    SELECT * FROM tasks
                    WHERE calendar_event_id IS NOT NULL
                """)
                tasks = [dict(row) for row in await cursor.fetchall()]

            updates_count = 0

            for task in tasks:
                try:
                    event_id = task['calendar_event_id']

                    # Check if task was completed
                    if task['status'] == 'completed' and task['completed_at']:
                        # Update event to mark as completed
                        await self.calendar.update_event(
                            event_id=event_id,
                            updates={
                                'summary': f"✅ {task['title']}",
                                'colorId': '10'  # Green color for completed
                            },
                            calendar_id=calendar_id
                        )
                        updates_count += 1
                        logger.info(f"Marked event {event_id} as completed")

                    elif task['status'] == 'cancelled':
                        # Delete the calendar event
                        await self.calendar.delete_event(event_id, calendar_id)
                        updates_count += 1
                        logger.info(f"Deleted event {event_id} for cancelled task")

                except Exception as e:
                    logger.error(f"Error syncing task {task['id']}: {e}")
                    continue

            logger.info(f"Tasks sync completed: {updates_count} events updated")
            return updates_count

        except Exception as e:
            logger.error(f"Error syncing tasks to calendar: {e}", exc_info=True)
            raise

    async def run_bidirectional_sync(self, calendar_id: str = 'primary'):
        """Run full bidirectional sync"""
        logger.info("Starting bidirectional sync")

        # Sync calendar changes to tasks first
        calendar_updates = await self.sync_calendar_to_tasks(calendar_id)

        # Then sync task changes to calendar
        task_updates = await self.sync_tasks_to_calendar(calendar_id)

        logger.info(
            f"Bidirectional sync completed: "
            f"{calendar_updates} tasks updated, {task_updates} events updated"
        )

        return {
            'calendar_to_tasks': calendar_updates,
            'tasks_to_calendar': task_updates
        }

    def _extract_task_id(self, description: str) -> Optional[str]:
        """Extract task ID from event description"""
        # Format: "Task ID: task-123"
        for line in description.split('\n'):
            if line.startswith('Task ID:'):
                return line.split('Task ID:')[1].strip()
        return None

    async def _get_task(self, task_id: str) -> Optional[Dict]:
        """Get task from database"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def _update_task_in_db(self, task_id: str, updates: Dict):
        """Update task in database"""
        # Build UPDATE query
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(task_id)

        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                f"UPDATE tasks SET {set_clause} WHERE id = ?",
                values
            )
            await conn.commit()
