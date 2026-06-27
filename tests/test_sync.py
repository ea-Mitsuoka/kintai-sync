import pytest
from unittest.mock import MagicMock, patch
from src.sync import SettingsSyncer

@patch("src.sync.build")
@patch("src.history.HistoryManager.set_user_settings")
def test_sync_success(mock_set_settings, mock_sheets_build):
    # Mock Sheets API response
    mock_service = MagicMock()
    mock_sheets_build.return_value = mock_service
    mock_values = [
        ["U1", "C1", "S1", "09:00", "13:00", "14:00", "18:00", "09:00", "18:00", "Asia/Tokyo"],
        ["U2", "C1", "S2"] # Minimal row
    ]
    mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {"values": mock_values}

    syncer = SettingsSyncer(spreadsheet_id="test-id", project_id="test-project")
    syncer.sync()

    assert mock_set_settings.call_count == 2
    # Check first call args
    args, _ = mock_set_settings.call_args_list[0]
    assert args[0] == "U1"
    assert args[1]["jobcan_staff_code"] == "S1"

@patch("src.sync.build")
def test_sync_no_data(mock_sheets_build):
    mock_service = MagicMock()
    mock_sheets_build.return_value = mock_service
    mock_service.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {}

    syncer = SettingsSyncer(spreadsheet_id="test-id")
    syncer.sync()
    # Should not raise exception
