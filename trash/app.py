import sys, os
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
tool_registry = ToolRegistry(notifier=notifier)
twin = DigitalTwin(
    client=client,
    rag_index=rag_index,
    tools=tool_registry,
    system_message=system_message,
)
print(twin)  # sanity check: DigitalTwin(model='gpt-4.1-mini', RAGIndex(chunks=...), ToolRegistry(tools=[...]))

fifa_client = FifaClient(api_key=APIFOOTBALL_API_KEY)
print(fifa_client)  # sanity check: FifaClient(league_id=1, season=2026, cached_dates=[])

def submit_message(message, history):
    try:
        logging.info(f"message = {message}")
        print("clicked", flush=True)
        history = history or []
        if "fifa" in message.lower():
            answer = fifa_client.today_cards()
        else:
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


# ---- UI ----
with gr.Blocks() as demo:

    gr.Markdown("# Mamta's Digital Twin")
    gr.Markdown("""
    Hi! I'm Mamta's digital twin. She built me to share her work in AI engineering,
    graphics verification, and system-level design.
    Try one of the prompts above or ask me about my work.
    """)

    with gr.Row(elem_id="prompt_row"):
        background_btn = gr.Button("Background", variant="secondary", scale=0)
        ai_btn = gr.Button("AI Engineering", variant="secondary", scale=0)
        memory_btn = gr.Button("Memory BFM", variant="secondary", scale=0)
        leader_btn = gr.Button("Leadership", variant="secondary", scale=0)
        fifa_btn = gr.Button("FIFAWorldCupToday", variant="secondary", scale=0)

    chatbot = gr.Chatbot(
        avatar_images=(None, "mamta.png"),
        height=400,
        container=True,
        autoscroll=False
    )

    msg = gr.Textbox(placeholder="Ask Mamta about her work ...")

    background_btn.click(
        lambda h: submit_message("What's your background?", h),
        inputs=[chatbot],
        outputs=[chatbot, msg]
    )
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
    """

    msg.submit(
        submit_message,
        [msg, chatbot],
        [chatbot, msg]
    )

print("Launching...")
demo.launch(debug=True, show_error=True, quiet=False)