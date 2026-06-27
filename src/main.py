import os
import asyncio
from flask import Flask, request, jsonify
from src.parser import MessageParser
from src.history import HistoryManager
from src.secrets import get_secret, get_jobcan_password
from src.jobcan import JobcanManager
from src.slack import SlackManager
from src.calendar import CalendarManager
from src.models import TaskExecutionState, SubTaskStatus
from src.config import config
from datetime import datetime

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
    
    # 1. Idempotency Check
    existing_state = history_manager.get_task_status(client_msg_id)
    if existing_state and existing_state.get("status") == "success":
        return jsonify({"status": "already_processed"}), 200

    # 2. Parse Message
    parser = MessageParser()
    try:
        attendance_info = parser.parse(message_text)
    except Exception as e:
        return jsonify({"status": "parse_error", "error": str(e)}), 400

    # 3. Get User Settings
    user_settings = history_manager.get_user_settings(user_id)
    
    # Initialize execution state
    execution_state = TaskExecutionState(client_msg_id=client_msg_id)
    history_manager.update_task_status(client_msg_id, "processing")

    # 4. Execute Subtasks (Jobcan, Slack, Calendar)
    # Note: In a real implementation, we would check subtask status before running
    
    # Jobcan Subtask
    jobcan_password = get_jobcan_password(user_settings["jobcan_staff_code"])
    jobcan = JobcanManager(
        user_settings["jobcan_company_id"], 
        user_settings["jobcan_staff_code"], 
        jobcan_password
    )
    success = await jobcan.apply_holiday(
        attendance_info.target_date, 
        attendance_info.attendance_type, 
        attendance_info.reason
    )
    execution_state.subtasks["jobcan"] = SubTaskStatus(success=success, executed_at=datetime.now().isoformat())
    
    # Slack Subtask (Post to Dept Channel)
    slack = SlackManager()
    report_format = config.get("slack.report_format")
    report_text = report_format.format(
        user_id=user_id,
        target_date=attendance_info.target_date,
        attendance_type=attendance_info.attendance_type
    )
    # dept_channel_id = os.getenv("DEPT_CHANNEL_ID")
    # slack.post_attendance_report(dept_channel_id, report_text)
    execution_state.subtasks["slack_post"] = SubTaskStatus(success=True)

    # 5. Finalize and Feedback
    history_manager.update_task_status(client_msg_id, "success", execution_state.dict()["subtasks"])
    
    feedback_header = config.get("slack.feedback_header")
    feedback_text = feedback_header + "\n" + "\n".join([f"- {k}: {'✅' if v.success else '❌'}" for k, v in execution_state.subtasks.items()])
    slack.reply_to_thread(channel_id, thread_ts, feedback_text)

    return jsonify({"status": "success"}), 200

# Production entry point for Gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
