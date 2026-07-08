"""Tool registry: OpenAI function-calling specs + dispatch."""

import re
import json
import random
from dataclasses import dataclass, field

from notifications import Notifier

__all__ = ["ToolRegistry"]


@dataclass
class ToolRegistry:
    """Owns the set of tools available to the LLM and dispatches tool calls.

    Attributes:
        notifier: Notifier instance backing the send_notification tool.
        specs: OpenAI tool specs, built automatically in __post_init__.
    """

    notifier: Notifier
    fifa_client: "FifaClient" = None
    specs: list[dict] = field(init=False)

    def __post_init__(self) -> None:
        self.specs = [
            {"type": "function", "function": self._dice_spec()},
            {"type": "function", "function": self.notifier.tool_spec},
        ]
        self.specs.append({"type": "function", "function": {
            "name": "get_world_cup_schedule",
            "description": (
                "Get live FIFA World Cup 2026 scores, today's matches, and "
                "the remaining schedule through the Final. Use for any "
                "question about current World Cup games, scores, or schedule."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        }})

    @staticmethod
    def _dice_spec() -> dict:
        return {
            "name": "roll_dice",
            "description": (
                "Simulates rolling a single six-sided dice. Use this when the "
                "user wants to roll a dice for games, decisions, or random "
                "number generation."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

    @staticmethod
    def roll_dice() -> int:
        """Roll a single six-sided die."""
        return random.randint(1, 6)

    def dispatch(self, tool_calls) -> list[dict]:
        """Execute each requested tool call and format results for the LLM.

        Args:
            tool_calls: The tool_calls list from an OpenAI chat completion message.

        Returns:
            A list of {"role": "tool", "tool_call_id", "content"} messages.
        """
        results = []
        for call in tool_calls:
            name = call.function.name
            if name == "send_notification":
                args = json.loads(call.function.arguments)
                self.notifier.send(args["message"])
                content = f"Notification sent: {args['message']}"
            elif name == "roll_dice":
                content = f"roll_dice_result: {self.roll_dice()}"
            elif name == "get_world_cup_schedule":
                raw = self.fifa_client.today_cards()
                content = re.sub(r"</?(pre|b)>", "", raw)  # plain text for the LLM
            else:
                content = f"Unknown function: {name}"
            results.append({"role": "tool", "tool_call_id": call.id, "content": content})
        return results

    def __repr__(self) -> str:
        return f"ToolRegistry(tools={[s['function']['name'] for s in self.specs]})"