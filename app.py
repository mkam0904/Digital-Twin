import gradio as gr
from llm import respond_ai
from fifa import fifa_cards, fifa_full_schedule_text
import traceback
import logging

def submit_message(message, history):
    # raise ValueError("FORCED ERROR TEST")
    try:
        logging.info(f"message = {message}")
        print("clicked", flush=True)

        if "fifa" in message.lower():
            return history + [(message, fifa_today_cards())], ""
        else: 
            history = history or []
            answer = respond_ai(message, history)
            history = history + [(message, answer)]
            return history, ""

    except Exception as e:
        logging.error(traceback.format_exc())
        raise


####
# Launch Gradio 
####
with gr.Blocks() as demo:

    gr.Markdown("# Mamta's Digital Twin")
    gr.Markdown("""
    Hi ! I'm Mamta's digital twin. She built me to share her work in AI engineering, graphics verification, and system-level design.
    Try one of the prompts above or ask me about my work.
    """)

    # AUTO-SUBMIT BUTTONS
    with gr.Row(elem_id="prompt_row"):
        background_btn = gr.Button("Background", variant="secondary", scale=0)
        ai_btn = gr.Button("AI Engineering", variant="secondary", scale=0)
        memory_btn = gr.Button("Memory BFM", variant="secondary", scale=0)
        leader_btn = gr.Button("Leadership", variant="secondary", scale=0)
        fifa_btn = gr.Button("FIFAWorldCupToday", variant="secondary", scale=0)
        # fifa_output = gr.HTML()

    chatbot = gr.Chatbot(
        avatar_images=(None, "mamta.png"),
        height=400,
        container=True
    )
    
    def add_fifa(history):
        history = history or []
        history.append({
            "role": "user",
            "content": "Show FIFA World Cup Today"
        })
        history.append({
            "role": "assistant",
            "content": fifa_today_cards()
        })
        return history

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

    # --- USER TYPING ---
    msg.submit(
        submit_message,
        [msg, chatbot], # inputs 
        [chatbot, msg]  # outputs 
    )
print("Launching...")
demo.launch(debug=True, show_error=True,quiet=False) # inbrowser=True) # share=True
