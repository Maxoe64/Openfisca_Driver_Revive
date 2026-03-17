from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    from app.calculator import (
        DailyEntry, DailyWorkInput, WorkInput,
        calculate_daily_breakdown, calculate_overtime_preview,
    )
    from app.web_search import format_search_context, search_legislation, should_search
except ModuleNotFoundError:  # Allows `python app/server.py` from repository root
    from calculator import (
        DailyEntry, DailyWorkInput, WorkInput,
        calculate_daily_breakdown, calculate_overtime_preview,
    )
    from web_search import format_search_context, search_legislation, should_search

STATIC_DIR = Path(__file__).resolve().parent / "static"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

SYSTEM_PROMPT = (
    "You are a helpful Canadian labour standards assistant for Motor Vehicle "
    "Operators (MVOHWR). Ask concise clarifying questions and explain overtime "
    "clearly for non-experts."
)

_OLLAMA_PROCESS: subprocess.Popen | None = None


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def can_reach_ollama() -> bool:
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/version",
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=1.5):
            return True
    except urllib.error.URLError:
        return False


def start_ollama_service() -> None:
    global _OLLAMA_PROCESS
    if _OLLAMA_PROCESS and _OLLAMA_PROCESS.poll() is None:
        return

    try:
        _OLLAMA_PROCESS = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "Ollama executable not found. Install Ollama and ensure `ollama` is on PATH."
        ) from exc


def ensure_ollama_running() -> None:
    if can_reach_ollama():
        return

    start_ollama_service()

    for _ in range(10):
        time.sleep(0.4)
        if can_reach_ollama():
            return

    raise RuntimeError(
        "Could not reach Ollama on http://127.0.0.1:11434. "
        "The app tried to start it automatically; please run `ollama serve` manually."
    )


def request_ollama_chat(
    user_message: str,
    estimate_context: dict | None = None,
    model: str | None = None,
    history: list[dict] | None = None,
) -> tuple[str, str, bool]:
    """Send a chat request to Ollama with full conversation history.

    ``history`` is a list of prior ``{"role": "user"|"assistant", "content": ...}``
    dicts so the model can follow up on earlier exchanges.

    Returns ``(response_text, model_used, searched)`` where *searched* indicates
    whether web search results were injected into the context.
    """
    ensure_ollama_running()

    selected_model = (model or OLLAMA_MODEL).strip()

    # Inject estimate context into the system prompt so the model always has it,
    # even across multi-turn follow-ups where history is replayed verbatim.
    system_content = SYSTEM_PROMPT
    if estimate_context:
        context_json = json.dumps(estimate_context, ensure_ascii=False)
        system_content += (
            f"\n\nThe citizen's current overtime estimate data:\n{context_json}"
        )

    # Web search: fetch current legislation when the question warrants it.
    searched = False
    if should_search(user_message):
        results = search_legislation(user_message)
        search_ctx = format_search_context(results)
        if search_ctx:
            system_content += f"\n{search_ctx}"
            searched = True

    # Build the messages array: system prompt, then prior history, then new user msg.
    messages: list[dict] = [{"role": "system", "content": system_content}]

    # Replay prior conversation turns so the model has context.
    for turn in (history or []):
        role = turn.get("role", "")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": selected_model,
        "stream": False,
        "messages": messages,
    }

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not query Ollama chat API. If model is missing, run e.g. "
            "`ollama pull llama3.1` or `ollama pull gpt-oss:20b`."
        ) from exc

    data = json.loads(raw)
    return data.get("message", {}).get("content", "No response from model."), selected_model, searched


def fetch_ollama_models() -> list[str]:
    ensure_ollama_running()
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/tags",
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
    return [item.get("name", "") for item in data.get("models", []) if item.get("name")]


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parse_request_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length)
        return json.loads(raw_body.decode("utf-8"))

    def do_GET(self):
        if self.path == "/api/models":
            try:
                models = fetch_ollama_models()
                self._send_json({"models": models, "default": OLLAMA_MODEL})
            except RuntimeError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            except urllib.error.URLError:
                self._send_json({"error": "Could not fetch models from Ollama"}, HTTPStatus.BAD_GATEWAY)
            return

        super().do_GET()

    def do_POST(self):
        try:
            data = self._parse_request_json()
        except json.JSONDecodeError as exc:
            self._send_json({"error": f"Invalid payload: {exc}"}, HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/calculate":
            try:
                work = WorkInput(
                    weekly_hours_bus=float(data.get("weekly_hours_bus", 0)),
                    weekly_hours_city=float(data.get("weekly_hours_city", 0)),
                    weekly_hours_highway=float(data.get("weekly_hours_highway", 0)),
                    weekly_hours_other=float(data.get("weekly_hours_other", 0)),
                    hourly_rate=float(data.get("hourly_rate", 0)),
                )
            except ValueError as exc:
                self._send_json({"error": f"Invalid payload: {exc}"}, HTTPStatus.BAD_REQUEST)
                return

            self._send_json(calculate_overtime_preview(work))
            return

        if self.path == "/api/daily-breakdown":
            try:
                raw_days = data.get("days", [])
                days = [
                    DailyEntry(
                        day=str(d.get("day", "")),
                        hours_bus=float(d.get("hours_bus", 0)),
                        hours_city=float(d.get("hours_city", 0)),
                        hours_highway=float(d.get("hours_highway", 0)),
                        hours_other=float(d.get("hours_other", 0)),
                        is_holiday=bool(d.get("is_holiday", False)),
                    )
                    for d in raw_days
                ]
                daily_input = DailyWorkInput(
                    days=days,
                    hourly_rate=float(data.get("hourly_rate", 0)),
                )
            except (ValueError, TypeError, AttributeError) as exc:
                self._send_json({"error": f"Invalid payload: {exc}"}, HTTPStatus.BAD_REQUEST)
                return

            self._send_json(calculate_daily_breakdown(daily_input))
            return

        if self.path == "/api/chat":
            user_message = str(data.get("message", "")).strip()
            selected_model = str(data.get("model", "")).strip() or OLLAMA_MODEL
            chat_history = data.get("history") or []
            if not user_message:
                self._send_json({"error": "message is required"}, HTTPStatus.BAD_REQUEST)
                return
            try:
                response, used_model, searched = request_ollama_chat(
                    user_message,
                    data.get("estimate"),
                    selected_model,
                    history=chat_history,
                )
            except RuntimeError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
                return

            reply_payload: dict = {"reply": response, "model": used_model}
            if searched:
                reply_payload["searched"] = True
            self._send_json(reply_payload)
            return

        self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)


def build_server(host: str, port: int) -> ReusableThreadingHTTPServer:
    return ReusableThreadingHTTPServer((host, port), AppHandler)


def resolve_server(host: str, port: int, auto_port: bool = True) -> tuple[ReusableThreadingHTTPServer, int]:
    candidate_ports = [port]
    if auto_port:
        candidate_ports.extend([5050, 8000, 8080])

    last_error = None
    for candidate_port in candidate_ports:
        try:
            return build_server(host, candidate_port), candidate_port
        except OSError as exc:
            last_error = exc
            continue

    assert last_error is not None
    raise last_error


def run(host: str = "127.0.0.1", port: int = 5000, auto_port: bool = True):
    try:
        server, actual_port = resolve_server(host, port, auto_port = auto_port)
    except OSError as exc:
        raise RuntimeError(
            "Could not bind HTTP server. On Windows this may be permission, antivirus, "
            "or port reservation policy. Try `--host 127.0.0.1 --port 5050` and run "
            "your terminal as a normal user."
        ) from exc

    if actual_port != port:
        print(
            f"Port {port} unavailable; started on http://{host}:{actual_port} instead.",
            flush=True,
        )
    else:
        print(f"OpenFisca Canada UI running on http://{host}:{actual_port}", flush=True)

    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Run the OpenFisca Canada citizen UI")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "5000")))
    parser.add_argument(
        "--no-auto-port",
        action="store_true",
        help="Disable automatic fallback to alternate ports",
    )
    args = parser.parse_args()
    run(host=args.host, port=args.port, auto_port=not args.no_auto_port)


if __name__ == "__main__":
    main()
