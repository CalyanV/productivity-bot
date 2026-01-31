import asyncio
import logging
from src.bot import ProductivityBot
from src.config import (
    TELEGRAM_BOT_TOKEN,
    DATABASE_PATH,
    VAULT_PATH,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REFRESH_TOKEN,
    TIMEZONE
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point"""
    logger.info("Starting Productivity Bot...")

    bot = ProductivityBot(
        token=TELEGRAM_BOT_TOKEN,
        db_path=DATABASE_PATH,
        vault_path=VAULT_PATH,
        calendar_client_id=GOOGLE_CLIENT_ID,
        calendar_client_secret=GOOGLE_CLIENT_SECRET,
        calendar_refresh_token=GOOGLE_REFRESH_TOKEN,
        timezone=TIMEZONE
    )

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await bot.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await bot.stop()
        raise


if __name__ == "__main__":
    asyncio.run(main())
