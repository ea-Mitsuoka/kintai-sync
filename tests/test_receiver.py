import pytest
from unittest.mock import MagicMock, patch
from src.receiver import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@patch("src.receiver.tasks_v2.CloudTasksClient")
def test_receiver_endpoint(mock_tasks_client, client):
    mock_inst = mock_tasks_client.return_value
    
    payload = {
        "event": {
            "type": "message",
            "client_msg_id": "msg1",
            "user": "U1",
            "text": "test",
            "channel": "C1",
            "ts": "123.456"
        }
    }
    
    response = client.post("/slack/events", json=payload)
    assert response.status_code == 200
    assert response.data.decode() == "OK"
    mock_inst.create_task.assert_called_once()

def test_receiver_url_verification(client):
    payload = {"type": "url_verification", "challenge": "abc"}
    response = client.post("/slack/events", json=payload)
    assert response.status_code == 200
    assert response.get_json()["challenge"] == "abc"
