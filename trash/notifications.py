# src/notifications.py
# wrapper for the Pushover API
#### Define Pushover as an LLM Tool and add it to tools list

import requests
from config import PUSHOVER_USER, PUSHOVER_TOKEN

# Load Pushover API keys from environment 
PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

# Function to send push notification via Pushover
def send_notification(message: str):
    payload = {"user": PUSHOVER_USER, "token": PUSHOVER_TOKEN,"message":message}
    requests.post(pushover_url, data=payload)

send_notification_function_d = {
    "name": "send_notification",
    "description": (
        "Send a message to Mamta via Pushover notification. "
        "If the user asks to contact Mamta, send her a notification. "
        "If you previously asked the user what message to send and the user "
        "replies with the message text, call this tool immediately."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "message": {"type": "string", "description": "notification message to send to the user's device"}
        },
        "required": ["message"],
    },
}
