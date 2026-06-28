import pytest
from unittest.mock import patch
from src.calendar import CalendarManager
from datetime import datetime


@pytest.fixture
def calendar_manager():
    # Patch build globally during fixture to prevent real API calls
    with patch("src.calendar.build") as mock_build:
        manager = CalendarManager(user_email="test@example.com")
        manager.mock_service = mock_build.return_value
        yield manager


def test_register_event_success(calendar_manager):
    mock_events = calendar_manager.mock_service.events.return_value
    mock_insert = mock_events.insert.return_value
    mock_insert.execute.return_value = {"id": "event123", "htmlLink": "http://link"}

    start = datetime(2026, 6, 28, 9, 0)
    end = datetime(2026, 6, 28, 18, 0)

    event_id = calendar_manager.register_event("Test Event", start, end)

    assert event_id == "event123"
    mock_events.insert.assert_called_once()


def test_register_event_failure(calendar_manager):
    mock_events = calendar_manager.mock_service.events.return_value
    mock_insert = mock_events.insert.return_value
    mock_insert.execute.side_effect = Exception("API Error")

    start = datetime(2026, 6, 28, 9, 0)
    end = datetime(2026, 6, 28, 18, 0)

    event_id = calendar_manager.register_event("Test Event", start, end)

    assert event_id is None


def test_delete_event_success(calendar_manager):
    mock_events = calendar_manager.mock_service.events.return_value
    mock_delete = mock_events.delete.return_value
    mock_delete.execute.return_value = {}

    calendar_manager.delete_event("event123")

    mock_events.delete.assert_called_once_with(calendarId="primary", eventId="event123")


def test_delete_event_failure(calendar_manager):
    mock_events = calendar_manager.mock_service.events.return_value
    mock_delete = mock_events.delete.return_value
    mock_delete.execute.side_effect = Exception("API Error")

    # Should handle exception and not crash
    calendar_manager.delete_event("event123")
