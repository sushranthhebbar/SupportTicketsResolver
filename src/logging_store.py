"""Persistent SQLite log for automated support decisions."""

from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")
SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
    decision_id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    ticket_id TEXT NOT NULL,
    stage TEXT NOT NULL,
    input_summary TEXT,
    model_name TEXT,
    model_version TEXT,
    prediction_value TEXT,
    prediction_confidence REAL,
    alternatives_json TEXT NOT NULL DEFAULT '[]',
    sources_used_json TEXT NOT NULL DEFAULT '[]',
    threshold_applied REAL,
    action_taken TEXT NOT NULL,
    reason TEXT NOT NULL,
    guardrail_results_json TEXT NOT NULL DEFAULT '{}',
    prompt_version TEXT,
    requirement_ids_json TEXT NOT NULL DEFAULT '[]'
)
"""


def database_path(database_url: str | None = None) -> Path:
    """Resolve the SQLite URL used by the setup guide."""
    url = database_url or os.getenv(
        "DATABASE_URL", "sqlite:///./storage/decisions.db"
    )
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        raise ValueError("This setup supports SQLite URLs beginning with sqlite:///")
    raw_path = url[len(prefix) :]
    path = Path(raw_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path


def connect(database_url: str | None = None) -> sqlite3.Connection:
    path = database_path(database_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_url: str | None = None) -> Path:
    """Create the decision table if it does not already exist."""
    path = database_path(database_url)
    with closing(connect(database_url)) as connection:
        connection.execute(SCHEMA)
        connection.commit()
    return path


def _json(value: Any, default: Any) -> str:
    return json.dumps(default if value is None else value, ensure_ascii=False)


def log_decision(
    decision: Mapping[str, Any], database_url: str | None = None
) -> str:
    """Persist one decision and return its generated or supplied ID."""
    for field in ("ticket_id", "stage", "action_taken", "reason"):
        if not decision.get(field):
            raise ValueError(f"Decision requires a non-empty {field!r}")

    decision_id = str(decision.get("decision_id") or uuid.uuid4())
    timestamp = decision.get("timestamp") or datetime.now(timezone.utc).isoformat()
    values = (
        decision_id,
        timestamp,
        str(decision["ticket_id"]),
        str(decision["stage"]),
        decision.get("input_summary"),
        decision.get("model_name"),
        decision.get("model_version"),
        decision.get("prediction_value"),
        decision.get("prediction_confidence"),
        _json(decision.get("alternatives"), []),
        _json(decision.get("sources_used"), []),
        decision.get("threshold_applied"),
        str(decision["action_taken"]),
        str(decision["reason"]),
        _json(decision.get("guardrail_results"), {}),
        decision.get("prompt_version"),
        _json(decision.get("requirement_ids"), []),
    )
    with closing(connect(database_url)) as connection:
        connection.execute(SCHEMA)
        connection.execute(
            """INSERT INTO decisions (
                decision_id, timestamp, ticket_id, stage, input_summary,
                model_name, model_version, prediction_value,
                prediction_confidence, alternatives_json, sources_used_json,
                threshold_applied, action_taken, reason, guardrail_results_json,
                prompt_version, requirement_ids_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            values,
        )
        connection.commit()
    return decision_id


def count_decisions(database_url: str | None = None) -> int:
    with closing(connect(database_url)) as connection:
        connection.execute(SCHEMA)
        count = int(connection.execute("SELECT COUNT(*) FROM decisions").fetchone()[0])
        connection.commit()
        return count
