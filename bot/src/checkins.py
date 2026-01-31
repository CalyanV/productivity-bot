import aiosqlite
import uuid
from datetime import datetime, date
from typing import Dict, List, Optional
import logging
from .database import Database
from .obsidian_sync import ObsidianSync
from .personality import BotPersonality

logger = logging.getLogger(__name__)


class CheckinManager:
    """Manage daily check-ins (morning, evening, periodic)"""

    def __init__(self, db_path: str, vault_path: str):
        self.db_path = db_path
        self.vault_path = vault_path
        self.db = Database(db_path)
        self.vault_sync = ObsidianSync(vault_path)

    async def initialize(self):
        """Initialize database"""
        await self.db.initialize()

    def get_morning_checkin_prompt(self) -> str:
        """Get the morning check-in prompt message"""
        greeting = BotPersonality.get_greeting()
        encouragement = BotPersonality.get_morning_encouragement()

        return f"""{greeting} Time for your daily check-in.

{encouragement}

**Energy Level** (1-10):
How are you feeling physically and mentally?

**Mood**:
In a word or two, how would you describe your mood?

**Daily Habits**:
✅ Exercise
✅ Meditation
✅ Healthy breakfast
✅ [Custom habits you track]

**Today's Top 3 Priorities**:
1.
2.
3.

Reply with your check-in or send voice message!"""

    def get_evening_review_prompt(self) -> str:
        """Get the evening review prompt message"""
        reflection = BotPersonality.get_evening_reflection()

        return f"""{reflection}

**Energy Level** (1-10):
How do you feel now?

**Mood**:
How would you describe your mood this evening?

**What did you accomplish today?**
List completed tasks and wins

**What's still pending?**
Unfinished items to carry over

**One thing you learned today?**

**Tomorrow's Top Priority**:
What's the most important thing to do tomorrow?

Reply to complete your evening review!"""

    def get_periodic_checkin_prompt(self) -> str:
        """Get the periodic check-in prompt"""
        reminder_tone = BotPersonality.get_reminder_tone()

        return f"""⏰ {reminder_tone}

**What are you working on right now?**

This helps track your actual work vs. planned tasks.
Reply briefly to log your current focus."""

    async def create_morning_checkin(self, checkin_data: Dict) -> Dict:
        """
        Create a morning check-in

        Args:
            checkin_data: Dictionary with date, energy_level, mood, habits, priorities

        Returns:
            Created check-in info with log_id
        """
        today = checkin_data.get("date") or datetime.now().strftime("%Y-%m-%d")
        log_id = f"log-{today}"
        now = datetime.now().isoformat()

        # Check if log already exists
        existing = await self.get_checkin_by_date(today)

        if existing:
            # Update existing log
            await self._update_morning_checkin(log_id, checkin_data)
            logger.info(f"Updated morning check-in for {today}")
        else:
            # Create new daily log
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                    INSERT INTO daily_logs (
                        id, date, created_at, morning_checkin_at,
                        energy_level_morning, file_path
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    log_id,
                    today,
                    now,
                    now,
                    checkin_data.get("energy_level"),
                    f"04-daily-logs/{today}.md"
                ))
                await conn.commit()

            # Save habits
            if "habits" in checkin_data:
                await self._save_habits(log_id, checkin_data["habits"])

            # Create Obsidian file
            await self._create_daily_log_file(log_id, today, checkin_data)

            logger.info(f"Created morning check-in for {today}")

        return {
            "log_id": log_id,
            "date": today,
            "type": "morning"
        }

    async def create_evening_review(self, review_data: Dict) -> Dict:
        """
        Create an evening review

        Args:
            review_data: Dictionary with date, energy_level, accomplishments, learnings

        Returns:
            Updated review info
        """
        today = review_data.get("date") or datetime.now().strftime("%Y-%m-%d")
        log_id = f"log-{today}"
        now = datetime.now().isoformat()

        # Get or create daily log
        existing = await self.get_checkin_by_date(today)

        if not existing:
            # Create new log
            async with aiosqlite.connect(self.db_path) as conn:
                await conn.execute("""
                    INSERT INTO daily_logs (
                        id, date, created_at, file_path
                    ) VALUES (?, ?, ?, ?)
                """, (
                    log_id,
                    today,
                    now,
                    f"04-daily-logs/{today}.md"
                ))
                await conn.commit()

        # Update with evening data
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                UPDATE daily_logs
                SET evening_review_at = ?,
                    energy_level_evening = ?
                WHERE id = ?
            """, (
                now,
                review_data.get("energy_level"),
                log_id
            ))
            await conn.commit()

        # Update Obsidian file
        await self._update_daily_log_with_evening(log_id, review_data)

        logger.info(f"Created evening review for {today}")

        return {
            "log_id": log_id,
            "date": today,
            "type": "evening"
        }

    async def add_periodic_checkin(self, checkin_data: Dict) -> Dict:
        """
        Add a periodic check-in note

        Args:
            checkin_data: Dictionary with timestamp and activity

        Returns:
            Check-in info
        """
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%I:%M %p")

        # Ensure daily log exists
        log_id = f"log-{today}"
        existing = await self.get_checkin_by_date(today)

        if not existing:
            await self.create_morning_checkin({"date": today})

        # Append to Obsidian file
        activity = checkin_data.get("activity", "Working")
        note = f"\n### {timestamp}\n{activity}\n"

        await self._append_to_daily_log(log_id, "Check-ins Throughout Day", note)

        logger.info(f"Added periodic check-in at {timestamp}")

        return {
            "log_id": log_id,
            "timestamp": timestamp,
            "activity": activity
        }

    async def get_todays_checkin(self) -> Optional[Dict]:
        """Get today's check-in if it exists"""
        today = datetime.now().strftime("%Y-%m-%d")
        return await self.get_checkin_by_date(today)

    async def get_checkin_by_date(self, date_str: str) -> Optional[Dict]:
        """Get check-in for a specific date"""
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT * FROM daily_logs
                WHERE date = ?
            """, (date_str,))
            row = await cursor.fetchone()

            if row:
                return dict(row)
            return None

    async def _update_morning_checkin(self, log_id: str, checkin_data: Dict):
        """Update existing morning check-in"""
        now = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                UPDATE daily_logs
                SET morning_checkin_at = ?,
                    energy_level_morning = ?
                WHERE id = ?
            """, (
                now,
                checkin_data.get("energy_level"),
                log_id
            ))
            await conn.commit()

        # Update habits
        if "habits" in checkin_data:
            await self._save_habits(log_id, checkin_data["habits"])

    async def _save_habits(self, log_id: str, habits: Dict):
        """Save habit completion data"""
        async with aiosqlite.connect(self.db_path) as conn:
            # Clear existing habits
            await conn.execute(
                "DELETE FROM daily_log_habits WHERE log_id = ?",
                (log_id,)
            )

            # Insert new habits
            for habit_key, completed in habits.items():
                await conn.execute("""
                    INSERT INTO daily_log_habits (log_id, habit_key, completed)
                    VALUES (?, ?, ?)
                """, (log_id, habit_key, 1 if completed else 0))

            await conn.commit()

    async def _create_daily_log_file(self, log_id: str, date_str: str, checkin_data: Dict):
        """Create Obsidian daily log file"""
        from pathlib import Path

        file_path = Path(self.vault_path) / "04-daily-logs" / f"{date_str}.md"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Format date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%A, %B %d, %Y")

        # Build content
        content = f"""---
id: {log_id}
type: daily_log
date: {date_str}
created_at: {datetime.now().isoformat()}
morning_checkin_at: {datetime.now().isoformat()}
energy_level_morning: {checkin_data.get('energy_level', '')}
---

# Daily Log - {formatted_date}

## Morning Check-in
**Energy**: {checkin_data.get('energy_level', '')}/10
**Mood**: {checkin_data.get('mood', '')}

### Habits
"""

        # Add habits
        habits = checkin_data.get("habits", {})
        for habit, completed in habits.items():
            check = "✅" if completed else "⬜"
            content += f"{check} {habit.replace('_', ' ').title()}\n"

        content += "\n### Today's Plan\n"

        # Add priorities
        priorities = checkin_data.get("priorities", [])
        for i, priority in enumerate(priorities, 1):
            content += f"{i}. {priority}\n"

        content += """
**Total Planned**:

## Check-ins Throughout Day


## Evening Review
**Energy**: /10
**Mood**:

### Completed


### Not Completed


### Learnings


### Tomorrow's Priorities

"""

        # Write file
        with open(file_path, 'w') as f:
            f.write(content)

        logger.info(f"Created daily log file: {file_path}")

    async def _update_daily_log_with_evening(self, log_id: str, review_data: Dict):
        """Update daily log file with evening review data"""
        # This would update the Obsidian file
        # For now, we'll implement basic version
        pass

    async def _append_to_daily_log(self, log_id: str, section: str, content: str):
        """Append content to a section in daily log"""
        # This would append to the Obsidian file
        # For now, basic implementation
        pass
