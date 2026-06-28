import json
import time
from unittest.mock import MagicMock, patch
from src.sync import SettingsSyncer


@patch("src.sync.get_secret", return_value="")
@patch("src.history.HistoryManager.set_users_synced_at")
@patch("src.sync.build")
@patch("src.history.HistoryManager.set_user_settings")
def test_sync_success(
    mock_set_settings, mock_sheets_build, mock_set_synced_at, mock_get_secret
):
    # Mock Sheets API response
    mock_service = MagicMock()
    mock_sheets_build.return_value = mock_service
    mock_values = [
        [
            "U1",
            "C1",
            "S1",
            "09:00",
            "13:00",
            "14:00",
            "18:00",
            "09:00",
            "18:00",
            "Asia/Tokyo",
        ],
        ["U2", "C1", "S2"],  # Minimal row
    ]
    mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
        "values": mock_values
    }

    syncer = SettingsSyncer(spreadsheet_id="test-id", project_id="test-project")
    syncer.sync()

    assert mock_set_settings.call_count == 2
    # Check first call args
    args, _ = mock_set_settings.call_args_list[0]
    assert args[0] == "U1"
    assert args[1]["jobcan_staff_code"] == "S1"
    # A successful sync stamps the cache freshness marker.
    mock_set_synced_at.assert_called_once()


@patch("src.sync.get_secret", return_value="")
@patch("src.history.HistoryManager.set_users_synced_at")
@patch("src.sync.build")
def test_sync_no_data(mock_sheets_build, mock_set_synced_at, mock_get_secret):
    mock_service = MagicMock()
    mock_sheets_build.return_value = mock_service
    mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {}

    syncer = SettingsSyncer(spreadsheet_id="test-id", project_id="test-project")
    syncer.sync()
    # Should not raise exception, and should still mark the sync attempt.
    mock_set_synced_at.assert_called_once()


@patch("src.history.HistoryManager.get_users_synced_at")
@patch("src.sync.build")
def test_sync_if_stale_skips_when_fresh(mock_sheets_build, mock_get_synced_at):
    # Cache was synced just now -> within TTL -> no Sheets read.
    mock_get_synced_at.return_value = time.time()

    syncer = SettingsSyncer(spreadsheet_id="test-id", project_id="test-project")
    performed = syncer.sync_if_stale(ttl_seconds=3600)

    assert performed is False
    mock_sheets_build.assert_not_called()


@patch("src.sync.get_secret", return_value="")
@patch("src.history.HistoryManager.set_users_synced_at")
@patch("src.history.HistoryManager.set_user_settings")
@patch("src.history.HistoryManager.get_users_synced_at")
@patch("src.sync.build")
def test_sync_if_stale_syncs_when_stale(
    mock_sheets_build,
    mock_get_synced_at,
    mock_set_settings,
    mock_set_synced_at,
    mock_get_secret,
):
    # Last sync was long ago -> stale -> perform a Sheets read.
    mock_get_synced_at.return_value = time.time() - 99999

    mock_service = MagicMock()
    mock_sheets_build.return_value = mock_service
    mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
        "values": [["U1", "C1", "S1"]]
    }

    syncer = SettingsSyncer(spreadsheet_id="test-id", project_id="test-project")
    performed = syncer.sync_if_stale(ttl_seconds=3600)

    assert performed is True
    mock_set_settings.assert_called_once()


@patch("src.sync.get_secret", return_value="")
@patch("src.history.HistoryManager.set_users_synced_at")
@patch("src.history.HistoryManager.set_user_settings")
@patch("src.history.HistoryManager.get_users_synced_at")
@patch("src.sync.build")
def test_sync_if_stale_syncs_when_never_synced(
    mock_sheets_build,
    mock_get_synced_at,
    mock_set_settings,
    mock_set_synced_at,
    mock_get_secret,
):
    # No prior sync timestamp -> must perform a sync.
    mock_get_synced_at.return_value = None

    mock_service = MagicMock()
    mock_sheets_build.return_value = mock_service
    mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
        "values": [["U1", "C1", "S1"]]
    }

    syncer = SettingsSyncer(spreadsheet_id="test-id", project_id="test-project")
    performed = syncer.sync_if_stale(ttl_seconds=3600)

    assert performed is True
    mock_sheets_build.assert_called_once()


@patch("src.sync.Credentials")
@patch("src.sync.get_secret")
def test_build_credentials_from_oauth_secret(mock_get_secret, mock_credentials):
    # A well-formed OAuth secret yields user credentials passed to the API.
    mock_get_secret.return_value = json.dumps(
        {
            "client_id": "cid",
            "client_secret": "csecret",
            "refresh_token": "rtoken",
        }
    )

    syncer = SettingsSyncer(spreadsheet_id="test-id", project_id="test-project")
    creds = syncer._build_credentials()

    assert creds is mock_credentials.return_value
    _, kwargs = mock_credentials.call_args
    assert kwargs["refresh_token"] == "rtoken"
    assert kwargs["client_id"] == "cid"
    assert kwargs["client_secret"] == "csecret"


@patch("src.sync.get_secret", return_value="")
def test_build_credentials_missing_secret_falls_back(mock_get_secret):
    # Absent secret -> None -> Sheets client falls back to ADC.
    syncer = SettingsSyncer(spreadsheet_id="test-id", project_id="test-project")
    assert syncer._build_credentials() is None


@patch("src.sync.get_secret", return_value="not-json")
def test_build_credentials_invalid_secret_falls_back(mock_get_secret):
    syncer = SettingsSyncer(spreadsheet_id="test-id", project_id="test-project")
    assert syncer._build_credentials() is None
