import json
from unittest.mock import patch, call

from app.server import request_ollama_chat


class FakeResponse:
    def __init__(self, content="Test reply"):
        self._content = content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps({"message": {"content": self._content}}).encode("utf-8")


def test_request_ollama_chat_returns_message_with_selected_model():
    with patch("app.server.ensure_ollama_running", return_value=None), patch(
        "urllib.request.urlopen", return_value=FakeResponse()
    ):
        reply, model = request_ollama_chat(
            "How is overtime computed?", {"overtime_hours": 5}, model="gpt-oss:20b"
        )
    assert reply == "Test reply"
    assert model == "gpt-oss:20b"


def test_request_ollama_chat_autostarts_when_needed():
    with patch("app.server.can_reach_ollama", side_effect=[False, True]), patch(
        "app.server.start_ollama_service", return_value=None
    ) as start_mock:
        with patch("urllib.request.urlopen", return_value=FakeResponse()):
            request_ollama_chat("question", {}, model="llama3.1")
    start_mock.assert_called_once()


def test_request_ollama_chat_sends_history():
    """Conversation history should be included in the messages sent to Ollama."""
    captured_payloads = []

    def capture_urlopen(req, **kwargs):
        captured_payloads.append(json.loads(req.data.decode("utf-8")))
        return FakeResponse("follow-up reply")

    history = [
        {"role": "user", "content": "What is my overtime?"},
        {"role": "assistant", "content": "You worked 5h of overtime."},
    ]

    with patch("app.server.ensure_ollama_running", return_value=None), patch(
        "urllib.request.urlopen", side_effect=capture_urlopen
    ):
        reply, model = request_ollama_chat(
            "Can you explain that?",
            {"overtime_hours": 5},
            model="llama3.1",
            history=history,
        )

    assert reply == "follow-up reply"

    # Check the payload sent to Ollama
    sent_messages = captured_payloads[0]["messages"]

    # Should be: system, user (history), assistant (history), user (new)
    assert len(sent_messages) == 4
    assert sent_messages[0]["role"] == "system"
    assert sent_messages[1]["role"] == "user"
    assert sent_messages[1]["content"] == "What is my overtime?"
    assert sent_messages[2]["role"] == "assistant"
    assert sent_messages[2]["content"] == "You worked 5h of overtime."
    assert sent_messages[3]["role"] == "user"
    assert sent_messages[3]["content"] == "Can you explain that?"


def test_request_ollama_chat_first_message_includes_estimate_context():
    """First message (no history) should include the estimate context."""
    captured_payloads = []

    def capture_urlopen(req, **kwargs):
        captured_payloads.append(json.loads(req.data.decode("utf-8")))
        return FakeResponse()

    with patch("app.server.ensure_ollama_running", return_value=None), patch(
        "urllib.request.urlopen", side_effect=capture_urlopen
    ):
        request_ollama_chat(
            "How much OT?",
            {"overtime_hours": 5},
            model="llama3.1",
            history=[],
        )

    sent_messages = captured_payloads[0]["messages"]
    # system + user (with context)
    assert len(sent_messages) == 2
    assert "overtime_hours" in sent_messages[1]["content"]
    assert "Citizen question" in sent_messages[1]["content"]


def test_request_ollama_chat_followup_omits_estimate_context():
    """Follow-up messages (with history) should NOT re-inject estimate context."""
    captured_payloads = []

    def capture_urlopen(req, **kwargs):
        captured_payloads.append(json.loads(req.data.decode("utf-8")))
        return FakeResponse()

    history = [
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "First answer"},
    ]

    with patch("app.server.ensure_ollama_running", return_value=None), patch(
        "urllib.request.urlopen", side_effect=capture_urlopen
    ):
        request_ollama_chat(
            "Follow-up question",
            {"overtime_hours": 5},
            model="llama3.1",
            history=history,
        )

    sent_messages = captured_payloads[0]["messages"]
    last_msg = sent_messages[-1]
    # Follow-up should be the raw message, not wrapped with "Citizen question:"
    assert last_msg["content"] == "Follow-up question"
    assert "Citizen question" not in last_msg["content"]
