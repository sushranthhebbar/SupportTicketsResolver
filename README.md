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

Edit `.env` and add your OpenRouter key. Keep `.env` private; it is ignored by Git. The example file contains placeholders only.

## Run checks

Run the automated, offline tests:

```cmd
python -m pytest tests/ -v
```

Run the optional live OpenRouter smoke check (uses the model configured in `.env`):

```cmd
python .\scripts\test_openrouter.py
```

Verify the local Chroma index, SQLite decision log, and Prometheus endpoint:

```cmd
python .\scripts\verify_setup_steps_4_6.py
```

Run a live 20-ticket classification/routing sample (requires the OpenRouter settings
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

Raw model confidence is not treated as calibrated. High urgency and security
incidents escalate; other tickets stay in review until calibrated confidence scores
are supplied to the routing pipeline.

The GitHub Actions workflow at `.github/workflows/ci.yml` installs the pinned dependencies and runs the offline tests on pushes and pull requests. It does not need an API key.

## Repository layout

- `src/` contains application modules: ticket normalization (`tickets.py`), classification (`classification.py`), routing (`routing.py`), grounded reply drafting (`answering.py`), reply guardrails (`guardrails.py`), pipeline/log integration (`pipeline.py`), evaluation (`evaluation.py`), retrieval (`retrieve.py`), decision logging (`logging_store.py`), and Prometheus metrics (`monitoring.py`).
- `tests/` contains automated tests that do not require network access or model credentials.
- `scripts/` contains manual setup and provider smoke checks, plus the evaluation runner (`run_evaluation.py`).
- `data/documentation.json` is the retrieval corpus.
- `evaluation/data/` contains the supplied development, validation, and reference-response datasets. Their labels are preserved as supplied, including conflicting urgency annotations; see `docs/architecture.md` for the human-review fallback. `evaluation/results/` is for dated evaluation outputs.
- `prompts/` separates runtime prompts from evaluation prompts.
- `docs/` contains architecture notes and the supplied project reference materials.
- `storage/` is generated at runtime and is excluded from Git.

The FastAPI application and agent review interface remain planned components. Generated replies are internal drafts and are never sent directly to customers.
