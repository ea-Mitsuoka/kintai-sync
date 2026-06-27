import os
import json
import hashlib
import hmac
import time
from flask import Flask, request, jsonify
from google.cloud import tasks_v2

app = Flask(__name__)

def verify_slack_signature(signing_secret: str):
    """Verifies the signature of a Slack request."""
    timestamp = request.headers.get('X-Slack-Request-Timestamp')
    signature = request.headers.get('X-Slack-Signature')
    
    if not timestamp or not signature:
        return False
    
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False
    
    sig_basestring = f"v0:{timestamp}:{request.get_data().decode('utf-8')}"
    my_signature = 'v0=' + hmac.new(
        signing_secret.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(my_signature, signature)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    """Endpoint for Slack Events API."""
    data = request.get_json()
    
    # 1. URL Verification (for first time setup)
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})

    # 2. Verify Signature
    # signing_secret = os.getenv("SLACK_SIGNING_SECRET")
    # if not verify_slack_signature(signing_secret):
    #     return "Invalid signature", 403

    event = data.get("event")
    if not event or event.get("type") != "message" or "bot_id" in event:
        return "Ignored", 200

    # 3. Create Cloud Task
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    queue = os.getenv("QUEUE_ID", "kintai-sync-queue")
    location = os.getenv("REGION", "asia-northeast1")
    url = os.getenv("WORKER_URL")

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project, location, queue)
    
    task_payload = {
        "client_msg_id": event.get("client_msg_id"),
        "user_id": event.get("user"),
        "text": event.get("text"),
        "channel_id": event.get("channel"),
        "ts": event.get("ts")
    }

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-type": "application/json"},
            "body": json.dumps(task_payload).encode()
        }
    }

    # Add OIDC token for authentication between Cloud Run services
    # service_account_email = os.getenv("RECEIVER_SA_EMAIL")
    # task["http_request"]["oidc_token"] = {"service_account_email": service_account_email}

    client.create_task(request={"parent": parent, "task": task})

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
