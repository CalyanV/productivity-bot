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
