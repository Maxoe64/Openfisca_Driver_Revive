import io
import json
from http import HTTPStatus
from unittest.mock import patch

from app.server import AppHandler, ReusableThreadingHTTPServer


class FakeWfile(io.BytesIO):
    pass


def _make_request(path, payload):
    """Simulate a POST request to the handler and return (status, parsed_json)."""
    body = json.dumps(payload).encode("utf-8")
    rfile = io.BytesIO(body)

    responses = []

    class CapturingHandler(AppHandler):
        def __init__(self):
            self.path = path
            self.headers = {"Content-Length": str(len(body))}
            self.rfile = rfile
            self.wfile = FakeWfile()
            self._sent_status = None

        def send_response(self, code, message=None):
            self._sent_status = code

        def send_header(self, keyword, value):
            pass

        def end_headers(self):
            pass

        def log_message(self, format, *args):
            pass

    handler = CapturingHandler()
    handler.do_POST()
    handler.wfile.seek(0)
    response_body = json.loads(handler.wfile.read().decode("utf-8"))
    return handler._sent_status, response_body


def test_daily_breakdown_endpoint():
    days = [
        {"day": "Mon", "hours_bus": 0, "hours_city": 10, "hours_highway": 0, "hours_other": 0, "is_holiday": False},
        {"day": "Tue", "hours_bus": 0, "hours_city": 10, "hours_highway": 0, "hours_other": 0, "is_holiday": False},
        {"day": "Wed", "hours_bus": 0, "hours_city": 10, "hours_highway": 0, "hours_other": 0, "is_holiday": False},
        {"day": "Thu", "hours_bus": 0, "hours_city": 10, "hours_highway": 0, "hours_other": 0, "is_holiday": False},
        {"day": "Fri", "hours_bus": 0, "hours_city": 10, "hours_highway": 0, "hours_other": 0, "is_holiday": False},
        {"day": "Sat", "hours_bus": 0, "hours_city": 0, "hours_highway": 0, "hours_other": 0, "is_holiday": False},
        {"day": "Sun", "hours_bus": 0, "hours_city": 0, "hours_highway": 0, "hours_other": 0, "is_holiday": False},
    ]
    status, data = _make_request("/api/daily-breakdown", {"days": days, "hourly_rate": 20})

    assert status == HTTPStatus.OK
    assert data["mode"] == "daily-breakdown"
    assert data["weekly_total_hours"] == 50.0
    assert data["best_overtime_hours"] > 0
    assert len(data["days"]) == 7


def test_daily_breakdown_bad_payload():
    status, data = _make_request("/api/daily-breakdown", {"days": "not-a-list"})
    assert status == HTTPStatus.BAD_REQUEST
    assert "error" in data
