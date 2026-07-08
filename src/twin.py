"""DigitalTwin: owns the LLM client, RAG index, and tool registry for a chat session."""

from dataclasses import dataclass

from openai import OpenAI

from rag import RAGIndex
from tools import ToolRegistry

__all__ = ["DigitalTwin"]


@dataclass
class DigitalTwin:
    """Owns the LLM client, RAG index, and tool registry for one chat session.

    Attributes:
        client: OpenAI client used for chat completions.
        rag_index: RAGIndex used to retrieve bio-doc context per turn.
        tools: ToolRegistry available to the LLM.
        system_message: Base system prompt defining the twin's persona.
        model: Chat completion model name.
        max_tool_calls: Max consecutive tool-call rounds per turn (loop guard).
    """

    client: OpenAI
    rag_index: RAGIndex
    tools: ToolRegistry
    system_message: str
    model: str = "gpt-4.1-mini"
    max_tool_calls: int = 3

    def respond(self, message: str, history: list[dict]) -> str:
        """Answer one user turn, retrieving context and handling tool calls.

        Args:
            message: The user's latest message.
            history: Prior turns, as OpenAI chat-message dicts.

        Returns:
            The assistant's text reply.
        """

        recent = " ".join(
            m["content"] for m in history[-2:]
            if isinstance(m.get("content"), str)
        )
        retrieval_query = f"{recent} {message}".strip()
        context = self.rag_index.retrieve_context(retrieval_query)
        system_enhanced_msg = f"{self.system_message}\n\nContext:\n{context}"

        msgs = [{"role": "system", "content": system_enhanced_msg}] + history + [
            {"role": "user", "content": message}
        ]

        response = self._call_llm(msgs)
        assistant_msg = response.choices[0].message

        count = 0
        while assistant_msg.tool_calls:
            if count >= self.max_tool_calls:
                break
            count += 1
            msgs.append(assistant_msg)
            msgs.extend(self.tools.dispatch(assistant_msg.tool_calls))
            response = self._call_llm(msgs)
            assistant_msg = response.choices[0].message

        return assistant_msg.content or "No text response returned."

    def _call_llm(self, msgs: list[dict]):
        """Call the chat completion endpoint with this twin's model and tools."""
        return self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            tools=self.tools.specs,
        )

    def __repr__(self) -> str:
        return f"DigitalTwin(model={self.model!r}, {self.rag_index!r}, {self.tools!r})"