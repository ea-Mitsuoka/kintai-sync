import os
from google.cloud import firestore
from typing import Optional, Dict, Any

class HistoryManager:
    def __init__(self, project_id: str = None):
        if not project_id:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.db = firestore.Client(project=project_id)
        self.tasks_collection = "tasks"
        self.users_collection = "users"

    def get_task_status(self, client_msg_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the status of a task from Firestore.
        """
        doc_ref = self.db.collection(self.tasks_collection).document(client_msg_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None

    def update_task_status(self, client_msg_id: str, status: str, subtasks: Dict[str, str] = None):
        """
        Updates the status of a task in Firestore.
        """
        data = {"status": status}
        if subtasks:
            data["subtasks"] = subtasks
        self.db.collection(self.tasks_collection).document(client_msg_id).set(data, merge=True)

    def get_user_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieves user-specific settings from Firestore.
        Returns default settings if not found.
        """
        doc_ref = self.db.collection(self.users_collection).document(user_id)
        doc = doc_ref.get()
        
        defaults = {
            "morning_off_start": "09:00",
            "morning_off_end": "13:00",
            "afternoon_off_start": "14:00",
            "afternoon_off_end": "18:00",
            "working_hours_start": "09:00",
            "working_hours_end": "18:00",
            "timezone": "Asia/Tokyo"
        }

        if doc.exists:
            settings = doc.to_dict()
            # Merge with defaults to ensure all keys are present
            return {**defaults, **settings}
        return defaults

    def set_user_settings(self, user_id: str, settings: Dict[str, Any]):
        """
        Saves user-specific settings to Firestore.
        """
        self.db.collection(self.users_collection).document(user_id).set(settings, merge=True)
