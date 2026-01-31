from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import time, datetime
from typing import Optional, Callable
import logging
import pytz

logger = logging.getLogger(__name__)


class Scheduler:
    """Manage scheduled tasks for the productivity bot"""

    def __init__(
        self,
        bot,
        telegram_chat_id: int,
        timezone: str = "America/New_York"
    ):
        """
        Initialize scheduler

        Args:
            bot: Bot instance (or any object with send_message method)
            telegram_chat_id: Telegram chat ID for notifications
            timezone: Timezone for scheduling (default: America/New_York)
        """
        self.bot = bot
        self.telegram_chat_id = telegram_chat_id
        self.timezone = timezone
        self._tz = pytz.timezone(timezone)
        self._scheduler: Optional[AsyncIOScheduler] = None

    def start(self):
        """Start the scheduler"""
        if self._scheduler and self._scheduler.running:
            logger.warning("Scheduler already running")
            return

        self._scheduler = AsyncIOScheduler(timezone=self._tz)
        self._scheduler.start()
        logger.info(f"Scheduler started with timezone {self.timezone}")

    def shutdown(self, wait: bool = True):
        """
        Shutdown the scheduler

        Args:
            wait: Wait for running jobs to complete
        """
        if self._scheduler:
            self._scheduler.shutdown(wait=wait)
            logger.info("Scheduler shut down")

    def add_morning_checkin(
        self,
        checkin_time: time,
        callback: Optional[Callable] = None
    ):
        """
        Add morning check-in job

        Args:
            checkin_time: Time for morning check-in (e.g., time(4, 30))
            callback: Optional callback function (defaults to internal handler)

        Returns:
            APScheduler job instance
        """
        if not self._scheduler:
            raise RuntimeError("Scheduler not started. Call start() first.")

        handler = callback or self._morning_checkin_handler

        trigger = CronTrigger(
            hour=checkin_time.hour,
            minute=checkin_time.minute,
            timezone=self._tz
        )

        job = self._scheduler.add_job(
            handler,
            trigger=trigger,
            id="morning_checkin",
            name="Morning Check-in",
            replace_existing=True
        )

        logger.info(f"Added morning check-in at {checkin_time}")
        return job

    def add_periodic_checkin(
        self,
        interval_hours: int = 2,
        start_hour: int = 9,
        end_hour: int = 17,
        callback: Optional[Callable] = None
    ):
        """
        Add periodic check-in job during work hours

        Args:
            interval_hours: Hours between check-ins (default: 2)
            start_hour: Work day start hour (default: 9am)
            end_hour: Work day end hour (default: 5pm)
            callback: Optional callback function

        Returns:
            APScheduler job instance
        """
        if not self._scheduler:
            raise RuntimeError("Scheduler not started. Call start() first.")

        handler = callback or self._periodic_checkin_handler

        # Create interval trigger
        # Note: This will run every N hours, but we filter by work hours in the handler
        trigger = IntervalTrigger(
            hours=interval_hours,
            timezone=self._tz
        )

        job = self._scheduler.add_job(
            handler,
            trigger=trigger,
            id="periodic_checkin",
            name="Periodic Check-in",
            replace_existing=True,
            kwargs={
                'start_hour': start_hour,
                'end_hour': end_hour
            }
        )

        logger.info(f"Added periodic check-in every {interval_hours} hours")
        return job

    def add_evening_review(
        self,
        review_time: time,
        callback: Optional[Callable] = None
    ):
        """
        Add evening review job

        Args:
            review_time: Time for evening review (e.g., time(22, 0))
            callback: Optional callback function

        Returns:
            APScheduler job instance
        """
        if not self._scheduler:
            raise RuntimeError("Scheduler not started. Call start() first.")

        handler = callback or self._evening_review_handler

        trigger = CronTrigger(
            hour=review_time.hour,
            minute=review_time.minute,
            timezone=self._tz
        )

        job = self._scheduler.add_job(
            handler,
            trigger=trigger,
            id="evening_review",
            name="Evening Review",
            replace_existing=True
        )

        logger.info(f"Added evening review at {review_time}")
        return job

    def add_custom_job(
        self,
        job_id: str,
        callback: Callable,
        trigger,
        name: Optional[str] = None,
        **kwargs
    ):
        """
        Add a custom scheduled job

        Args:
            job_id: Unique job identifier
            callback: Function to call
            trigger: APScheduler trigger (CronTrigger, IntervalTrigger, etc.)
            name: Optional job name
            **kwargs: Additional arguments passed to callback

        Returns:
            APScheduler job instance
        """
        if not self._scheduler:
            raise RuntimeError("Scheduler not started. Call start() first.")

        job = self._scheduler.add_job(
            callback,
            trigger=trigger,
            id=job_id,
            name=name or job_id,
            replace_existing=True,
            kwargs=kwargs
        )

        logger.info(f"Added custom job: {job_id}")
        return job

    def remove_job(self, job_id: str):
        """Remove a job by ID"""
        if self._scheduler:
            self._scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")

    def get_jobs(self):
        """Get list of all scheduled jobs"""
        if self._scheduler:
            return self._scheduler.get_jobs()
        return []

    async def _morning_checkin_handler(self):
        """Default handler for morning check-in"""
        logger.info("Triggering morning check-in")

        message = """🌅 Good morning! Time for your daily check-in.

Let's start the day right:
1️⃣ How are you feeling? (1-10)
2️⃣ What are your top 3 priorities today?
3️⃣ Any habits you want to track?

Reply to this message to log your check-in."""

        try:
            await self.bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message
            )
            logger.info("Morning check-in sent")
        except Exception as e:
            logger.error(f"Error sending morning check-in: {e}", exc_info=True)

    async def _periodic_checkin_handler(self, start_hour: int = 9, end_hour: int = 17):
        """Default handler for periodic check-ins"""
        # Check if within work hours
        now = datetime.now(self._tz)
        current_hour = now.hour

        if current_hour < start_hour or current_hour >= end_hour:
            logger.debug(f"Skipping periodic check-in (outside work hours)")
            return

        # Skip weekends
        if now.weekday() >= 5:  # Saturday=5, Sunday=6
            logger.debug("Skipping periodic check-in (weekend)")
            return

        logger.info("Triggering periodic check-in")

        message = """⏰ Quick check-in!

What are you working on right now?

This helps track your actual work vs. planned tasks."""

        try:
            await self.bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message
            )
            logger.info("Periodic check-in sent")
        except Exception as e:
            logger.error(f"Error sending periodic check-in: {e}", exc_info=True)

    async def _evening_review_handler(self):
        """Default handler for evening review"""
        logger.info("Triggering evening review")

        message = """🌙 Time for your evening review!

Let's reflect on today:
1️⃣ What did you accomplish?
2️⃣ What's still pending?
3️⃣ Energy level now? (1-10)
4️⃣ One thing you learned today?

Reply to wrap up your day."""

        try:
            await self.bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message
            )
            logger.info("Evening review sent")
        except Exception as e:
            logger.error(f"Error sending evening review: {e}", exc_info=True)
