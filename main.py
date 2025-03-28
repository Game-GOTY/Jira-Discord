from flask import Flask, request
import requests
import os

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
print(f"DISCORD_WEBHOOK_URL: {DISCORD_WEBHOOK_URL}")  # Debug


@app.route("/webhook", methods=["POST"])
def jira_webhook():
    print(f"Headers: {request.headers}")
    print(f"Content-Type: {request.content_type}")
    print(f"Raw Data: {request.get_data(as_text=True)}")
    print(f"Query Params: {request.args}")

    if not DISCORD_WEBHOOK_URL:
        return "DISCORD_WEBHOOK_URL not set in environment", 500

    # Optional: Validate Jira secret token only if Jira sends a specific header
    jira_token = os.environ.get("JIRA_SECRET_TOKEN")
    if jira_token:
        received_token = request.headers.get(
            "X-Jira-Webhook-Token", ""
        )  # Adjust header name if needed
        if received_token != jira_token:
            print(f"Token mismatch: expected {jira_token}, got {received_token}")
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
        event_type = data["webhookEvent"]
        message = f"**{issue_key}** - {event_type}: {issue_summary}"
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
