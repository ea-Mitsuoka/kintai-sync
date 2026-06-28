from src.models import UserSettings, AttendanceInfo, TaskExecutionState, SubTaskStatus
from datetime import date

def test_user_settings_defaults():
    settings = UserSettings(
        slack_user_id="U123",
        jobcan_company_id="C456",
        jobcan_staff_code="S789"
    )
    assert settings.morning_off_start == "09:00"
    assert settings.timezone == "Asia/Tokyo"
    assert settings.dept_channel_id is None

def test_attendance_info_validation():
    info = AttendanceInfo(
        target_dates=[date(2026, 6, 28)],
        attendance_type="morning_off",
        reason="Doctor",
        original_message="Taking tomorrow morning off"
    )
    assert info.target_dates[0].isoformat() == "2026-06-28"
    assert info.attendance_type == "morning_off"

def test_task_execution_state_initial():
    state = TaskExecutionState(client_msg_id="msg123")
    assert state.overall_status == "pending"
    assert len(state.subtasks) == 0
