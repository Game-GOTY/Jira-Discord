from flask import Flask, request
import requests
import os

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
print(f"DISCORD_WEBHOOK_URL: {DISCORD_WEBHOOK_URL}")
JIRA_SECRET_TOKEN = os.environ.get("JIRA_SECRET_TOKEN")  # Optional
print(f"JIRA: {JIRA_SECRET_TOKEN}")


@app.route("/webhook", methods=["POST"])
def jira_webhook():
    # Log request details
    print(f"Headers: {request.headers}")
    print(f"Content-Type: {request.content_type}")
    print(f"Raw Data: {request.get_data(as_text=True)}")
    print(f"Query Params: {request.args}")  # Capture query string like ?triggeredByUser

    # Optional: Validate Jira secret token
    received_token = request.headers.get("X-Hub-Signature", "")
    if JIRA_SECRET_TOKEN and received_token != JIRA_SECRET_TOKEN:
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
            return "Failed to send to Discord", 500

    # Try to parse JSON payload
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
