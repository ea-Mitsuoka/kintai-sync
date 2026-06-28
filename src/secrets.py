import os
from google.cloud import secretmanager
from typing import Optional

def get_secret(secret_id: str, project_id: str = None) -> str:
    """
    Retrieves a secret from Google Cloud Secret Manager.
    If running locally or secret is missing, falls back to environment variables.
    """
    if not project_id:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    
    # If no project_id is found, we assume local development or fallback
    if not project_id:
        return os.getenv(secret_id, "")

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        # Log the error (in a real app, use a proper logger)
        print(f"Error accessing secret {secret_id} in project {project_id}: {e}")
        # Fallback to env var
        return os.getenv(secret_id, "")

def get_jobcan_password(staff_code: str) -> str:
    """
    Retrieves the Jobcan password for a specific staff code.
    Naming convention: JOBCAN_PASSWORD_[staff_code]
    """
    secret_id = f"JOBCAN_PASSWORD_{staff_code.replace('-', '_')}"
    return get_secret(secret_id)

def get_slack_user_token(user_id: str) -> str:
    """
    Retrieves the Slack User Token (xoxp-...) for a specific user.
    Naming convention: SLACK_USER_TOKEN_[user_id]
    """
    secret_id = f"SLACK_USER_TOKEN_{user_id.replace('-', '_')}"
    return get_secret(secret_id)
