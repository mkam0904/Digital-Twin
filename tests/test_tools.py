"""Tests for ToolRegistry: spec assembly and dispatch, no network needed."""

import json
from types import SimpleNamespace

from tools import ToolRegistry


class StubNotifier:
    """Records sends instead of calling Pushover."""

    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)

    @property
    def tool_spec(self):
        return {
            "name": "send_notification",
            "description": "stub",
            "parameters": {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"],
            },
        }


class StubFifaClient:
    def today_cards(self):
        return "<pre><b>WINNER</b> 1 vs 0 Loser</pre>"


def make_tool_call(name, arguments="{}", call_id="call_1"):
    """Mimic the OpenAI tool_call object shape (attribute access)."""
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def make_registry():
    return ToolRegistry(notifier=StubNotifier(), fifa_client=StubFifaClient())


def test_specs_include_expected_tools():
    reg = make_registry()
    names = [s["function"]["name"] for s in reg.specs]
    assert "roll_dice" in names
    assert "send_notification" in names
    assert "get_world_cup_schedule" in names


def test_dispatch_roll_dice_returns_valid_result():
    reg = make_registry()
    results = reg.dispatch([make_tool_call("roll_dice")])
    assert len(results) == 1
    r = results[0]
    assert r["role"] == "tool"
    assert r["tool_call_id"] == "call_1"
    value = int(r["content"].rsplit(":", 1)[1].strip())
    assert 1 <= value <= 6


def test_dispatch_send_notification_calls_notifier():
    reg = make_registry()
    args = json.dumps({"message": "hello Mamta"})
    results = reg.dispatch([make_tool_call("send_notification", arguments=args)])
    assert reg.notifier.sent == ["hello Mamta"]
    assert "hello Mamta" in results[0]["content"]


def test_dispatch_world_cup_strips_html_tags():
    reg = make_registry()
    results = reg.dispatch([make_tool_call("get_world_cup_schedule")])
    content = results[0]["content"]
    assert "<pre>" not in content and "<b>" not in content
    assert "WINNER" in content


def test_dispatch_unknown_function_is_graceful():
    reg = make_registry()
    results = reg.dispatch([make_tool_call("no_such_tool")])
    assert "Unknown function" in results[0]["content"]


def test_dispatch_multiple_calls_preserve_ids_and_order():
    reg = make_registry()
    calls = [
        make_tool_call("roll_dice", call_id="a"),
        make_tool_call("roll_dice", call_id="b"),
    ]
    results = reg.dispatch(calls)
    assert [r["tool_call_id"] for r in results] == ["a", "b"]