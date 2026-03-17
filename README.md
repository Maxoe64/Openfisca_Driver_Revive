# OpenFisca Canada (MVO Hours of Work Rules)

This repository contains:

- the OpenFisca rules package (`openfisca_canada_mvohwr`),
- a citizen-facing overtime calculator UI (`app/`), and
- an Ollama-powered chat assistant endpoint for citizen Q&A.

## Features

### Calculator
- **Quick Estimate** (`GET /`) — enter weekly totals by work type and get an instant overtime + pay estimate.
- **Daily Breakdown** — enter hours for each day of the week in a 7-day grid. The tool calculates *both* daily and weekly overtime, then uses whichever is higher (better for the worker), exactly as the MVOHWR requires.
- **Mixed Employment Majority Logic** — for drivers who split time between city, highway, bus, and other work, the calculator applies the MVOHWR majority-hours rule to pick the correct overtime threshold.

### For Drivers
- **Multi-week History** — save weekly estimates to browser localStorage. Build evidence over time (up to 52 weeks).
- **Print / Save PDF** — generate a clean printable summary to take to your employer or the Labour Program.
- **Know Your Rights** — step-by-step guidance on what to do if you think you are owed overtime, with direct links to file a complaint with the Federal Labour Program.
- **Bilingual EN/FR** — toggle between English and French at any time. Required for Canadian federal tools.

### API Endpoints
- `GET /` interactive web UI with tabs for quick estimate, daily breakdown, history, and rights.
- `GET /start-here.html` citizen-facing page with use cases and step-by-step instructions.
- `POST /api/calculate` weekly overtime estimate API.
- `POST /api/daily-breakdown` daily + weekly overtime breakdown API.
- `POST /api/chat` local LLM chat endpoint (via Ollama API, with model selection).
- `GET /api/models` list available Ollama models.

## Simple local installation (full app)

### 1) Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed (optional, for chat feature)

### 2) Clone and install Python app

```bash
git clone <your-fork-or-repo-url>
cd Openfisca-Canada-codex-revive-github-package-for-openfisca-standards
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### 3) Pull at least one Ollama model (optional)

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

Open: `http://localhost:5000`

## Example citizen questions for the chat UX

- "I drove 52 city hours this week. How many hours are overtime?"
- "If my hourly wage is $29 and I worked 64 highway hours, what should I expect in overtime pay?"
- "I split time between city and highway routes. Which standard hours should I compare against?"
- "What information should I gather before disputing unpaid overtime?"

## Run tests

```bash
# App + calculator tests (23 tests)
python -m pytest tests_app -v

# OpenFisca rules tests
openfisca test --country-package openfisca_canada_mvohwr openfisca_canada_mvohwr/tests

# Compile check
python -m compileall openfisca_canada_mvohwr app
```

## Docker

```bash
docker compose up --build
```

Open: `http://localhost:5000`

## MVOHWR Overtime Thresholds

| Worker Type | Daily Standard | Weekly Standard |
|---|---|---|
| Bus operator (CLC) | 8 hours | 40 hours |
| City MVO (CMVO) | 9 hours | 45 hours |
| Highway MVO (HMVO) | No daily OT | 60 hours |
| Other (CLC) | 8 hours | 40 hours |

**Mixed employment:** The regulation uses a majority-hours rule. The work type with the most hours determines which weekly threshold applies.

**Daily vs weekly OT:** The MVOHWR requires calculating both daily and weekly overtime, then using whichever is higher (better for the worker).

## Notes

- The calculator remains an "OpenFisca-ready preview" for citizen use and service prototyping.
- Weekly thresholds match repository parameter defaults.
- Chat responses depend on your local Ollama model and may vary.

## Citizen-facing page

Use `http://localhost:5000/start-here.html` as the front page for onboarding citizens.

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
