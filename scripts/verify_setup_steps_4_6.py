"""Smoke-check the vector store, decision database, and Prometheus endpoint."""

from __future__ import annotations

import json
import socket
import sys
import tempfile
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.logging_store import count_decisions, initialize_database, log_decision
from src.retrieve import (
    DEFAULT_DOCUMENTATION_PATH,
    get_vector_store,
    search_documentation,
)
from src.monitoring import record_ticket, start_metrics_server


def check_vector_store() -> None:
    with DEFAULT_DOCUMENTATION_PATH.open(encoding="utf-8") as file:
        articles = json.load(file)
    expected_doc_id = articles[0]["doc_id"]
    query = articles[0]["title"]

    store = get_vector_store()
    matches = search_documentation(query, k=3, store=store)
    if not matches:
        raise RuntimeError("Chroma returned no passages for the documentation query")
    if expected_doc_id not in {match["doc_id"] for match in matches}:
        raise RuntimeError(
            f"Expected source {expected_doc_id} was not among the top results: "
            f"{[match['doc_id'] for match in matches]}"
        )
    print(
        f"Step 4 OK: indexed {store._collection.count()} passages from "
        f"{len(articles)} articles; query returned source {expected_doc_id}."
    )


def check_decision_database() -> None:
    path = initialize_database()
    storage_directory = PROJECT_ROOT / "storage"
    storage_directory.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="tickets-resolver-db-check-", dir=storage_directory
    ) as folder:
        test_db = Path(folder) / "decision_check.db"
        test_url = f"sqlite:///{test_db.as_posix()}"
        decision_id = log_decision(
            {
                "ticket_id": "SETUP-CHECK",
                "stage": "validation",
                "prediction_value": "setup_check",
                "prediction_confidence": 1.0,
                "sources_used": [{"doc_id": "DOC-TEST", "score": 0.0}],
                "action_taken": "block",
                "reason": "Temporary setup verification record",
                "guardrail_results": {"setup_check": "pass"},
                "requirement_ids": ["SETUP-CHECK"],
            },
            database_url=test_url,
        )
        if count_decisions(test_url) != 1 or not decision_id:
            raise RuntimeError("SQLite decision insert/count verification failed")
    print(f"Step 5 OK: SQLite database initialized at {path}; insert/read check passed.")


def check_prometheus() -> None:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    start_metrics_server(port)
    record_ticket("setup_check", "verified")
    response = requests.get(f"http://127.0.0.1:{port}/metrics", timeout=5)
    response.raise_for_status()
    expected_sample = (
        'tickets_processed_total{channel="setup_check",outcome="verified"} 1.0'
    )
    if expected_sample not in response.text:
        raise RuntimeError("Prometheus endpoint did not expose the recorded ticket metric")
    print(f"Step 6 OK: Prometheus /metrics responded on localhost:{port}.")


if __name__ == "__main__":
    check_vector_store()
    check_decision_database()
    check_prometheus()
    print("Setup steps 4–6 verified.")
