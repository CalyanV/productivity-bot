"""
Bot personality and messaging helpers

This module provides context-aware, encouraging messages for the bot
"""

import random
from datetime import datetime
from typing import Optional, List


class BotPersonality:
    """Bot personality and messaging"""

    # Encouraging prefixes for task completion
    COMPLETION_MESSAGES = [
        "Awesome! ✨",
        "Great job! 🎉",
        "Nice work! 👏",
        "Well done! ⭐",
        "Fantastic! 🌟",
        "You're crushing it! 💪",
    ]

    # Motivational messages for morning
    MORNING_ENCOURAGEMENT = [
        "Let's make today count! 💫",
        "You've got this! 🚀",
        "Ready to tackle the day? 💪",
        "Today is full of possibilities! ✨",
        "Let's accomplish great things! 🎯",
    ]

    # Evening reflection prompts
    EVENING_REFLECTION = [
        "Time to reflect on your day 🌙",
        "Let's review what you accomplished 📝",
        "How did today go? 🤔",
        "Wrapping up the day 🌅",
    ]

    # Task reminder tone
    REMINDER_TONES = [
        "Friendly reminder:",
        "Just checking in:",
        "Heads up:",
        "Quick reminder:",
    ]

    @staticmethod
    def get_greeting(hour: Optional[int] = None) -> str:
        """
        Get time-appropriate greeting

        Args:
            hour: Hour of day (0-23), defaults to current hour

        Returns:
            Greeting message
        """
        if hour is None:
            hour = datetime.now().hour

        if 5 <= hour < 12:
            greetings = [
                "Good morning! ☀️",
                "Morning! 🌅",
                "Rise and shine! ☀️",
                "Hey there! Good morning! 🌞",
            ]
        elif 12 <= hour < 17:
            greetings = [
                "Good afternoon! 👋",
                "Hey! How's your day going? 🌤️",
                "Afternoon! ☀️",
            ]
        elif 17 <= hour < 22:
            greetings = [
                "Good evening! 🌆",
                "Evening! 👋",
                "Hey there! 🌙",
            ]
        else:
            greetings = [
                "Hey night owl! 🦉",
                "Burning the midnight oil? 🌙",
                "Still up? 💫",
            ]

        return random.choice(greetings)

    @staticmethod
    def get_completion_message() -> str:
        """Get encouraging message for task completion"""
        return random.choice(BotPersonality.COMPLETION_MESSAGES)

    @staticmethod
    def get_morning_encouragement() -> str:
        """Get motivational message for morning"""
        return random.choice(BotPersonality.MORNING_ENCOURAGEMENT)

    @staticmethod
    def get_evening_reflection() -> str:
        """Get reflection prompt for evening"""
        return random.choice(BotPersonality.EVENING_REFLECTION)

    @staticmethod
    def get_reminder_tone() -> str:
        """Get friendly reminder prefix"""
        return random.choice(BotPersonality.REMINDER_TONES)

    @staticmethod
    def format_task_list(tasks: List[dict], max_items: int = 5) -> str:
        """
        Format task list with encouraging context

        Args:
            tasks: List of task dictionaries
            max_items: Maximum number of tasks to show

        Returns:
            Formatted message
        """
        if not tasks:
            return "No tasks yet! Ready to add something? 🎯"

        count = len(tasks)
        shown = min(count, max_items)

        message = f"You have {count} task{'s' if count != 1 else ''}"

        if count > max_items:
            message += f" (showing {shown}):"
        else:
            message += ":"

        message += "\n\n"

        for i, task in enumerate(tasks[:max_items], 1):
            title = task.get("title", "Untitled")
            status = task.get("status", "unknown")
            emoji = {
                "completed": "✅",
                "active": "📋",
                "blocked": "🚧",
                "inbox": "📥",
            }.get(status, "•")

            message += f"{emoji} {title}\n"

        if count > max_items:
            remaining = count - max_items
            message += f"\n...and {remaining} more"

        return message

    @staticmethod
    def format_error(error_msg: str, helpful_tip: Optional[str] = None) -> str:
        """
        Format error message in a friendly way

        Args:
            error_msg: Error message
            helpful_tip: Optional helpful tip for user

        Returns:
            Formatted error message
        """
        message = f"Oops! {error_msg}"

        if helpful_tip:
            message += f"\n\n💡 Tip: {helpful_tip}"

        return message

    @staticmethod
    def get_productivity_tip() -> str:
        """Get random productivity tip"""
        tips = [
            "Break large tasks into smaller, actionable steps 📝",
            "Time-block your day for better focus 📅",
            "Review your tasks each morning ☀️",
            "Celebrate small wins along the way 🎉",
            "Track your energy levels to optimize scheduling 📊",
            "Batch similar tasks together for efficiency ⚡",
            "Set realistic expectations and be kind to yourself 💙",
            "Use your calendar as your single source of truth 📆",
        ]

        return random.choice(tips)

    @staticmethod
    def get_context_aware_message(
        action: str,
        context: dict
    ) -> str:
        """
        Generate context-aware message based on action and context

        Args:
            action: Action being performed (e.g., "task_created", "morning_checkin")
            context: Context dictionary with relevant info

        Returns:
            Context-aware message
        """
        messages = {
            "task_created": [
                f"Got it! I've added '{context.get('title', 'your task')}' 📝",
                f"Added! {context.get('title', 'Task')} is now on your list ✅",
                f"Done! '{context.get('title', 'Your task')}' has been captured 🎯",
            ],
            "task_scheduled": [
                f"Scheduled! I found you a perfect time slot ⏰",
                f"You're all set! Time is blocked on your calendar 📅",
                f"Great! Added to your calendar with a reminder 🔔",
            ],
            "morning_checkin_complete": [
                f"Perfect! {BotPersonality.get_morning_encouragement()}",
                f"Thanks! Have an amazing day ahead! 🌟",
                f"All set! Go make today great! 💫",
            ],
            "evening_review_complete": [
                f"Well done today! Rest up for tomorrow 🌙",
                f"Great work! You accomplished a lot today 👏",
                f"Nice job reflecting! See you tomorrow ✨",
            ],
        }

        action_messages = messages.get(action, [f"{action} completed!"])
        return random.choice(action_messages)
