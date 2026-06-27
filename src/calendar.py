import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime, timedelta
from src.config import config

class CalendarManager:
    def __init__(self, user_email: str):
        self.user_email = user_email
        self.service = self._build_service()

    def _build_service(self):
        """
        Builds the Google Calendar API service.
        Note: In a real GCP environment, this would use Domain-Wide Delegation
        with a Service Account to impersonate the user.
        """
        # Placeholder for building the service with appropriate credentials
        # return build('calendar', 'v3', credentials=creds)
        return build('calendar', 'v3', cache_discovery=False)

    def register_event(self, summary: str, start_time: datetime, end_time: datetime, description: str = ""):
        """
        Registers an event in the user's primary calendar.
        """
        timezone = config.get("calendar.timezone")
        calendar_id = config.get("calendar.calendar_id")
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': timezone,
            },
        }

        try:
            event = self.service.events().insert(calendarId=calendar_id, body=event).execute()
            print(f"Event created: {event.get('htmlLink')}")
            return event.get('id')
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None

    def delete_event(self, event_id: str):
        """
        Deletes an event from the user's primary calendar.
        """
        calendar_id = config.get("calendar.calendar_id")
        try:
            self.service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        except Exception as e:
            print(f"Error deleting calendar event: {e}")
