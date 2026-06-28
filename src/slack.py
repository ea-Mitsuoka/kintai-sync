import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import Optional


class SlackManager:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        self.client = WebClient(token=self.token)

    def post_attendance_report(self, channel_id: str, text: str) -> Optional[str]:
        """
        Posts an attendance report to the designated channel.
        Returns the timestamp (ts) of the message.
        """
        try:
            response = self.client.chat_postMessage(channel=channel_id, text=text)
            return response["ts"]
        except SlackApiError as e:
            print(f"Error posting message to Slack: {e.response['error']}")
            return None

    def reply_to_thread(self, channel_id: str, thread_ts: str, text: str):
        """
        Replies to a specific thread (usually the original attendance message).
        """
        try:
            self.client.chat_postMessage(
                channel=channel_id, thread_ts=thread_ts, text=text
            )
        except SlackApiError as e:
            print(f"Error replying to thread: {e.response['error']}")

    def set_user_status(
        self, user_token: str, status_text: str, status_emoji: str, expiration: int = 0
    ):
        """
        Updates the user's Slack status.
        Requires a User Token (xoxp-...) with 'users.profile:write' scope.
        """
        user_client = WebClient(token=user_token)
        try:
            user_client.users_profile_set(
                profile={
                    "status_text": status_text,
                    "status_emoji": status_emoji,
                    "status_expiration": expiration,
                }
            )
        except SlackApiError as e:
            print(f"Error setting user status: {e.response['error']}")

    def get_user_info(self, user_id: str):
        """
        Retrieves user information.
        """
        try:
            response = self.client.users_info(user=user_id)
            return response["user"]
        except SlackApiError as e:
            print(f"Error getting user info: {e.response['error']}")
            return None
