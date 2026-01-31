"""
Main entry point for the productivity bot

This module initializes and runs the bot with all components
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from .bot import ProductivityBot
from .scheduler import Scheduler
from .checkins import CheckinManager
from .git_sync import GitSync

# Load environment variables
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/app/data/bot.log') if os.path.exists('/app/data') else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


def validate_environment():
    """Validate required environment variables"""
    required = ["TELEGRAM_BOT_TOKEN", "OPENROUTER_API_KEY"]
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    logger.info("Environment validation passed")


def setup_directories():
    """Create necessary directories if they don't exist"""
    data_dir = Path(os.getenv("DATABASE_PATH", "./data/bot.db")).parent
    vault_dir = Path(os.getenv("VAULT_PATH", "./obsidian-vault"))

    data_dir.mkdir(parents=True, exist_ok=True)
    vault_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Vault directory: {vault_dir}")


async def setup_git_sync(vault_path: str, db_path: str):
    """Setup git synchronization if enabled"""
    if os.getenv("GIT_SYNC_ENABLED", "false").lower() != "true":
        logger.info("Git sync disabled")
        return None

    remote_url = os.getenv("GIT_REMOTE_URL")
    if not remote_url:
        logger.warning("Git sync enabled but GIT_REMOTE_URL not set")
        return None

    git_sync = GitSync(
        vault_path=vault_path,
        db_path=db_path,
        remote_name="origin",
        branch_name=os.getenv("GIT_BRANCH", "master")
    )

    await git_sync.initialize()

    # Initial sync
    logger.info("Performing initial git sync...")
    result = await git_sync.sync()

    if result.get("errors"):
        logger.warning(f"Git sync completed with errors: {result['errors']}")
    else:
        logger.info("Git sync completed successfully")

    return git_sync


async def setup_scheduler(bot, chat_id: int, timezone: str):
    """Setup scheduled check-ins"""
    from datetime import time

    scheduler = Scheduler(
        bot=bot.app.bot,
        telegram_chat_id=chat_id,
        timezone=timezone
    )

    # Morning check-in at 4:30 AM
    morning_time = time(4, 30)
    scheduler.add_morning_checkin(morning_time)
    logger.info(f"Scheduled morning check-in at {morning_time}")

    # Periodic check-ins every 2 hours during work hours
    scheduler.add_periodic_checkin(
        interval_hours=2,
        start_hour=9,
        end_hour=17
    )
    logger.info("Scheduled periodic check-ins (9 AM - 5 PM)")

    # Evening review at 8:00 PM
    evening_time = time(20, 0)
    scheduler.add_evening_review(evening_time)
    logger.info(f"Scheduled evening review at {evening_time}")

    # Start scheduler
    scheduler.start()

    return scheduler


async def main():
    """Main application entry point"""
    try:
        logger.info("=" * 60)
        logger.info("Starting Productivity Bot")
        logger.info("=" * 60)

        # Validate environment
        validate_environment()

        # Setup directories
        setup_directories()

        # Get configuration
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        db_path = os.getenv("DATABASE_PATH", "./data/bot.db")
        vault_path = os.getenv("VAULT_PATH", "./obsidian-vault")
        timezone = os.getenv("TZ", "America/New_York")

        # Optional: Calendar integration
        calendar_client_id = os.getenv("GOOGLE_CLIENT_ID")
        calendar_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        calendar_refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")

        # Initialize bot
        logger.info("Initializing bot...")
        bot = ProductivityBot(
            token=telegram_token,
            db_path=db_path,
            vault_path=vault_path,
            calendar_client_id=calendar_client_id,
            calendar_client_secret=calendar_client_secret,
            calendar_refresh_token=calendar_refresh_token,
            timezone=timezone
        )

        # Setup git sync if enabled
        git_sync = await setup_git_sync(vault_path, db_path)

        # Setup scheduler if chat ID is provided
        admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
        if admin_chat_id:
            try:
                scheduler = await setup_scheduler(
                    bot,
                    int(admin_chat_id),
                    timezone
                )
            except ValueError:
                logger.warning(f"Invalid TELEGRAM_ADMIN_CHAT_ID: {admin_chat_id}")
                scheduler = None
        else:
            logger.info("TELEGRAM_ADMIN_CHAT_ID not set, scheduler disabled")
            scheduler = None

        # Start bot
        logger.info("Starting bot polling...")
        logger.info("Bot is ready! Press Ctrl+C to stop.")

        # Run bot
        await bot.start()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Shutting down bot...")
        if 'scheduler' in locals() and scheduler:
            scheduler.stop()
        if 'bot' in locals():
            await bot.stop()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
