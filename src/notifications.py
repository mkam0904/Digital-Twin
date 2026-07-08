"""Pushover notification tool."""

from dataclasses import dataclass
import requests

__all__ = ["Notifier"]


@dataclass
class Notifier:
    """Sends push notifications via Pushover.

    Attributes:
        user_key: Pushover user key.
        api_token: Pushover application token.
        url: Pushover API endpoint.
    """

    user_key: str
    api_token: str
    url: str = "https://api.pushover.net/1/messages.json"

    def send(self, message: str) -> None:
        """Send a push notification.

        Args:
            message: The notification text to send.
        """
        payload = {"user": self.user_key, "token": self.api_token, "message": message}
        requests.post(self.url, data=payload)

    @property
    def tool_spec(self) -> dict:
        """OpenAI function-calling spec for this tool."""
        return {
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
                    "message": {
                        "type": "string",
                        "description": "notification message to send to the user's device",
                    }
                },
                "required": ["message"],
            },
        }