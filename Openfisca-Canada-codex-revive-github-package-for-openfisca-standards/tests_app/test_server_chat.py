import json
import urllib.error
from unittest.mock import patch, call

from app.server import (
    request_ollama_chat,
    fetch_legislation_context,
    _HTMLTextExtractor,
    _legislation_cache,
)


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

    sent_messages = captured_payloads[0]["messages"]

    # Should be: system (with estimate), user (history), assistant (history), user (new)
    assert len(sent_messages) == 4
    assert sent_messages[0]["role"] == "system"
    assert "overtime_hours" in sent_messages[0]["content"]
    assert sent_messages[1]["role"] == "user"
    assert sent_messages[1]["content"] == "What is my overtime?"
    assert sent_messages[2]["role"] == "assistant"
    assert sent_messages[2]["content"] == "You worked 5h of overtime."
    assert sent_messages[3]["role"] == "user"
    assert sent_messages[3]["content"] == "Can you explain that?"


def test_estimate_context_in_system_prompt():
    """Estimate context should be injected into the system prompt, not the user message."""
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
        )

    sent_messages = captured_payloads[0]["messages"]
    # Estimate data lives in the system prompt
    assert "overtime_hours" in sent_messages[0]["content"]
    # User message is sent as-is, no wrapping
    assert sent_messages[1]["content"] == "How much OT?"


def test_estimate_context_persists_across_followups():
    """Estimate context should be present in system prompt on every turn, not just the first."""
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
    # System prompt still has the estimate context
    assert "overtime_hours" in sent_messages[0]["content"]
    # User messages are raw (no "Citizen question:" wrapping)
    assert sent_messages[-1]["content"] == "Follow-up question"
    assert sent_messages[1]["content"] == "First question"


def test_no_estimate_context_when_none():
    """When no estimate context is provided, the system prompt is unchanged."""
    captured_payloads = []

    def capture_urlopen(req, **kwargs):
        captured_payloads.append(json.loads(req.data.decode("utf-8")))
        return FakeResponse()

    with patch("app.server.ensure_ollama_running", return_value=None), patch(
        "urllib.request.urlopen", side_effect=capture_urlopen
    ):
        request_ollama_chat("Hello", model="llama3.1")

    sent_messages = captured_payloads[0]["messages"]
    # No estimate data appended
    assert "overtime estimate data" not in sent_messages[0]["content"]


# ---------------------------------------------------------------------------
# Legislation web-search tests
# ---------------------------------------------------------------------------

def test_html_text_extractor():
    """HTMLTextExtractor should strip tags and skip script/style."""
    html = "<html><head><title>T</title></head><body><script>var x=1;</script><p>Hello <b>world</b></p><style>.x{}</style><p>Second</p></body></html>"
    parser = _HTMLTextExtractor()
    parser.feed(html)
    text = parser.get_text()
    assert "Hello world" in text
    assert "Second" in text
    assert "var x=1" not in text
    assert ".x{}" not in text


class FakeHTTPResponse:
    """Simulates urllib response for URL fetches."""

    def __init__(self, body: str):
        self._body = body.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


def test_fetch_legislation_context_returns_text():
    """fetch_legislation_context should return concatenated text from legislation URLs."""
    _legislation_cache.clear()

    fake_html = "<html><body><p>Section 3: Standard hours are 60 per week.</p></body></html>"

    with patch("urllib.request.urlopen", return_value=FakeHTTPResponse(fake_html)):
        result = fetch_legislation_context()

    assert "Standard hours are 60 per week" in result
    assert "Current MVOHWR legislation" in result


def test_fetch_legislation_context_uses_cache():
    """Subsequent calls should use the cache, not re-fetch."""
    _legislation_cache.clear()

    fake_html = "<html><body><p>Cached content</p></body></html>"

    with patch("urllib.request.urlopen", return_value=FakeHTTPResponse(fake_html)) as mock_open:
        fetch_legislation_context()
        call_count_after_first = mock_open.call_count

        # Second call should use cache
        result = fetch_legislation_context()
        assert mock_open.call_count == call_count_after_first

    assert "Cached content" in result


def test_fetch_legislation_context_handles_errors():
    """When URLs fail and there's no cache, they should be silently skipped."""
    _legislation_cache.clear()

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("fail")):
        result = fetch_legislation_context()

    assert result == ""


def test_search_legislation_injects_into_system_prompt():
    """When search_legislation=True, legislation text should appear in the system prompt."""
    captured_payloads = []

    def capture_urlopen(req, **kwargs):
        captured_payloads.append(json.loads(req.data.decode("utf-8")))
        return FakeResponse()

    fake_legislation = "=== Current MVOHWR legislation ===\nSection 3: 60 hours."

    with patch("app.server.ensure_ollama_running", return_value=None), \
         patch("urllib.request.urlopen", side_effect=capture_urlopen), \
         patch("app.server.fetch_legislation_context", return_value=fake_legislation):
        request_ollama_chat(
            "What are the standard hours?",
            model="llama3.1",
            search_legislation=True,
        )

    system_msg = captured_payloads[0]["messages"][0]["content"]
    assert "Section 3: 60 hours" in system_msg
    assert "Cite specific sections" in system_msg


def test_search_legislation_false_does_not_inject():
    """When search_legislation=False, no legislation text should appear."""
    captured_payloads = []

    def capture_urlopen(req, **kwargs):
        captured_payloads.append(json.loads(req.data.decode("utf-8")))
        return FakeResponse()

    with patch("app.server.ensure_ollama_running", return_value=None), \
         patch("urllib.request.urlopen", side_effect=capture_urlopen):
        request_ollama_chat(
            "What are the standard hours?",
            model="llama3.1",
            search_legislation=False,
        )

    system_msg = captured_payloads[0]["messages"][0]["content"]
    assert "MVOHWR legislation" not in system_msg
