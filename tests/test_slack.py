import pytest
from unittest.mock import patch
from src.slack import SlackManager
from slack_sdk.errors import SlackApiError


@pytest.fixture
def slack_manager():
    with patch("src.slack.WebClient") as mock_web:
        manager = SlackManager(token="test-token")
        # Keep track of the mock instance created during __init__
        manager.mock_client = mock_web.return_value
        yield manager


def test_post_attendance_report_success(slack_manager):
    slack_manager.mock_client.chat_postMessage.return_value = {"ts": "1234.567"}

    ts = slack_manager.post_attendance_report("C1", "hello")

    assert ts == "1234.567"
    slack_manager.mock_client.chat_postMessage.assert_called_once()


def test_post_attendance_report_failure(slack_manager):
    slack_manager.mock_client.chat_postMessage.side_effect = SlackApiError(
        "Error", {"error": "channel_not_found"}
    )

    ts = slack_manager.post_attendance_report("C1", "hello")

    assert ts is None


def test_reply_to_thread_success(slack_manager):
    slack_manager.reply_to_thread("C1", "ts.123", "reply text")

    slack_manager.mock_client.chat_postMessage.assert_called_with(
        channel="C1", thread_ts="ts.123", text="reply text"
    )


def test_reply_to_thread_failure(slack_manager):
    slack_manager.mock_client.chat_postMessage.side_effect = SlackApiError(
        "Error", {"error": "thread_not_found"}
    )

    # Should not raise exception
    slack_manager.reply_to_thread("C1", "ts.123", "reply text")


@patch("src.slack.WebClient")
def test_set_user_status_success(mock_web_client, slack_manager):
    # This call creates a NEW WebClient inside set_user_status
    mock_user_client = mock_web_client.return_value

    slack_manager.set_user_status("user-token", "Working Remotely", ":house:", 12345)

    mock_web_client.assert_any_call(token="user-token")
    mock_user_client.users_profile_set.assert_called_once_with(
        profile={
            "status_text": "Working Remotely",
            "status_emoji": ":house:",
            "status_expiration": 12345,
        }
    )


@patch("src.slack.WebClient")
def test_set_user_status_failure(mock_web_client, slack_manager):
    mock_user_client = mock_web_client.return_value
    mock_user_client.users_profile_set.side_effect = SlackApiError(
        "Error", {"error": "invalid_auth"}
    )

    slack_manager.set_user_status("user-token", "Working Remotely", ":house:")


def test_get_user_info_success(slack_manager):
    slack_manager.mock_client.users_info.return_value = {
        "user": {"id": "U1", "name": "testuser"}
    }

    user = slack_manager.get_user_info("U1")

    assert user["id"] == "U1"
    slack_manager.mock_client.users_info.assert_called_with(user="U1")


def test_get_user_info_failure(slack_manager):
    slack_manager.mock_client.users_info.side_effect = SlackApiError(
        "Error", {"error": "user_not_found"}
    )

    user = slack_manager.get_user_info("U1")
    assert user is None
