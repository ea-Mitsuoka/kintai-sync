import pytest
from unittest.mock import MagicMock, patch, AsyncMock, ANY
from src.main import app
from src.models import AttendanceInfo
from datetime import date

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@patch("src.main.get_slack_user_token")
@patch("src.main.CalendarManager")
@patch("src.main.get_jobcan_password")
@patch("src.main.MessageParser")
@patch("src.main.HistoryManager")
@patch("src.main.JobcanManager")
@patch("src.main.SlackManager")
def test_worker_endpoint(mock_slack, mock_jobcan, mock_history, mock_parser, mock_pass, mock_calendar, mock_token, client):
    # Setup mocks
    mock_parser_inst = mock_parser.return_value
    mock_parser_inst.parse.return_value = AttendanceInfo(
        target_date=date(2026, 6, 28), 
        attendance_type="full_day", 
        reason="Rest",
        original_message="Taking off"
    )
    
    mock_history_inst = mock_history.return_value
    mock_history_inst.get_task_status.return_value = None
    mock_history_inst.get_user_settings.return_value = {
        "jobcan_company_id": "C1", 
        "jobcan_staff_code": "S1", 
        "dept_channel_id": "D1",
        "working_hours_start": "09:00",
        "working_hours_end": "18:00",
        "morning_off_start": "09:00",
        "morning_off_end": "13:00",
        "afternoon_off_start": "14:00",
        "afternoon_off_end": "18:00",
        "timezone": "Asia/Tokyo"
    }
    
    mock_jobcan_inst = mock_jobcan.return_value
    mock_jobcan_inst.apply_holiday = AsyncMock(return_value=True)
    
    mock_slack_inst = mock_slack.return_value
    mock_slack_inst.get_user_info.return_value = {"profile": {"email": "test@example.com"}}
    mock_slack_inst.post_attendance_report.return_value = "ts1"
    
    mock_calendar_inst = mock_calendar.return_value
    mock_calendar_inst.register_event.return_value = "event1"
    
    mock_pass.return_value = "password"
    mock_token.return_value = "xoxp-token"
    
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
