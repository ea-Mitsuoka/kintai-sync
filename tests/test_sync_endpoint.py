import pytest
from unittest.mock import MagicMock, patch
from src.sync import app
import os

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@patch("src.sync.SettingsSyncer")
def test_sync_endpoint(mock_syncer_class, client):
    mock_inst = mock_syncer_class.return_value
    
    with patch.dict(os.environ, {"SETTINGS_SPREADSHEET_ID": "test-id"}):
        response = client.post("/sync")
        assert response.status_code == 200
        assert response.get_json()["status"] == "success"
        mock_inst.sync.assert_called_once()
