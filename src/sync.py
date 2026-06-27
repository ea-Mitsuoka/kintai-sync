import json
import os
import time
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from src.models import UserSettings
from src.history import HistoryManager
from src.secrets import get_secret
from src.config import config

# Scopes for the Google Sheets API (read-only).
SHEETS_SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
OAUTH_TOKEN_URI = "https://oauth2.googleapis.com/token"


class SettingsSyncer:
    """
    Syncs user settings from a Google Spreadsheet into Firestore.

    Used as a *lazy read-through cache* by the Worker: instead of a scheduled
    job or a manual command, the Worker calls ``sync_if_stale()`` right before
    it reads a user's settings. The spreadsheet is only fetched when the cached
    snapshot in Firestore is older than ``sync.cache_ttl_seconds``.

    The spreadsheet is owned by the e-agency Workspace, but its sharing policy
    forbids granting access to the service account (``gserviceaccount.com`` is
    treated as an external domain). So instead of sharing the file with the SA,
    the Worker authenticates as an *authorized user* using an OAuth refresh
    token stored in Secret Manager (``sync.oauth_secret_id``).
    """

    def __init__(self, spreadsheet_id: str, project_id: str = None):
        self.spreadsheet_id = spreadsheet_id
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.history_manager = HistoryManager(project_id)

        self.scopes = SHEETS_SCOPES
        self._service = None

    def _build_credentials(self):
        """Build OAuth user credentials from the refresh token in Secret
        Manager. Returns None if the secret is absent/invalid, in which case
        the Sheets client falls back to Application Default Credentials
        (useful for local development with GOOGLE_APPLICATION_CREDENTIALS)."""
        secret_id = config.get("sync.oauth_secret_id")
        if not secret_id:
            return None

        raw = get_secret(secret_id, self.project_id)
        if not raw:
            return None

        try:
            data = json.loads(raw)
            return Credentials(
                token=None,
                refresh_token=data["refresh_token"],
                client_id=data["client_id"],
                client_secret=data["client_secret"],
                token_uri=OAUTH_TOKEN_URI,
                scopes=self.scopes,
            )
        except (ValueError, KeyError) as e:
            print(f"Invalid OAuth secret '{secret_id}': {e}")
            return None

    @property
    def service(self):
        """Lazily build the Sheets API client (avoids network/credentials work
        when the cache is fresh and no sync is needed)."""
        if self._service is None:
            credentials = self._build_credentials()
            self._service = build(
                'sheets', 'v4', credentials=credentials, cache_discovery=False
            )
        return self._service

    def sync_if_stale(self, ttl_seconds: int = None) -> bool:
        """
        Refresh settings from the spreadsheet only if the cached snapshot is
        older than ``ttl_seconds``. Returns True if a sync was performed.
        """
        if ttl_seconds is None:
            ttl_seconds = config.get("sync.cache_ttl_seconds", 3600)

        last_synced = self.history_manager.get_users_synced_at()
        if last_synced is not None and (time.time() - last_synced) < ttl_seconds:
            return False  # Cache is fresh; skip the Sheets read.

        self.sync()
        return True

    def sync(self, range_name: str = None):
        """
        Syncs data from Google Sheets to Firestore.
        Expected columns:
        slack_user_id, jobcan_company_id, jobcan_staff_code,
        morning_off_start, morning_off_end, afternoon_off_start, afternoon_off_end,
        working_hours_start, working_hours_end, timezone
        """
        if range_name is None:
            range_name = config.get("sync.default_range")

        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])

        if not values:
            print('No data found in spreadsheet.')
            # Still record the sync attempt so we don't re-read every message.
            self.history_manager.set_users_synced_at(time.time())
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
                    morning_off_start=row[3] if len(row) > 3 else config.get("sync.defaults.morning_off_start"),
                    morning_off_end=row[4] if len(row) > 4 else config.get("sync.defaults.morning_off_end"),
                    afternoon_off_start=row[5] if len(row) > 5 else config.get("sync.defaults.afternoon_off_start"),
                    afternoon_off_end=row[6] if len(row) > 6 else config.get("sync.defaults.afternoon_off_end"),
                    working_hours_start=row[7] if len(row) > 7 else config.get("sync.defaults.working_hours_start"),
                    working_hours_end=row[8] if len(row) > 8 else config.get("sync.defaults.working_hours_end"),
                    timezone=row[9] if len(row) > 9 else config.get("sync.defaults.timezone")
                )

                self.history_manager.set_user_settings(settings.slack_user_id, settings.dict())
                synced_count += 1
            except Exception as e:
                print(f"Error syncing row {row}: {e}")

        self.history_manager.set_users_synced_at(time.time())
        print(f"Successfully synced {synced_count} users to Firestore.")
