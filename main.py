from flask import Flask, request
import requests
import os

app = Flask(__name__)

# Load secrets from Replit environment variables
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
JIRA_SECRET_TOKEN = os.environ.get("JIRA_SECRET_TOKEN")  # Optional


@app.route("/webhook", methods=["POST"])
def jira_webhook():
    # Optional: Validate Jira secret token if configured
    received_token = request.headers.get(
        "X-Hub-Signature", ""
    )  # Adjust header if Jira uses something else
    if JIRA_SECRET_TOKEN and received_token != JIRA_SECRET_TOKEN:
        return "Invalid token", 403

    # Get JSON data from Jira webhook
    data = request.json

    # Extract useful info from Jira payload
    try:
        issue_key = data["issue"]["key"]
        issue_summary = data["issue"]["fields"]["summary"]
        event_type = data["webhookEvent"]

        # Craft a message for Discord
        message = f"**{issue_key}** - {event_type}: {issue_summary}"

        # Send to Discord
        payload = {"content": message}
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)

        if response.status_code == 204:
            return "Success", 200
        else:
            return "Failed to send to Discord", 500
    except KeyError as e:
        print(f"Error: {e}, Data: {data}")  # Debug in Replit console
        return "Invalid Jira payload", 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
