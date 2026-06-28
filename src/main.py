import os
from flask import Flask, request, jsonify
from src.parser import MessageParser
from src.history import HistoryManager
from src.secrets import get_jobcan_password, get_slack_user_token
from src.jobcan import JobcanManager
from src.slack import SlackManager
from src.calendar import CalendarManager
from src.sync import SettingsSyncer
from src.models import TaskExecutionState, SubTaskStatus
from src.config import config
from datetime import datetime, time, date
from typing import Tuple

app = Flask(__name__)


@app.route("/worker", methods=["POST"])
async def worker():
    """
    Main worker entry point triggered by Cloud Tasks.
    """
    data = request.get_json()
    client_msg_id = data.get("client_msg_id")
    user_id = data.get("user_id")
    message_text = data.get("text")
    channel_id = data.get("channel_id")
    thread_ts = data.get("ts")

    history_manager = HistoryManager()

    # 1. Idempotency & State Recovery
    existing_data = history_manager.get_task_status(client_msg_id)
    if existing_data and existing_data.get("status") == "success":
        return jsonify({"status": "already_processed"}), 200

    # Load previous subtask results if any
    prev_subtasks = existing_data.get("subtasks", {}) if existing_data else {}

    # 2. Parse Message
    parser = MessageParser()
    try:
        attendance_info = parser.parse(message_text)
    except Exception as e:
        return jsonify({"status": "parse_error", "error": str(e)}), 400

    # Early exit if no attendance action is needed
    if attendance_info.attendance_type == "none" or not attendance_info.target_dates:
        slack = SlackManager()
        slack.reply_to_thread(
            channel_id,
            thread_ts,
            "✅ メッセージを確認しました（勤怠申請は必要ないと判断しました）。",
        )
        history_manager.update_task_status(
            client_msg_id, "success", {"info": "no_action_needed"}
        )
        return jsonify({"status": "success"}), 200

    # 3. Get User Settings
    spreadsheet_id = os.getenv("SETTINGS_SPREADSHEET_ID")
    if spreadsheet_id:
        try:
            SettingsSyncer(spreadsheet_id).sync_if_stale()
        except Exception as e:
            print(f"Settings refresh skipped: {e}")

    settings_dict = history_manager.get_user_settings(user_id)

    # Initialize execution state
    execution_state = TaskExecutionState(client_msg_id=client_msg_id)
    for k, v in prev_subtasks.items():
        execution_state.subtasks[k] = SubTaskStatus(**v)

    history_manager.update_task_status(client_msg_id, "processing")

    slack = SlackManager()

    # 4. Execute Subtasks (Jobcan, Slack Post, Calendar, Slack Status)

    # --- Loop over target dates for Jobcan and Calendar ---
    for target_date in attendance_info.target_dates:
        date_str = target_date.isoformat()

        # Jobcan
        jobcan_key = f"jobcan:{date_str}"
        if (
            not execution_state.subtasks.get(jobcan_key)
            or not execution_state.subtasks[jobcan_key].success
        ):
            try:
                jobcan_password = get_jobcan_password(
                    settings_dict["jobcan_staff_code"]
                )
                jobcan = JobcanManager(
                    settings_dict["jobcan_company_id"],
                    settings_dict["jobcan_staff_code"],
                    jobcan_password,
                )
                success = await jobcan.apply_holiday(
                    target_date, attendance_info.attendance_type, attendance_info.reason
                )
                execution_state.subtasks[jobcan_key] = SubTaskStatus(
                    success=success, executed_at=datetime.now().isoformat()
                )
            except Exception as e:
                execution_state.subtasks[jobcan_key] = SubTaskStatus(
                    success=False, error_message=str(e)
                )

        # Google Calendar
        cal_key = f"google_calendar:{date_str}"
        if (
            not execution_state.subtasks.get(cal_key)
            or not execution_state.subtasks[cal_key].success
        ):
            try:
                user_info = slack.get_user_info(user_id)
                user_email = user_info.get("profile", {}).get("email")
                if user_email:
                    calendar = CalendarManager(user_email)
                    start_dt, end_dt = _get_event_times(
                        target_date, attendance_info.attendance_type, settings_dict
                    )
                    summary = f"【勤怠】{attendance_info.attendance_type}: {attendance_info.reason or ''}"
                    event_id = calendar.register_event(summary, start_dt, end_dt)
                    execution_state.subtasks[cal_key] = SubTaskStatus(
                        success=True if event_id else False
                    )
                else:
                    execution_state.subtasks[cal_key] = SubTaskStatus(
                        success=False, error_message="Email not found"
                    )
            except Exception as e:
                execution_state.subtasks[cal_key] = SubTaskStatus(
                    success=False, error_message=str(e)
                )

    # --- Slack Post (once per message) ---
    if (
        not execution_state.subtasks.get("slack_post")
        or not execution_state.subtasks["slack_post"].success
    ):
        dept_channel_id = settings_dict.get("dept_channel_id")
        if dept_channel_id:
            dates_str = ", ".join([d.isoformat() for d in attendance_info.target_dates])
            report_format = config.get("slack.report_format")
            report_text = report_format.format(
                user_id=user_id,
                target_date=dates_str,
                attendance_type=attendance_info.attendance_type,
            )
            ts = slack.post_attendance_report(dept_channel_id, report_text)
            execution_state.subtasks["slack_post"] = SubTaskStatus(
                success=True if ts else False
            )
        else:
            execution_state.subtasks["slack_post"] = SubTaskStatus(
                success=True, error_message="No dept channel"
            )

    # --- Slack Status (once per message, using the first date as reference) ---
    if (
        not execution_state.subtasks.get("slack_status")
        or not execution_state.subtasks["slack_status"].success
    ):
        user_token = get_slack_user_token(user_id)
        if user_token:
            mapping = config.get("slack.status_mapping", {}).get(
                attendance_info.attendance_type, {}
            )
            if mapping:
                slack.set_user_status(
                    user_token, mapping.get("text", ""), mapping.get("emoji", "")
                )
                execution_state.subtasks["slack_status"] = SubTaskStatus(success=True)
            else:
                execution_state.subtasks["slack_status"] = SubTaskStatus(
                    success=True, error_message="No mapping"
                )
        else:
            execution_state.subtasks["slack_status"] = SubTaskStatus(
                success=False, error_message="Token missing"
            )

    # 5. Finalize and Feedback
    overall_success = all(s.success for s in execution_state.subtasks.values())
    status = "success" if overall_success else "partial_failure"

    history_manager.update_task_status(
        client_msg_id, status, execution_state.model_dump()["subtasks"]
    )

    feedback_header = config.get("slack.feedback_header")
    feedback_text = (
        feedback_header
        + "\n"
        + "\n".join(
            [
                f"- {k}: {'✅' if v.success else '❌' + (f' ({v.error_message})' if v.error_message else '')}"
                for k, v in execution_state.subtasks.items()
            ]
        )
    )
    slack.reply_to_thread(channel_id, thread_ts, feedback_text)

    return jsonify({"status": status}), 200


def _get_event_times(
    target_date: date, t_type: str, settings: dict
) -> Tuple[datetime, datetime]:
    """Helper to calculate event start/end times."""
    if t_type == "full_day":
        start = time.fromisoformat(settings["working_hours_start"])
        end = time.fromisoformat(settings["working_hours_end"])
    elif t_type == "morning_off":
        start = time.fromisoformat(settings["morning_off_start"])
        end = time.fromisoformat(settings["morning_off_end"])
    elif t_type == "afternoon_off":
        start = time.fromisoformat(settings["afternoon_off_start"])
        end = time.fromisoformat(settings["afternoon_off_end"])
    else:
        start = time.fromisoformat(settings["working_hours_start"])
        end = time.fromisoformat(settings["working_hours_end"])

    return (datetime.combine(target_date, start), datetime.combine(target_date, end))


# Production entry point for Gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
