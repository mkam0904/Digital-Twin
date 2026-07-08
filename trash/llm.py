# src/llm.py
# model client wrapper (OpenAI/Anthropic/etc.)

from config import client
from tools import tools_l

# Call the large language model
def call_llm(msgs):
    return client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=msgs,
        tools=tools_l,
    )
 