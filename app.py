import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import gradio as gr
import traceback
import logging

from config import client, PUSHOVER_USER, PUSHOVER_TOKEN, APIFOOTBALL_API_KEY
from data_loader import load_documents
from rag import RAGIndex
from notifications import Notifier
from tools import ToolRegistry
from prompts import system_message
from twin import DigitalTwin
from fifa import FifaClient

logging.basicConfig(
    filename="gradio_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ---- Build once at startup ----
documents = load_documents()
rag_index = RAGIndex.from_documents(client, documents)
notifier = Notifier(user_key=PUSHOVER_USER, api_token=PUSHOVER_TOKEN)
fifa_client = FifaClient(api_key=APIFOOTBALL_API_KEY)
tool_registry = ToolRegistry(notifier=notifier,fifa_client=fifa_client)
twin = DigitalTwin(
    client=client,
    rag_index=rag_index,
    tools=tool_registry,
    system_message=system_message,
)
print(twin)  # sanity check: DigitalTwin(model='gpt-4.1-mini', RAGIndex(chunks=...), ToolRegistry(tools=[...]))
print(fifa_client)  # sanity check: FifaClient(league_id=1, season=2026, cached=[])


def submit_message(message, history):
    try:
        logging.info(f"message = {message}")
        # print("clicked", flush=True)
        history = history or []
        answer = twin.respond(message, history)
        history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": answer},
        ]
        return history, ""
    except Exception:
        logging.error(traceback.format_exc())
        raise


def add_fifa(history):
    history = history or []
    history.append({"role": "user", "content": "Show FIFA World Cup Today"})
    history.append({"role": "assistant", "content": fifa_client.today_cards()})
    return history

scroll_to_answer_js = """
() => {
  setTimeout(() => {
    const msgs = document.querySelectorAll('#chatbot .message');
    if (msgs.length) {
      msgs[msgs.length - 1].scrollIntoView({block: 'start', behavior: 'smooth'});
    }
  }, 150);
}
"""

# ---- UI ----

CUSTOM_CSS = """
    #prompt_row button { font-size: 12px; padding: 6px 10px; border-radius: 12px; }
    #fifa_btn { background: linear-gradient(135deg, #FFD700 0%, #0B3D91 100%); color: #fff; font-weight: 700; border: none; }
    .message pre { font-size: 11px; white-space: pre; overflow-x: auto; }
"""

with gr.Blocks() as demo:

    gr.Markdown("# Mamta's Digital Twin")
    gr.Markdown(
"""Hi! I'm Mamta's digital twin. She built me to share her work in AI engineering, graphics verification, and system-level design. Try one of the prompts below or ask me about my work.

You can also send her a note — anonymously or with your name. If you know her, she'd love your honest take on her strengths and weaknesses, and any critical feedback that helps her become the best version of herself. Thanks for visiting!"""
    )

    with gr.Row(elem_id="prompt_row"):
        background_btn = gr.Button("Background", variant="secondary", scale=0)
        ai_btn = gr.Button("AI Engineering", variant="secondary", scale=0)
        memory_btn = gr.Button("Memory BFM", variant="secondary", scale=0)
        leader_btn = gr.Button("Leadership", variant="secondary", scale=0)
        fifa_btn = gr.Button("🏆 FIFA World Cup", variant="secondary", scale=0, elem_id="fifa_btn")

    AVATAR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatar_m.png")
    chatbot = gr.Chatbot(
        avatar_images=(None, AVATAR_PATH),
        height=400,
        container=True,
        autoscroll=True,
        elem_id="chatbot"
    )

    msg = gr.Textbox(placeholder="Ask Mamta about her work ...")

    background_btn.click(
        lambda h: submit_message("What's your background?", h),
        inputs=[chatbot],
        outputs=[chatbot, msg]
    ).then(None, js=scroll_to_answer_js)
    ai_btn.click(
        lambda h: submit_message("Tell me about your AI Engineering experience", h),
        inputs=[chatbot],
        outputs=[chatbot, msg]
    )
    memory_btn.click(
        lambda h: submit_message("Explain your Memory BFM ownership and design work", h),
        inputs=[chatbot],
        outputs=[chatbot, msg]
    )
    leader_btn.click(
        lambda h: submit_message("Describe your leadership and mentoring experience", h),
        inputs=[chatbot],
        outputs=[chatbot, msg]
    )
    fifa_btn.click(
        fn=add_fifa,
        inputs=chatbot,
        outputs=chatbot
    )

    demo.css = """
    #prompt_row button {
        font-size: 12px;
        padding: 6px 10px;
        border-radius: 12px;
    }
    #fifa_btn {
        background: linear-gradient(135deg, #FFD700 0%, #0B3D91 100%);
        color: #ffffff;
        font-weight: 700;
        border: none;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
    }
    #fifa_btn:hover {
        filter: brightness(1.08);
    }
    .message pre {
        font-size: 11px;
        white-space: pre;
        overflow-x: auto;
        line-height: 1.35;
    }
    """

    msg.submit(
        submit_message,
        [msg, chatbot],
        [chatbot, msg]
    )

print("Launching...")
demo.launch(debug=True, show_error=True, quiet=False, css=CUSTOM_CSS)