import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.calendar import CalendarManager

@patch("src.calendar.build")
def test_register_event_success(mock_build):
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.events.return_value.insert.return_value.execute.return_value = {"id": "ev_123", "htmlLink": "http://link"}
    
    manager = CalendarManager(user_email="test@example.com")
    start = datetime(2026, 6, 27, 9, 0)
    end = datetime(2026, 6, 27, 13, 0)
    event_id = manager.register_event("Morning Off", start, end)
    
    assert event_id == "ev_123"
    mock_service.events.return_value.insert.assert_called_once()

@patch("src.calendar.build")
def test_delete_event(mock_build):
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    manager = CalendarManager(user_email="test@example.com")
    manager.delete_event("ev_123")
    
    mock_service.events.return_value.delete.assert_called_with(calendarId='primary', eventId="ev_123")
