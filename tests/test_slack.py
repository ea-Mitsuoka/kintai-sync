import pytest
from unittest.mock import MagicMock, patch
from src.slack import SlackManager

@patch("src.slack.WebClient")
def test_post_attendance_report_success(mock_web_client):
    mock_instance = mock_web_client.return_value
    mock_instance.chat_postMessage.return_value = {"ts": "1234.567"}
    
    manager = SlackManager(token="test-token")
    ts = manager.post_attendance_report("C1", "hello")
    
    assert ts == "1234.567"
    mock_instance.chat_postMessage.assert_called_once()

@patch("src.slack.WebClient")
def test_reply_to_thread(mock_web_client):
    mock_instance = mock_web_client.return_value
    manager = SlackManager(token="test-token")
    manager.reply_to_thread("C1", "ts.123", "reply text")
    
    mock_instance.chat_postMessage.assert_called_with(
        channel="C1",
        thread_ts="ts.123",
        text="reply text"
    )
