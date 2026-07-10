import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import gradio as gr
import traceback
import logging

import config
from data_loader import load_documents
from rag import RAGIndex
from notifications import Notifier
from tools import ToolRegistry
from prompts import system_message, initial_message
from twin import DigitalTwin
from fifa import FifaClient

logging.basicConfig(
    filename="gradio_debug.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ---- Build once at startup ----
documents = load_documents()
rag_index = RAGIndex.from_documents(config.client, documents)
notifier = Notifier(user_key=config.PUSHOVER_USER, api_token=config.PUSHOVER_TOKEN)
fifa_client = FifaClient(api_key=config.APIFOOTBALL_API_KEY)
tool_registry = ToolRegistry(notifier=notifier, fifa_client=fifa_client)
twin = DigitalTwin(
    client=config.client,
    rag_index=rag_index,
    tools=tool_registry,
    system_message=system_message,
)
print(twin)         # sanity check: DigitalTwin(model='gpt-4.1-mini', RAGIndex(chunks=...), ...)
print(fifa_client)  # sanity check: FifaClient(league_id=1, season=2026, cached=[])


def submit_message(message, history):
    try:
        logging.info(f"message = {message}")
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


def send_direct(message, contact):
    if not message.strip():
        return "Please write a message first."
    notifier.send(
        f"Message from digital twin visitor: {message}\n"
        f"Optional contact: {contact or 'not provided'}"
    )
    return "✅ Sent! Mamta will see it soon."


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

open_send_accordion_js = """
() => {
  setTimeout(() => {
    const acc = document.querySelector('#send_accordion');
    if (acc) { acc.scrollIntoView({block: 'start', behavior: 'smooth'}); }
  }, 100);
}
"""

# ---- CSS (single source of truth, applied via gr.Blocks) ----

CUSTOM_CSS = """
#prompt_row button {
    font-size: 15px;
    padding: 6px 14px;
    border-radius: 17px;      /* pill look */
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
/* chat text: bigger for mobile readability */
#chatbot, #chatbot p, #chatbot li {
    font-size: 16px;
    line-height: 1.45;
}
/* safety net for any preformatted content: wrap, don't clip */
#chatbot pre, #chatbot code {
    white-space: pre-wrap;
    font-size: 13px;
    overflow-x: auto;
    line-height: 1.35;
}
/* Mobile optimizations */
@media (max-width: 768px) {
    #chatbot {
        height: 35vh !important;
    }
}
"""

# ---- UI ----

with gr.Blocks(css=CUSTOM_CSS) as demo:

    gr.Markdown("# Mamta's Digital Twin")

    with gr.Row(elem_id="prompt_row"):
        background_btn = gr.Button("Background", variant="secondary", size="sm", scale=0)
        ai_btn = gr.Button("AI Engineering", variant="secondary", size="sm", scale=0)
        kpi_btn = gr.Button("KPI", variant="secondary", size="sm", scale=0)
        fifa_btn = gr.Button("🏆 FIFA World Cup", variant="secondary", size="sm", scale=0, elem_id="fifa_btn")
        send_msg_btn = gr.Button("Send Message", variant="secondary", size="sm", scale=0)

    chatbot = gr.Chatbot(
        value=[{"role": "assistant", "content": initial_message}],
        label="Digital Twin",
        avatar_images=(None, None),
        height=400,
        container=True,
        autoscroll=False,
        elem_id="chatbot",
    )

    with gr.Row():
        msg = gr.Textbox(
            placeholder="Ask me anything...",
            show_label=False,
            submit_btn=True,   # send (arrow) button inside the textbox
            elem_id="msg-input",
        )

    with gr.Accordion("📨 Send Mamta a message", open=False, elem_id="send_accordion") as send_accordion:
        gr.Markdown("Anonymous or with your name — honest feedback welcome.")
        visitor_msg = gr.Textbox(placeholder="Your message...", show_label=False, lines=3)
        visitor_contact = gr.Textbox(placeholder="Name/contact (optional)", show_label=False)
        send_btn2 = gr.Button("Send", variant="primary", size="sm")
        send_status = gr.Markdown()

    # ---- events ----

    msg.submit(
        submit_message,
        [msg, chatbot],
        [chatbot, msg],
    ).then(None, js=scroll_to_answer_js)

    background_btn.click(
        lambda h: submit_message("What's your background?", h),
        inputs=[chatbot],
        outputs=[chatbot, msg],
    ).then(None, js=scroll_to_answer_js)

    ai_btn.click(
        lambda h: submit_message("Tell me about your AI Engineering experience", h),
        inputs=[chatbot],
        outputs=[chatbot, msg],
    ).then(None, js=scroll_to_answer_js)

    kpi_btn.click(
        lambda h: submit_message("Explain your KPI work", h),
        inputs=[chatbot],
        outputs=[chatbot, msg],x``
    ).then(None, js=scroll_to_answer_js)

    fifa_btn.click(
        fn=add_fifa,
        inputs=chatbot,
        outputs=chatbot,
    ).then(None, js=scroll_to_answer_js)

    # "Send Message" opens the dedicated form instead of injecting a chat bubble
    send_msg_btn.click(
        lambda: gr.Accordion(open=True),
        outputs=send_accordion,
    ).then(None, js=open_send_accordion_js)

    send_btn2.click(
        send_direct,
        inputs=[visitor_msg, visitor_contact],
        outputs=send_status,
    )

    send_btn2.click(
        lambda: ("", ""),
        outputs=[visitor_msg, visitor_contact],
    )


if __name__ == "__main__":
    print("Launching...")
    demo.launch(debug=True, show_error=True, quiet=False, ssr_mode=False)