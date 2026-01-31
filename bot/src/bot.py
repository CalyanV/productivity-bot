from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import logging
from .database import Database
from .obsidian_sync import ObsidianSync

logger = logging.getLogger(__name__)


class ProductivityBot:
    """Main Telegram bot for productivity system"""

    def __init__(self, token: str, db_path: str, vault_path: str):
        self.token = token
        self.db_path = db_path
        self.vault_path = vault_path

        self.db = Database(db_path)
        self.vault_sync = ObsidianSync(vault_path)

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

**Daily Workflow:**
/morning - Morning check-in
/evening - Evening review

**More commands coming soon!**"""

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
