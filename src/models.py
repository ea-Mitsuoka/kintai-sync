from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import date

class UserSettings(BaseModel):
    """
    Configuration for an individual user, managed via Google Sheets and cached in Firestore.
    """
    slack_user_id: str
    morning_off_start: str = "09:00"
    morning_off_end: str = "13:00"
    afternoon_off_start: str = "14:00"
    afternoon_off_end: str = "18:00"
    working_hours_start: str = "09:00"
    working_hours_end: str = "18:00"
    timezone: str = "Asia/Tokyo"

class AttendanceInfo(BaseModel):
    """
    Structured data extracted from a Slack message by Gemini API.
    """
    target_date: date
    attendance_type: str  # e.g., "full_day", "morning_off", "afternoon_off", "late", "early"
    reason: Optional[str] = None
    original_message: str

class SubTaskStatus(BaseModel):
    """
    Execution status of an individual sub-task.
    """
    success: bool = False
    error_message: Optional[str] = None
    executed_at: Optional[str] = None

class TaskExecutionState(BaseModel):
    """
    Overall execution state of a sync request, stored in Firestore for idempotency.
    """
    client_msg_id: str
    overall_status: str = "pending"  # pending, processing, success, partial_failure, failure
    subtasks: Dict[str, SubTaskStatus] = Field(default_factory=dict)
    # Keys in subtasks: "jobcan", "slack_post", "google_calendar", "slack_status", "feedback"
