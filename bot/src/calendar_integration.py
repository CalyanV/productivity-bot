from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import asyncio
import pytz

logger = logging.getLogger(__name__)


class CalendarIntegration:
    """Google Calendar API integration"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        timezone: str = "America/New_York"
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.timezone = timezone
        self._service = None
        self._credentials = None

    async def get_credentials(self) -> Credentials:
        """Get or refresh Google credentials"""
        if self._credentials and self._credentials.valid:
            return self._credentials

        # Create credentials from refresh token
        self._credentials = Credentials(
            None,  # No access token initially
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret
        )

        # Refresh if needed
        if not self._credentials.valid:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._credentials.refresh,
                Request()
            )
            logger.info("Google credentials refreshed")

        return self._credentials

    async def get_service(self):
        """Get Google Calendar service"""
        if self._service:
            return self._service

        credentials = await self.get_credentials()

        loop = asyncio.get_event_loop()
        self._service = await loop.run_in_executor(
            None,
            lambda: build('calendar', 'v3', credentials=credentials)
        )

        logger.info("Google Calendar service initialized")
        return self._service

    async def list_calendars(self) -> List[Dict]:
        """List all calendars for the user"""
        service = await self.get_service()

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: service.calendarList().list().execute()
        )

        calendars = result.get('items', [])
        logger.info(f"Found {len(calendars)} calendars")
        return calendars

    async def get_events(
        self,
        calendar_id: str = 'primary',
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Get events from calendar

        Args:
            calendar_id: Calendar ID (default: 'primary')
            time_min: Start time (default: now)
            time_max: End time (default: 1 week from now)
            max_results: Maximum number of events to return

        Returns:
            List of calendar events
        """
        service = await self.get_service()

        if not time_min:
            time_min = datetime.now(pytz.timezone(self.timezone))
        if not time_max:
            time_max = time_min + timedelta(days=7)

        # Convert to ISO format with timezone
        time_min_str = time_min.isoformat()
        time_max_str = time_max.isoformat()

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: service.events().list(
                calendarId=calendar_id,
                timeMin=time_min_str,
                timeMax=time_max_str,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
        )

        events = result.get('items', [])
        logger.info(f"Retrieved {len(events)} events from {calendar_id}")
        return events

    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        calendar_id: str = 'primary'
    ) -> Dict:
        """
        Create a calendar event

        Args:
            summary: Event title
            start_time: Start time
            end_time: End time
            description: Event description
            location: Event location
            calendar_id: Calendar ID (default: 'primary')

        Returns:
            Created event object
        """
        service = await self.get_service()

        # Ensure times have timezone
        tz = pytz.timezone(self.timezone)
        if start_time.tzinfo is None:
            start_time = tz.localize(start_time)
        if end_time.tzinfo is None:
            end_time = tz.localize(end_time)

        event = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': self.timezone,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': self.timezone,
            }
        }

        if description:
            event['description'] = description

        if location:
            event['location'] = location

        loop = asyncio.get_event_loop()
        created_event = await loop.run_in_executor(
            None,
            lambda: service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
        )

        logger.info(f"Created event: {created_event['id']} - {summary}")
        return created_event

    async def update_event(
        self,
        event_id: str,
        updates: Dict,
        calendar_id: str = 'primary'
    ) -> Dict:
        """
        Update an existing event

        Args:
            event_id: Event ID to update
            updates: Dictionary of fields to update
            calendar_id: Calendar ID (default: 'primary')

        Returns:
            Updated event object
        """
        service = await self.get_service()

        # Get existing event
        loop = asyncio.get_event_loop()
        event = await loop.run_in_executor(
            None,
            lambda: service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
        )

        # Apply updates
        event.update(updates)

        # Update event
        updated_event = await loop.run_in_executor(
            None,
            lambda: service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
        )

        logger.info(f"Updated event: {event_id}")
        return updated_event

    async def delete_event(
        self,
        event_id: str,
        calendar_id: str = 'primary'
    ):
        """
        Delete a calendar event

        Args:
            event_id: Event ID to delete
            calendar_id: Calendar ID (default: 'primary')
        """
        service = await self.get_service()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
        )

        logger.info(f"Deleted event: {event_id}")

    async def get_free_busy(
        self,
        time_min: datetime,
        time_max: datetime,
        calendar_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Query free/busy information for calendars

        Args:
            time_min: Start time
            time_max: End time
            calendar_ids: List of calendar IDs (default: ['primary'])

        Returns:
            Free/busy information
        """
        service = await self.get_service()

        if not calendar_ids:
            calendar_ids = ['primary']

        # Ensure times have timezone
        tz = pytz.timezone(self.timezone)
        if time_min.tzinfo is None:
            time_min = tz.localize(time_min)
        if time_max.tzinfo is None:
            time_max = tz.localize(time_max)

        body = {
            "timeMin": time_min.isoformat(),
            "timeMax": time_max.isoformat(),
            "timeZone": self.timezone,
            "items": [{"id": cal_id} for cal_id in calendar_ids]
        }

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: service.freebusy().query(body=body).execute()
        )

        logger.info(f"Retrieved free/busy for {len(calendar_ids)} calendars")
        return result

    async def find_free_slots(
        self,
        duration_minutes: int,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        calendar_ids: Optional[List[str]] = None,
        work_hours_start: int = 9,
        work_hours_end: int = 17,
        max_slots: int = 10
    ) -> List[Dict]:
        """
        Find available time slots for a task

        Args:
            duration_minutes: Required duration in minutes
            time_min: Search start time (default: now)
            time_max: Search end time (default: 7 days from now)
            calendar_ids: Calendar IDs to check (default: ['primary'])
            work_hours_start: Work day start hour (default: 9am)
            work_hours_end: Work day end hour (default: 5pm)
            max_slots: Maximum number of slots to return

        Returns:
            List of available time slots with start/end times
        """
        tz = pytz.timezone(self.timezone)

        if not time_min:
            time_min = datetime.now(tz)
        if not time_max:
            time_max = time_min + timedelta(days=7)

        # Ensure timezone
        if time_min.tzinfo is None:
            time_min = tz.localize(time_min)
        if time_max.tzinfo is None:
            time_max = tz.localize(time_max)

        # Get free/busy information
        free_busy = await self.get_free_busy(time_min, time_max, calendar_ids)

        # Extract busy periods
        busy_periods = []
        for calendar_id in (calendar_ids or ['primary']):
            calendar_busy = free_busy.get('calendars', {}).get(calendar_id, {})
            for busy in calendar_busy.get('busy', []):
                start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                busy_periods.append((start.astimezone(tz), end.astimezone(tz)))

        # Sort busy periods by start time
        busy_periods.sort()

        # Find free slots
        free_slots = []
        current_time = time_min

        while current_time < time_max and len(free_slots) < max_slots:
            # Skip to next work day if outside work hours
            if current_time.hour < work_hours_start:
                current_time = current_time.replace(
                    hour=work_hours_start, minute=0, second=0, microsecond=0
                )
            elif current_time.hour >= work_hours_end:
                # Move to next day
                current_time = (current_time + timedelta(days=1)).replace(
                    hour=work_hours_start, minute=0, second=0, microsecond=0
                )
                continue

            # Skip weekends
            if current_time.weekday() >= 5:  # Saturday=5, Sunday=6
                current_time = current_time + timedelta(days=(7 - current_time.weekday()))
                current_time = current_time.replace(
                    hour=work_hours_start, minute=0, second=0, microsecond=0
                )
                continue

            # Check if this slot is free
            slot_end = current_time + timedelta(minutes=duration_minutes)

            # Ensure slot doesn't extend past work hours
            if slot_end.hour > work_hours_end or (slot_end.hour == work_hours_end and slot_end.minute > 0):
                current_time = (current_time + timedelta(days=1)).replace(
                    hour=work_hours_start, minute=0, second=0, microsecond=0
                )
                continue

            # Check for conflicts with busy periods
            is_free = True
            for busy_start, busy_end in busy_periods:
                # Check if slot overlaps with busy period
                if (current_time < busy_end and slot_end > busy_start):
                    is_free = False
                    # Jump to end of busy period
                    current_time = busy_end
                    break

            if is_free:
                free_slots.append({
                    'start': current_time,
                    'end': slot_end,
                    'start_iso': current_time.isoformat(),
                    'end_iso': slot_end.isoformat(),
                    'duration_minutes': duration_minutes
                })
                # Move to next potential slot (15 minute increments)
                current_time = current_time + timedelta(minutes=15)
            else:
                # Already moved to end of busy period
                pass

        logger.info(f"Found {len(free_slots)} free slots for {duration_minutes}min task")
        return free_slots
