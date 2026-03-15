import json
from unittest.mock import patch

from app.server import request_ollama_chat


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps({"message": {"content": "Test reply"}}).encode("utf-8")


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
