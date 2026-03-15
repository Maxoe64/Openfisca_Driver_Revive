# OpenFisca Canada (MVO Hours of Work Rules)

This repository contains:

- the OpenFisca rules package (`openfisca_canada_mvohwr`),
- a citizen-facing overtime calculator UI (`app/`), and
- an Ollama-powered chat assistant endpoint for citizen Q&A.

## Features

- `GET /` interactive web UI for hours + pay estimate.
- `GET /start-here.html` citizen-facing page with use cases and step-by-step instructions.
- `POST /api/calculate` overtime estimate API.
- `POST /api/chat` local LLM chat endpoint (via Ollama API, with model selection).

## Simple local installation (full app)

### 1) Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed

### 2) Clone and install Python app

```bash
git clone <your-fork-or-repo-url>
cd Openfisca-Canada
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### 3) Pull at least one Ollama model

```bash
ollama pull llama3.1
# optional
ollama pull gpt-oss:20b
ollama pull mistral
```

The app now attempts to auto-start `ollama serve` on the standard local port `11434` if Ollama is installed.

> Optional: set a different model or endpoint using environment variables:
>
> ```bash
> export OLLAMA_MODEL=mistral
> export OLLAMA_URL=http://127.0.0.1:11434/api/chat
> ```

### 4) Run the app

Recommended (works from any folder after install):

```bash
mvohwr-ui --host 127.0.0.1 --port 5000
# if 5000 is blocked, app auto-falls back (e.g. 5050, 8000, 8080)
```

Alternative (run from repository root):

```bash
python -m app.server --host 127.0.0.1 --port 5000
```

Windows fallback if module path errors:

```bash
python app/server.py --host 127.0.0.1 --port 5000
```

Open: `http://localhost:5000`

## Example citizen questions for the chat UX

- “I drove 52 city hours this week. How many hours are overtime?”
- “If my hourly wage is $29 and I worked 64 highway hours, what should I expect in overtime pay?”
- “I split time between city and highway routes. Which standard hours should I compare against?”
- “What information should I gather before disputing unpaid overtime?”

## Run tests

```bash
python -m pytest tests_app
python -m compileall openfisca_canada_mvohwr app
```

## Docker

```bash
docker compose up --build
```

Open: `http://localhost:5000`

## Notes

- The calculator remains an "OpenFisca-ready preview" for citizen use and service prototyping.
- Weekly thresholds match repository defaults (`40/45/60` profiles).
- Chat responses depend on your local Ollama model and may vary.


## Citizen-facing page

Use `http://localhost:5000/start-here.html` as the front page for onboarding citizens.
It explains:

- intended audience,
- concrete citizen use cases,
- a step-by-step usage flow, and
- limitations (informational estimate, not legal advice).


## Troubleshooting

If you see: `ModuleNotFoundError: No module named 'app'`

- Make sure you ran `pip install -e .` in the repo first.
- Start with `mvohwr-ui` (preferred, after install).
- If running source directly, run from repo root with `python -m app.server` or `python app/server.py`.

If `http://localhost:5000` does not open:

- Start with `mvohwr-ui --host 127.0.0.1 --port 5000`; if 5000 is blocked the app auto-switches to `5050`, `8000`, or `8080`.
- For Ollama chat errors, ensure a model exists (`ollama list`) and pull one if needed (`ollama pull llama3.1`).
- Read terminal output and open the exact URL shown.
- To force a single port only (disable fallback), add `--no-auto-port`.
- On Docker, use `docker compose up --build` (container binds `0.0.0.0:5000`).
