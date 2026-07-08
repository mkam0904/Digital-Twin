"""Tests for Notifier: payload correctness with requests mocked."""

import notifications
from notifications import Notifier


def test_send_posts_correct_payload(monkeypatch):
    captured = {}

    def fake_post(url, data=None):
        captured["url"] = url
        captured["data"] = data

    monkeypatch.setattr(notifications.requests, "post", fake_post)

    n = Notifier(user_key="user123", api_token="tok456")
    n.send("test message")

    assert captured["url"] == n.url
    assert captured["data"] == {
        "user": "user123",
        "token": "tok456",
        "message": "test message",
    }


def test_tool_spec_shape():
    n = Notifier(user_key="u", api_token="t")
    spec = n.tool_spec
    assert spec["name"] == "send_notification"
    assert spec["parameters"]["required"] == ["message"]
    assert "message" in spec["parameters"]["properties"]