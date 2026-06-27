import pytest
from datetime import date
from src.models import UserSettings, AttendanceInfo, TaskExecutionState, SubTaskStatus

def test_user_settings_defaults():
    settings = UserSettings(slack_user_id="U12345", jobcan_company_id="C1", jobcan_staff_code="S1")
    assert settings.timezone == "Asia/Tokyo"
    assert settings.morning_off_start == "09:00"

def test_attendance_info_validation():
    info = AttendanceInfo(
        target_date=date(2026, 6, 28),
        attendance_type="morning_off",
        reason="Doctor",
        original_message="Taking tomorrow morning off"
    )
    assert info.target_date.isoformat() == "2026-06-28"

def test_task_execution_state_subtasks():
    state = TaskExecutionState(client_msg_id="msg_123")
    state.subtasks["jobcan"] = SubTaskStatus(success=True, executed_at="2026-06-27T10:00:00")
    assert state.subtasks["jobcan"].success is True
    assert "slack_post" not in state.subtasks
