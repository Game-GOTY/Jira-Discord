from flask import Flask, request
import requests
import os

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
JIRA_SECRET_TOKEN = os.environ.get("JIRA_SECRET_TOKEN")  # Optional


@app.route("/webhook", methods=["POST"])
def jira_webhook():
    print(f"Headers: {request.headers}")
    print(f"Content-Type: {request.content_type}")
    print(f"Raw Data: {request.get_data(as_text=True)}")

    if request.content_type == "application/x-www-form-urlencoded":
        data = request.form
        triggered_by = data.get("triggeredByUser", "Unknown")
        message = f"Webhook triggered by user: {triggered_by}"
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        if response.status_code == 204:
            return "Success", 200
        else:
            return "Failed to send to Discord", 500

    # Existing JSON handling
    try:
        data = request.json
        issue_key = data["issue"]["key"]
        issue_summary = data["issue"]["fields"]["summary"]
        event_type = data["webhookEvent"]
        message = f"**{issue_key}** - {event_type}: {issue_summary}"
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        if response.status_code == 204:
            return "Success", 200
        else:
            return "Failed to send to Discord", 500
    except Exception as e:
        print(f"Error: {e}")
        return "Invalid payload", 415
