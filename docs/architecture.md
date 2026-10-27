# Architecture

## Current components

- `src/retrieve.py` splits documentation articles into passages, builds or loads a persistent Chroma index, and returns source identifiers with retrieved passages.
- `src/logging_store.py` writes auditable decisions to SQLite.
- `src/monitoring.py` exposes Prometheus counters and latency metrics.
- `scripts/verify_setup_steps_4_6.py` verifies those three setup components locally.

## Data flow

The retrieval corpus is `data/documentation.json`. The source datasets for development and evaluation live under `evaluation/data/`. Runtime artifacts, including the vector index and SQLite database, are stored under `storage/` and are not committed.

## Planned components

Ticket ingestion, classification, routing, response generation, guardrails, and the FastAPI application will be added as those stages are implemented. The evaluation harness should accept input and output paths rather than hardcoding a dataset filename.
