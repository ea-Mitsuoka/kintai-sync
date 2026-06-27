from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, GenerationConfig
from datetime import date, datetime
from src.models import AttendanceInfo
import json
import os

class MessageParser:
    def __init__(self, project_id: str = None, location: str = "us-central1"):
        if not project_id:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        aiplatform.init(project=project_id, location=location)
        self.model = GenerativeModel("gemini-1.5-flash")

    def parse(self, message: str, current_date: date = None) -> AttendanceInfo:
        """
        Parses a Slack message and returns structured AttendanceInfo.
        """
        if not current_date:
            current_date = date.today()

        prompt = f"""
        Extract attendance information from the following Slack message.
        Today's date is {current_date.isoformat()}.
        
        Message: "{message}"
        
        Output must be a JSON object with the following keys:
        - target_date: ISO 8601 format (YYYY-MM-DD)
        - attendance_type: One of "full_day", "morning_off", "afternoon_off", "late", "early", "flex"
        - reason: Brief reason for the attendance change
        """

        try:
            # Request JSON output
            response = self.model.generate_content(
                prompt,
                generation_config=GenerationConfig(response_mime_type="application/json")
            )
            data = json.loads(response.text)
            
            return AttendanceInfo(
                target_date=data["target_date"],
                attendance_type=data["attendance_type"],
                reason=data.get("reason"),
                original_message=message
            )
        except Exception as e:
            print(f"Error parsing message with Gemini: {e}")
            raise
