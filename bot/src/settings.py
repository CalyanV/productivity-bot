"""
User settings and preferences management
"""

import aiosqlite
import json
from datetime import time
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class UserSettings:
    """Manage user preferences and settings"""

    DEFAULT_SETTINGS = {
        "timezone": "America/New_York",
        "morning_checkin_time": "04:30",
        "evening_checkin_time": "20:00",
        "periodic_checkin_enabled": True,
        "periodic_checkin_interval_hours": 2,
        "periodic_checkin_start_hour": 9,
        "periodic_checkin_end_hour": 17,
        "notification_priority": "default",
        "notification_tags": ["productivity", "tasks"],
        "work_hours_start": 9,
        "work_hours_end": 17,
        "exclude_weekends": True,
        "language": "en"
    }

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        """Initialize settings table"""
        async with aiosqlite.connect(self.db_path) as conn:
            # Create settings table if not exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    telegram_user_id INTEGER PRIMARY KEY,
                    settings TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            await conn.commit()

    async def get_settings(self, telegram_user_id: int) -> Dict[str, Any]:
        """
        Get user settings or return defaults

        Args:
            telegram_user_id: Telegram user ID

        Returns:
            Dictionary of settings
        """
        async with aiosqlite.connect(self.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT settings FROM user_settings
                WHERE telegram_user_id = ?
            """, (telegram_user_id,))
            row = await cursor.fetchone()

            if row:
                # Parse stored settings and merge with defaults
                stored_settings = json.loads(row["settings"])
                settings = {**self.DEFAULT_SETTINGS, **stored_settings}
                return settings

            # Return defaults for new user
            return self.DEFAULT_SETTINGS.copy()

    async def update_settings(
        self,
        telegram_user_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user settings

        Args:
            telegram_user_id: Telegram user ID
            updates: Dictionary of settings to update

        Returns:
            Updated settings dictionary
        """
        from datetime import datetime

        # Get current settings
        current_settings = await self.get_settings(telegram_user_id)

        # Apply updates
        current_settings.update(updates)

        # Validate settings
        validated_settings = self._validate_settings(current_settings)

        # Store updated settings
        settings_json = json.dumps(validated_settings)
        now = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_path) as conn:
            # Upsert settings
            await conn.execute("""
                INSERT INTO user_settings (telegram_user_id, settings, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(telegram_user_id) DO UPDATE SET
                    settings = excluded.settings,
                    updated_at = excluded.updated_at
            """, (telegram_user_id, settings_json, now, now))
            await conn.commit()

        logger.info(f"Updated settings for user {telegram_user_id}")
        return validated_settings

    async def reset_settings(self, telegram_user_id: int) -> Dict[str, Any]:
        """
        Reset user settings to defaults

        Args:
            telegram_user_id: Telegram user ID

        Returns:
            Default settings
        """
        from datetime import datetime

        settings_json = json.dumps(self.DEFAULT_SETTINGS)
        now = datetime.now().isoformat()

        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute("""
                INSERT INTO user_settings (telegram_user_id, settings, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(telegram_user_id) DO UPDATE SET
                    settings = excluded.settings,
                    updated_at = excluded.updated_at
            """, (telegram_user_id, settings_json, now, now))
            await conn.commit()

        logger.info(f"Reset settings for user {telegram_user_id}")
        return self.DEFAULT_SETTINGS.copy()

    def _validate_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate settings values

        Args:
            settings: Settings dictionary to validate

        Returns:
            Validated settings
        """
        validated = settings.copy()

        # Validate time strings (HH:MM format)
        for time_field in ["morning_checkin_time", "evening_checkin_time"]:
            if time_field in validated:
                try:
                    time.fromisoformat(validated[time_field])
                except ValueError:
                    logger.warning(f"Invalid time format for {time_field}: {validated[time_field]}")
                    validated[time_field] = self.DEFAULT_SETTINGS[time_field]

        # Validate hours (0-23)
        for hour_field in ["periodic_checkin_start_hour", "periodic_checkin_end_hour",
                          "work_hours_start", "work_hours_end"]:
            if hour_field in validated:
                hour = validated[hour_field]
                if not isinstance(hour, int) or hour < 0 or hour > 23:
                    logger.warning(f"Invalid hour for {hour_field}: {hour}")
                    validated[hour_field] = self.DEFAULT_SETTINGS[hour_field]

        # Validate interval hours (1-12)
        if "periodic_checkin_interval_hours" in validated:
            interval = validated["periodic_checkin_interval_hours"]
            if not isinstance(interval, int) or interval < 1 or interval > 12:
                logger.warning(f"Invalid interval: {interval}")
                validated["periodic_checkin_interval_hours"] = self.DEFAULT_SETTINGS["periodic_checkin_interval_hours"]

        # Validate notification priority
        if "notification_priority" in validated:
            priority = validated["notification_priority"]
            valid_priorities = ["min", "low", "default", "high", "urgent"]
            if priority not in valid_priorities:
                logger.warning(f"Invalid notification priority: {priority}")
                validated["notification_priority"] = self.DEFAULT_SETTINGS["notification_priority"]

        # Validate booleans
        for bool_field in ["periodic_checkin_enabled", "exclude_weekends"]:
            if bool_field in validated:
                if not isinstance(validated[bool_field], bool):
                    logger.warning(f"Invalid boolean for {bool_field}: {validated[bool_field]}")
                    validated[bool_field] = self.DEFAULT_SETTINGS[bool_field]

        return validated

    def format_settings_message(self, settings: Dict[str, Any]) -> str:
        """
        Format settings as readable message

        Args:
            settings: Settings dictionary

        Returns:
            Formatted message string
        """
        message = "**⚙️ Your Settings**\n\n"

        message += f"**🌍 Timezone:** {settings['timezone']}\n\n"

        message += "**⏰ Check-in Times:**\n"
        message += f"• Morning: {settings['morning_checkin_time']}\n"
        message += f"• Evening: {settings['evening_checkin_time']}\n"
        message += f"• Periodic: {'Enabled' if settings['periodic_checkin_enabled'] else 'Disabled'}\n"
        if settings['periodic_checkin_enabled']:
            message += f"  Every {settings['periodic_checkin_interval_hours']} hours "
            message += f"({settings['periodic_checkin_start_hour']}:00 - {settings['periodic_checkin_end_hour']}:00)\n"

        message += f"\n**🔔 Notifications:**\n"
        message += f"• Priority: {settings['notification_priority']}\n"
        message += f"• Tags: {', '.join(settings['notification_tags'])}\n"

        message += f"\n**📅 Work Schedule:**\n"
        message += f"• Hours: {settings['work_hours_start']}:00 - {settings['work_hours_end']}:00\n"
        message += f"• Exclude weekends: {'Yes' if settings['exclude_weekends'] else 'No'}\n"

        message += "\n💡 Use /settings <key> <value> to update"

        return message
