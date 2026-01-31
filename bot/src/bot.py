from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import logging
from datetime import datetime
from typing import Optional
from .database import Database
from .obsidian_sync import ObsidianSync
from .calendar_integration import CalendarIntegration

logger = logging.getLogger(__name__)


class ProductivityBot:
    """Main Telegram bot for productivity system"""

    def __init__(
        self,
        token: str,
        db_path: str,
        vault_path: str,
        calendar_client_id: Optional[str] = None,
        calendar_client_secret: Optional[str] = None,
        calendar_refresh_token: Optional[str] = None,
        timezone: str = "America/New_York"
    ):
        self.token = token
        self.db_path = db_path
        self.vault_path = vault_path
        self.timezone = timezone

        self.db = Database(db_path)
        self.vault_sync = ObsidianSync(vault_path)

        # Initialize calendar integration if credentials provided
        self.calendar = None
        if calendar_client_id and calendar_client_secret and calendar_refresh_token:
            self.calendar = CalendarIntegration(
                client_id=calendar_client_id,
                client_secret=calendar_client_secret,
                refresh_token=calendar_refresh_token,
                timezone=timezone
            )
            logger.info("Calendar integration enabled")

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

        # Calendar commands (if calendar integration enabled)
        if self.calendar:
            self.app.add_handler(CommandHandler("schedule", self.cmd_schedule))
            self.app.add_handler(CommandHandler("suggest", self.cmd_suggest))
            self.app.add_handler(CommandHandler("calendar", self.cmd_calendar))

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

**Calendar & Scheduling:**"""

        if self.calendar:
            message += """
/schedule <task_id> - Schedule a task on your calendar
/suggest <duration> - Get time slot suggestions
/calendar - View upcoming calendar events"""
        else:
            message += """
(Calendar integration not configured)"""

        message += """

**Daily Workflow:**
/morning - Morning check-in
/evening - Evening review"""

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

    async def cmd_schedule(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /schedule command - Schedule a task on calendar"""
        if not self.calendar:
            await update.message.reply_text(
                "❌ Calendar integration is not configured.\n"
                "Please set up Google Calendar credentials."
            )
            return

        # Get task ID from args
        if not context.args:
            await update.message.reply_text(
                "Usage: /schedule <task_id>\n\n"
                "Example: /schedule task-123"
            )
            return

        task_id = context.args[0]

        try:
            # For now, mock task data (will integrate with database in later phases)
            task_data = {
                "id": task_id,
                "title": "Sample Task",
                "duration_minutes": 60,
                "due_date": None
            }

            await update.message.reply_text(
                "🔍 Finding the best time slot for your task...\n"
                f"Task: {task_data['title']}\n"
                f"Duration: {task_data['duration_minutes']} minutes"
            )

            # Schedule the task
            result = await self.calendar.schedule_task(
                task_data=task_data,
                vault_path=self.vault_path
            )

            # Format response
            start_time = result['start'].strftime('%I:%M %p')
            date = result['start'].strftime('%A, %B %d')

            message = f"""✅ Task scheduled!

📋 {task_data['title']}
📅 {date}
⏰ {start_time}
🔗 [View in Calendar]({result['event_link']})

Other available slots:"""

            for i, slot in enumerate(result.get('suggested_slots', [])[1:3], 1):
                slot_time = slot['start'].strftime('%I:%M %p')
                slot_date = slot['start'].strftime('%a %b %d')
                message += f"\n{i}. {slot_date} at {slot_time}"

            await update.message.reply_text(message, parse_mode="Markdown")
            logger.info(f"Scheduled task {task_id} for user {update.effective_user.id}")

        except Exception as e:
            logger.error(f"Error scheduling task: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ Error scheduling task: {str(e)}\n\n"
                "Please try again or check your calendar settings."
            )

    async def cmd_suggest(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /suggest command - Get time slot suggestions"""
        if not self.calendar:
            await update.message.reply_text(
                "❌ Calendar integration is not configured."
            )
            return

        # Get duration from args
        duration = 60  # default
        if context.args:
            try:
                duration = int(context.args[0])
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid duration. Please provide a number in minutes.\n\n"
                    "Example: /suggest 90"
                )
                return

        try:
            await update.message.reply_text(
                f"🔍 Finding free time slots for {duration} minutes..."
            )

            # Find free slots
            slots = await self.calendar.find_free_slots(
                duration_minutes=duration,
                max_slots=5
            )

            if not slots:
                await update.message.reply_text(
                    "❌ No free slots found in the next 7 days.\n"
                    "Your calendar is quite busy!"
                )
                return

            # Format response
            message = f"📅 Available {duration}-minute slots:\n\n"

            for i, slot in enumerate(slots, 1):
                start_time = slot['start'].strftime('%I:%M %p')
                date = slot['start'].strftime('%A, %B %d')
                message += f"{i}. {date} at {start_time}\n"

            await update.message.reply_text(message)
            logger.info(f"Suggested {len(slots)} slots for user {update.effective_user.id}")

        except Exception as e:
            logger.error(f"Error finding slots: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ Error finding time slots: {str(e)}"
            )

    async def cmd_calendar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /calendar command - View upcoming events"""
        if not self.calendar:
            await update.message.reply_text(
                "❌ Calendar integration is not configured."
            )
            return

        try:
            await update.message.reply_text("📅 Loading your calendar...")

            # Get upcoming events (next 7 days)
            events = await self.calendar.get_events(max_results=10)

            if not events:
                await update.message.reply_text(
                    "📅 No upcoming events in the next 7 days.\n"
                    "Your calendar is clear!"
                )
                return

            # Format response
            message = "📅 **Upcoming Events:**\n\n"

            for event in events:
                summary = event.get('summary', 'No title')
                start = event.get('start', {})

                if 'dateTime' in start:
                    # Timed event
                    start_dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    time_str = start_dt.strftime('%I:%M %p')
                    date_str = start_dt.strftime('%a %b %d')
                    message += f"• {summary}\n  {date_str} at {time_str}\n\n"
                else:
                    # All-day event
                    date_str = start.get('date', 'Unknown')
                    message += f"• {summary}\n  {date_str} (All day)\n\n"

            await update.message.reply_text(message, parse_mode="Markdown")
            logger.info(f"Showed calendar for user {update.effective_user.id}")

        except Exception as e:
            logger.error(f"Error retrieving calendar: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ Error retrieving calendar: {str(e)}"
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
