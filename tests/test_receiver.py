import pytest
import hmac
import hashlib
import time
from unittest.mock import patch
from src.receiver import app, verify_slack_signature


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def generate_slack_signature(secret, timestamp, body):
    sig_basestring = f"v0:{timestamp}:{body}"
    my_signature = (
        "v0="
        + hmac.new(
            secret.encode("utf-8"), sig_basestring.encode("utf-8"), hashlib.sha256
        ).hexdigest()
    )
    return my_signature


@patch("src.receiver.tasks_v2.CloudTasksClient")
@patch("src.receiver.verify_slack_signature")
@patch("os.getenv")
def test_receiver_endpoint_with_auth(
    mock_getenv, mock_verify, mock_tasks_client, client
):
    # Setup mocks
    mock_verify.return_value = True
    mock_inst = mock_tasks_client.return_value

    # Mock env vars for OIDC and Signature
    def side_effect(key, default=None):
        vals = {
            "SLACK_SIGNING_SECRET": "secret",
            "RECEIVER_SA_EMAIL": "receiver@example.com",
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "WORKER_URL": "https://worker-url",
        }
        return vals.get(key, default)

    mock_getenv.side_effect = side_effect

    payload = {
        "event": {
            "type": "message",
            "client_msg_id": "msg1",
            "user": "U1",
            "text": "test",
            "channel": "C1",
            "ts": "123.456",
        }
    }

    response = client.post("/slack/events", json=payload)
    assert response.status_code == 200
    assert response.data.decode() == "OK"

    # Verify OIDC token was added to the task
    args, kwargs = mock_inst.create_task.call_args
    task = kwargs["request"]["task"]
    assert (
        task["http_request"]["oidc_token"]["service_account_email"]
        == "receiver@example.com"
    )


def test_receiver_url_verification(client):
    payload = {"type": "url_verification", "challenge": "abc"}
    response = client.post("/slack/events", json=payload)
    assert response.status_code == 200
    assert response.get_json()["challenge"] == "abc"


def test_verify_slack_signature_logic(client):
    secret = "secret"
    timestamp = str(int(time.time()))
    body = '{"test": "data"}'
    signature = generate_slack_signature(secret, timestamp, body)

    with app.test_request_context(
        path="/slack/events",
        method="POST",
        data=body,
        headers={
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": signature,
        },
    ):
        assert verify_slack_signature(secret) is True


def test_verify_slack_signature_invalid(client):
    secret = "secret"
    timestamp = str(int(time.time()))
    body = '{"test": "data"}'

    with app.test_request_context(
        path="/slack/events",
        method="POST",
        data=body,
        headers={
            "X-Slack-Request-Timestamp": timestamp,
            "X-Slack-Signature": "invalid",
        },
    ):
        assert verify_slack_signature(secret) is False


def test_receiver_ignored_events(client):
    # Bot message should be ignored
    payload = {"event": {"type": "message", "bot_id": "B1", "text": "bot message"}}
    response = client.post("/slack/events", json=payload)
    assert response.status_code == 200
    assert response.data.decode() == "Ignored"

    # Non-message event should be ignored
    payload = {"event": {"type": "reaction_added"}}
    response = client.post("/slack/events", json=payload)
    assert response.status_code == 200
    assert response.data.decode() == "Ignored"
