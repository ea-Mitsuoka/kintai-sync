from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, GenerationConfig
from datetime import date
from src.models import AttendanceInfo
from src.config import config
import json
import os


class MessageParser:
    def __init__(self, project_id: str = None, location: str = None):
        if not project_id:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not location:
            location = config.get("gcp.location")
        aiplatform.init(project=project_id, location=location)
        self.model = GenerativeModel(config.get("gemini.model_name"))

    def parse(self, message: str, current_date: date = None) -> AttendanceInfo:
        """
        Parses a Slack message and returns structured AttendanceInfo.
        """
        if not current_date:
            current_date = date.today()

        prompt_template = config.get("gemini.prompt_template")
        prompt = prompt_template.format(
            current_date=current_date.isoformat(), message=message
        )

        try:
            # Request JSON output
            response = self.model.generate_content(
                prompt,
                generation_config=GenerationConfig(
                    response_mime_type="application/json"
                ),
            )
            data = json.loads(response.text)

            return AttendanceInfo(
                target_dates=data.get("target_dates", []),
                attendance_type=data["attendance_type"],
                reason=data.get("reason"),
                original_message=message,
            )
        except Exception as e:
            print(f"Error parsing message with Gemini: {e}")
            raise
