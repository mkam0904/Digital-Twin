import pytest
import gradio as gr
from src.prompts import initial_message

def test_chatbot_initialization():
    """Test that chatbot initializes without format errors"""
    try:
        chatbot = gr.Chatbot(
            value=[{"role": "assistant", "content": initial_message}],
            label="Digital Twin"
        )
        assert chatbot is not None
    except gr.exceptions.Error as e:
        pytest.fail(f"Chatbot initialization failed: {e}")

def test_initial_message_format():
    """Validate initial message has required keys"""
    msg = {"role": "assistant", "content": initial_message}
    assert "role" in msg, "Missing 'role' key"
    assert "content" in msg, "Missing 'content' key"
    assert msg["role"] in ["assistant", "user"], "Invalid role"
    assert len(msg["content"]) > 0, "Empty message content"