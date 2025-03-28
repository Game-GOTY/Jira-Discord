from flask import Flask, request
import requests
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")


@app.route("/webhook", methods=["POST"])
def jira_webhook():
    print(f"Headers: {request.headers}")
    print(f"Content-Type: {request.content_type}")
    print(f"Raw Data: {request.get_data(as_text=True)}")
    print(f"Query Params: {request.args}")

    if not DISCORD_WEBHOOK_URL:
        return "DISCORD_WEBHOOK_URL not set in environment", 500

    # Token validation (disabled unless Jira sends a specific header)
    jira_token = os.environ.get("JIRA_SECRET_TOKEN")
    if jira_token and "X-Jira-Webhook-Token" in request.headers:
        received_token = request.headers.get("X-Jira-Webhook-Token", "")
        if received_token != jira_token:
            print(f"Jira Token mismatch")
            return "Invalid token", 403

    # Handle empty or non-JSON requests
    if not request.content_type or request.content_length == 0:
        query_user = request.args.get("triggeredByUser", "Unknown")
        message = (
            f"Webhook ping or empty request received. Triggered by user: {query_user}"
        )
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        if response.status_code == 204:
            return "Success (empty request handled)", 200
        else:
            return f"Failed to send to Discord: {response.text}", 500

    # Try to parse JSON payload
    try:
        data = request.json
        issue_key = data["issue"]["key"]
        issue_summary = data["issue"]["fields"]["summary"]
        event_type = data["webhookEvent"].split(":")[1]
        user = data["user"]["displayName"]
        time = (
            datetime.fromtimestamp(data["timestamp"] / 1000, timezone.utc)
            .astimezone(data["user"]["timeZone"])
            .strftime("%Y-%m-%d %H:%M:%S")
        )
        message = f"**{issue_key}** - {event_type}: {issue_summary} by {user} at {time}.\nURL: https://goty.atlassian.net/browse/{issue_key}/"
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        if response.status_code == 204:
            return "Success", 200
        else:
            return f"Failed to send to Discord: {response.text}", 500
    except Exception as e:
        print(f"Error: {e}")
        return "Invalid payload", 415


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
