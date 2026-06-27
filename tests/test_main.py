import pytest
from unittest.mock import MagicMock, patch, AsyncMock, ANY
from src.main import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@patch("src.main.get_jobcan_password")
@patch("src.main.MessageParser")
@patch("src.main.HistoryManager")
@patch("src.main.JobcanManager")
@patch("src.main.SlackManager")
def test_worker_endpoint(mock_slack, mock_jobcan, mock_history, mock_parser, mock_pass, client):
    # Setup mocks
    mock_parser_inst = mock_parser.return_value
    mock_parser_inst.parse.return_value = MagicMock(target_date="2026-06-28", attendance_type="full_day", reason="Rest")
    
    mock_history_inst = mock_history.return_value
    mock_history_inst.get_task_status.return_value = None
    mock_history_inst.get_user_settings.return_value = {
        "jobcan_company_id": "C1", "jobcan_staff_code": "S1"
    }
    
    mock_jobcan_inst = mock_jobcan.return_value
    mock_jobcan_inst.apply_holiday = AsyncMock(return_value=True)
    
    mock_pass.return_value = "password"
    
    payload = {
        "client_msg_id": "msg1",
        "user_id": "U1",
        "text": "Taking off",
        "channel_id": "C1",
        "ts": "123.456"
    }
    
    response = client.post("/worker", json=payload)
    assert response.status_code == 200
    assert response.get_json()["status"] == "success"
    mock_history_inst.update_task_status.assert_any_call("msg1", "processing")
    mock_history_inst.update_task_status.assert_any_call("msg1", "success", ANY)
