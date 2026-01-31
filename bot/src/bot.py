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
from .people import PeopleManager
from .personality import BotPersonality
from .settings import UserSettings

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
        self.people_manager = PeopleManager(db_path, vault_path)
        self.user_settings = UserSettings(db_path)

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

        # People/CRM commands
        self.app.add_handler(CommandHandler("people", self.cmd_people))
        self.app.add_handler(CommandHandler("person", self.cmd_person))
        self.app.add_handler(CommandHandler("contact", self.cmd_contact))

        # Settings command
        self.app.add_handler(CommandHandler("settings", self.cmd_settings))

        # Messages (for conversation flow)
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        greeting = BotPersonality.get_greeting()

        message = f"""{greeting} Welcome {user.first_name}!

I'm your productivity assistant. I'll help you:
• Capture tasks quickly with natural language
• Schedule time blocks on your calendar
• Track important relationships
• Stay on top of your goals with daily check-ins

Get started:
/add - Add a new task
/tasks - View your tasks
/help - See all commands

{BotPersonality.get_productivity_tip()}"""

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

**People & CRM:**
/people - List all people in your network
/person <name> - Add or view a person
/contact <id> - Update last contact date

**Daily Workflow:**
/morning - Morning check-in
/evening - Evening review

**Preferences:**
/settings - View and update your preferences"""

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
        message = BotPersonality.get_context_aware_message(
            "task_created",
            {"title": task_text}
        )
        await update.message.reply_text(
            f"{message}\n\n(Task parsing coming in Phase 2!)"
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

            message += f"\n\n{BotPersonality.get_context_aware_message('task_scheduled', {})}"

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

    async def cmd_people(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /people command - List all people"""
        try:
            await self.people_manager.initialize()
            people = await self.people_manager.list_people(limit=20)

            if not people:
                await update.message.reply_text(
                    "📇 No people in your network yet.\n\n"
                    "Add someone with: /person John Doe"
                )
                return

            message = "📇 **Your Network:**\n\n"

            for person in people:
                name = person["name"]
                company = person.get("company", "")
                role = person.get("role", "")

                info_parts = []
                if role:
                    info_parts.append(role)
                if company:
                    info_parts.append(f"@ {company}")

                info = " - " + ", ".join(info_parts) if info_parts else ""

                message += f"• {name}{info}\n"

            message += f"\n💡 Use /person <name> to view details"

            await update.message.reply_text(message, parse_mode="Markdown")
            logger.info(f"Listed {len(people)} people for user {update.effective_user.id}")

        except Exception as e:
            logger.error(f"Error listing people: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error listing people: {str(e)}")

    async def cmd_person(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /person command - Add or view a person"""
        if not context.args:
            await update.message.reply_text(
                "Usage:\n"
                "/person John Doe - Add new person\n"
                "/person person-abc123 - View person details"
            )
            return

        try:
            await self.people_manager.initialize()

            query = " ".join(context.args)

            # Check if it's a person ID
            if query.startswith("person-"):
                person = await self.people_manager.get_person(query)

                if not person:
                    await update.message.reply_text(f"❌ Person not found: {query}")
                    return

                # Display person details
                message = f"**{person['name']}**\n\n"

                if person.get("role"):
                    message += f"**Role**: {person['role']}\n"
                if person.get("company"):
                    message += f"**Company**: {person['company']}\n"
                if person.get("email"):
                    message += f"**Email**: {person['email']}\n"
                if person.get("phone"):
                    message += f"**Phone**: {person['phone']}\n"

                if person.get("last_contact"):
                    last_contact = datetime.fromisoformat(person['last_contact'])
                    message += f"\n**Last Contact**: {last_contact.strftime('%B %d, %Y')}\n"

                message += f"\n**ID**: `{person['id']}`"

                await update.message.reply_text(message, parse_mode="Markdown")

            else:
                # Search for person or create new
                results = await self.people_manager.search_people(query)

                if results:
                    # Show search results
                    message = f"Found {len(results)} match(es):\n\n"

                    for person in results[:5]:
                        name = person["name"]
                        person_id = person["id"]
                        company = person.get("company", "")
                        message += f"• {name}"
                        if company:
                            message += f" @ {company}"
                        message += f"\n  ID: `{person_id}`\n"

                    await update.message.reply_text(message, parse_mode="Markdown")

                else:
                    # Create new person
                    result = await self.people_manager.create_person({"name": query})

                    completion_msg = BotPersonality.get_completion_message()
                    await update.message.reply_text(
                        f"{completion_msg} Added {result['name']} to your network!\n\n"
                        f"ID: `{result['person_id']}`\n\n"
                        f"Update details with /person {result['person_id']}",
                        parse_mode="Markdown"
                    )

                    logger.info(f"Created person: {result['person_id']}")

        except Exception as e:
            logger.error(f"Error handling person command: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def cmd_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /contact command - Update last contact date"""
        if not context.args:
            await update.message.reply_text(
                "Usage: /contact <person_id>\n\n"
                "Updates last contact date to today."
            )
            return

        try:
            await self.people_manager.initialize()

            person_id = context.args[0]
            person = await self.people_manager.get_person(person_id)

            if not person:
                await update.message.reply_text(f"❌ Person not found: {person_id}")
                return

            # Update last contact
            await self.people_manager.update_last_contact(person_id)

            completion_msg = BotPersonality.get_completion_message()
            await update.message.reply_text(
                f"{completion_msg} Updated last contact for {person['name']}\n"
                f"Date: {datetime.now().strftime('%B %d, %Y')}"
            )

            logger.info(f"Updated last contact for {person_id}")

        except Exception as e:
            logger.error(f"Error updating contact: {e}", exc_info=True)
            await update.message.reply_text(f"❌ Error: {str(e)}")

    async def cmd_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command - View and update preferences"""
        try:
            await self.user_settings.initialize()
            user_id = update.effective_user.id

            # No args - show current settings
            if not context.args:
                settings = await self.user_settings.get_settings(user_id)
                message = self.user_settings.format_settings_message(settings)
                await update.message.reply_text(message, parse_mode="Markdown")
                return

            # Check for reset command
            if context.args[0] == "reset":
                settings = await self.user_settings.reset_settings(user_id)
                await update.message.reply_text(
                    "✅ Settings reset to defaults!\n\n" +
                    self.user_settings.format_settings_message(settings),
                    parse_mode="Markdown"
                )
                return

            # Update specific setting: /settings <key> <value>
            if len(context.args) < 2:
                await update.message.reply_text(
                    "Usage:\n"
                    "/settings - View current settings\n"
                    "/settings <key> <value> - Update a setting\n"
                    "/settings reset - Reset to defaults\n\n"
                    "Examples:\n"
                    "/settings timezone America/Los_Angeles\n"
                    "/settings morning_checkin_time 05:00\n"
                    "/settings work_hours_start 8"
                )
                return

            key = context.args[0]
            value_str = " ".join(context.args[1:])

            # Parse value based on key type
            value = self._parse_setting_value(key, value_str)

            if value is None:
                await update.message.reply_text(
                    f"❌ Invalid value for {key}: {value_str}\n\n"
                    "Please check the format and try again."
                )
                return

            # Update setting
            updated_settings = await self.user_settings.update_settings(
                user_id,
                {key: value}
            )

            completion_msg = BotPersonality.get_completion_message()
            await update.message.reply_text(
                f"{completion_msg} Updated {key} to {value}\n\n"
                f"Current settings:\n{self.user_settings.format_settings_message(updated_settings)}",
                parse_mode="Markdown"
            )

            logger.info(f"Updated setting {key}={value} for user {user_id}")

        except Exception as e:
            logger.error(f"Error handling settings: {e}", exc_info=True)
            await update.message.reply_text(
                BotPersonality.format_error(
                    f"Error updating settings: {str(e)}",
                    "Use /settings to see available options"
                )
            )

    def _parse_setting_value(self, key: str, value_str: str):
        """Parse setting value from string"""
        # Boolean fields
        if key in ["periodic_checkin_enabled", "exclude_weekends"]:
            if value_str.lower() in ["true", "yes", "on", "1", "enabled"]:
                return True
            elif value_str.lower() in ["false", "no", "off", "0", "disabled"]:
                return False
            return None

        # Integer fields
        if key in ["periodic_checkin_interval_hours", "periodic_checkin_start_hour",
                   "periodic_checkin_end_hour", "work_hours_start", "work_hours_end"]:
            try:
                return int(value_str)
            except ValueError:
                return None

        # List fields (tags)
        if key == "notification_tags":
            return [tag.strip() for tag in value_str.split(",")]

        # String fields (timezone, times, priority, language)
        return value_str

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
        await self.people_manager.initialize()
        await self.user_settings.initialize()
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
