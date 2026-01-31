import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from src.calendar_integration import CalendarIntegration

@pytest.fixture
def mock_credentials():
    """Mock Google credentials"""
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds.expired = False
    mock_creds.refresh_token = "test_refresh_token"
    return mock_creds

def test_calendar_integration_initialization(mock_credentials):
    """Test calendar integration initializes correctly"""
    calendar = CalendarIntegration(
        client_id="test_client_id",
        client_secret="test_client_secret",
        refresh_token="test_refresh_token"
    )

    assert calendar.client_id == "test_client_id"
    assert calendar.client_secret == "test_client_secret"
    assert calendar.refresh_token == "test_refresh_token"

@pytest.mark.asyncio
async def test_get_credentials(mock_credentials):
    """Test getting/refreshing credentials"""
    with patch('src.calendar_integration.Credentials') as mock_creds_class:
        mock_creds_class.return_value = mock_credentials

        calendar = CalendarIntegration(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token"
        )

        creds = await calendar.get_credentials()
        assert creds is not None
        assert creds.valid is True

@pytest.mark.asyncio
async def test_list_calendars():
    """Test listing user's calendars"""
    with patch('src.calendar_integration.build') as mock_build:
        mock_service = Mock()
        mock_calendar_list = Mock()
        mock_calendar_list.list.return_value.execute.return_value = {
            'items': [
                {'id': 'primary', 'summary': 'Primary Calendar'},
                {'id': 'work@example.com', 'summary': 'Work Calendar'}
            ]
        }
        mock_service.calendarList.return_value = mock_calendar_list
        mock_build.return_value = mock_service

        calendar = CalendarIntegration(
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token"
        )

        calendars = await calendar.list_calendars()
        assert len(calendars) == 2
        assert calendars[0]['id'] == 'primary'
