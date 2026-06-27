import os
from google.cloud import firestore
from googleapiclient.discovery import build
from google.oauth2 import service_account
from src.models import UserSettings
from src.history import HistoryManager
from typing import List

class SettingsSyncer:
    def __init__(self, spreadsheet_id: str, project_id: str = None):
        self.spreadsheet_id = spreadsheet_id
        self.history_manager = HistoryManager(project_id)
        
        # Scopes for Google Sheets API
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets.readonly']
        self.service = self._build_service()

    def _build_service(self):
        """Builds the Google Sheets API service."""
        # In Cloud Run, it uses the default service account automatically
        # For local dev, it looks for GOOGLE_APPLICATION_CREDENTIALS
        return build('sheets', 'v4', cache_discovery=False)

    def sync(self, range_name: str = 'Sheet1!A2:I'):
        """
        Syncs data from Google Sheets to Firestore.
        Expected columns: 
        slack_user_id, jobcan_company_id, jobcan_staff_code, 
        morning_off_start, morning_off_end, afternoon_off_start, afternoon_off_end, 
        working_hours_start, working_hours_end, timezone
        """
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])

        if not values:
            print('No data found in spreadsheet.')
            return

        synced_count = 0
        for row in values:
            try:
                # Ensure we have enough columns
                if len(row) < 3:
                    continue

                settings = UserSettings(
                    slack_user_id=row[0],
                    jobcan_company_id=row[1],
                    jobcan_staff_code=row[2],
                    morning_off_start=row[3] if len(row) > 3 else "09:00",
                    morning_off_end=row[4] if len(row) > 4 else "13:00",
                    afternoon_off_start=row[5] if len(row) > 5 else "14:00",
                    afternoon_off_end=row[6] if len(row) > 6 else "18:00",
                    working_hours_start=row[7] if len(row) > 7 else "09:00",
                    working_hours_end=row[8] if len(row) > 8 else "18:00",
                    timezone=row[9] if len(row) > 9 else "Asia/Tokyo"
                )
                
                self.history_manager.set_user_settings(settings.slack_user_id, settings.dict())
                synced_count += 1
            except Exception as e:
                print(f"Error syncing row {row}: {e}")

        print(f"Successfully synced {synced_count} users to Firestore.")

if __name__ == "__main__":
    # This block is for testing or running via Cloud Scheduler
    S_ID = os.getenv("SETTINGS_SPREADSHEET_ID")
    if S_ID:
        syncer = SettingsSyncer(S_ID)
        syncer.sync()
    else:
        print("Error: SETTINGS_SPREADSHEET_ID not set.")
