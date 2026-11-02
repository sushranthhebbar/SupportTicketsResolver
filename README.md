# Support Tickets Resolver

A Python project for building and evaluating a support-ticket resolution system.

## Setup

Use Python 3.11 and create a virtual environment from the project root:

```cmd
py -3.11 -m venv .venv311
.venv311\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
```

If `py -3.11` reports that no Python installation is registered, use the full path to your Python 3.11 executable for the virtual-environment command instead, for example `"C:\Path\To\Python311\python.exe" -m venv .venv311`.

Edit `.env` and add your model-provider key. The example uses Groq's OpenAI-compatible endpoint and `qwen/qwen3.8-27b`; replace the placeholder with your Groq API key. Keep `.env` private; it is ignored by Git. To use OpenRouter instead, set `MODEL_API_KEY`, `MODEL_API_URL`, and `MODEL_NAME` to your OpenRouter key, chat-completions URL, and chosen model. Existing `OPENROUTER_API_KEY` / `OPENROUTER_API_URL` settings remain supported as fallback configuration.

## Run checks

Run the automated, offline tests:

```cmd
.venv311\Scripts\python.exe -m pytest tests/ -v
```

Run the optional live provider smoke check (uses the configured URL, key, and model):

```cmd
.venv311\Scripts\python.exe .\scripts\test_model_provider.py
```

Verify the local Chroma index, SQLite decision log, and Prometheus endpoint:

```cmd
python .\scripts\verify_setup_steps_4_6.py
```

Run a live 20-ticket classification/routing sample (requires the model provider settings
in `.env`) and inspect the per-ticket output plus SQLite decision log:

```cmd
python .\scripts\run_classification_sample.py
```

Run the diverse development urgency sample (30 live model calls) and review the
classifier's urgency evidence, ambiguity flags, routes, and offline-only reference
labels:

```cmd
python .\scripts\run_urgency_spectrum_sample.py
```

Run the full evaluation pipeline on the supplied validation set (live model calls;
the hidden 120-ticket evaluation set is not distributed):

```cmd
.venv311\Scripts\python.exe .\scripts\run_evaluation.py --input evaluation\data\validation_tickets.json --output evaluation\results\validation_2026-11-02.jsonl --processor src.pipeline:process_ticket --system-version 0.1
.venv311\Scripts\python.exe .\scripts\verify_evaluation_artifacts.py --input evaluation\data\validation_tickets.json --results evaluation\results\validation_2026-11-02.jsonl --report evaluation\results\validation_2026-11-02.report.json
```

The verifier checks that every input ticket appears exactly once and in order, no
ticket failed, report counts reconcile, and evaluation-only labels/history did not
reach processor results. Run automated offline tests in the project virtual
environment with `.venv311\Scripts\python.exe -m pytest tests/ -v`.

Raw model confidence is not treated as calibrated. High urgency and security
incidents escalate; other tickets stay in review until calibrated confidence scores
are supplied to the routing pipeline.

## Agent review API

Set a private, random `AGENT_API_TOKEN` in `.env`, then start the API from the
project root:

```cmd
.venv311\Scripts\python.exe -m uvicorn src.app:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000/review](http://127.0.0.1:8000/review) for the agent
review page. The authenticated `/api/review/drafts` endpoints list and retrieve
grounded drafts, and let an agent edit, approve, or reject them. The review page also
shows ticket decision history and lets an agent record outcomes, feedback, or an
escalation decision. Edits and approvals are rechecked against retrieved source IDs and reply
guardrails. Approval records the AI assistance disclosure and source IDs. The API
does not send customer messages; it only records an agent-reviewed result for a
future delivery integration. `GET /api/review/outcomes/summary` reports descriptive
outcomes by customer tier and language-fluency group without attributing causality
to AI. API clients pass `Authorization: Bearer <AGENT_API_TOKEN>`. The `.env.example`
token value is a placeholder and must be replaced before starting the API. This
prototype uses one shared bearer token; the reviewer ID is supplied by the agent,
so configure per-agent identity and retention policy before a multi-agent deployment.

Open [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard) for the
authenticated operations dashboard. It summarizes persisted decision volume,
routes, intent/urgency, channels, guardrail failures, outcome coverage, and observed
outcomes by customer tier and language fluency. Outcome summaries are descriptive
and do not establish AI causality. Latency is marked unavailable until per-ticket
latency is persisted by the pipeline. Dashboard data uses the same bearer token.

The GitHub Actions workflow at `.github/workflows/ci.yml` installs the pinned dependencies and runs the offline tests on pushes and pull requests. It does not need an API key.

## Repository layout

- `src/` contains application modules: the review API (`app.py`), review workflow store (`review_store.py`), and outcome store/report (`outcome_store.py`); ticket normalization (`tickets.py`), classification (`classification.py`), routing (`routing.py`), escalation summaries (`escalation.py`), grounded reply drafting (`answering.py`), reply guardrails (`guardrails.py`), pipeline/log integration (`pipeline.py`), evaluation (`evaluation.py`), retrieval (`retrieve.py`), decision logging (`logging_store.py`), and Prometheus metrics (`monitoring.py`).
- `tests/` contains automated tests that do not require network access or model credentials.
- `scripts/` contains manual setup and provider smoke checks, plus the evaluation runner (`run_evaluation.py`).
- `data/documentation.json` is the retrieval corpus.
- `evaluation/data/` contains the supplied development, validation, and reference-response datasets. Their labels are preserved as supplied, including conflicting urgency annotations; see `docs/architecture.md` for the human-review fallback. `evaluation/results/` is for dated evaluation outputs.
- `prompts/` separates runtime prompts from evaluation prompts.
- `docs/` contains architecture notes and the supplied project reference materials.
- `storage/` is generated at runtime and is excluded from Git.

The FastAPI agent review API is available for local use. Generated replies remain
internal drafts until an agent approves them, and this project does not send replies
directly to customers.
