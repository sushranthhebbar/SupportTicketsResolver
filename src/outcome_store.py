"""Store observed outcomes and report descriptive assisted-ticket metrics."""

from __future__ import annotations

import json
import sqlite3
import statistics
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime, timezone
from typing import Any

from src.logging_store import SCHEMA as DECISIONS_SCHEMA
from src.logging_store import connect, log_decision


OUTCOME_SCHEMA = """
CREATE TABLE IF NOT EXISTS ticket_outcomes (
    ticket_id TEXT PRIMARY KEY,
    first_contact_resolution INTEGER,
    escalated INTEGER,
    repeat_contact INTEGER,
    resolution_time_minutes REAL,
    csat_rating REAL,
    customer_tier TEXT,
    language_fluency TEXT,
    feedback_category TEXT,
    agent_feedback TEXT,
    reviewer_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""

class OutcomeNotFound(LookupError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_optional(value: Any, field: str, max_length: int = 120) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text")
    cleaned = value.strip()
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise ValueError(f"{field} must be at most {max_length} characters")
    return cleaned


def record_ticket_outcome(
    ticket_id: str,
    *,
    reviewer_id: str,
    first_contact_resolution: bool | None = None,
    escalated: bool | None = None,
    repeat_contact: bool | None = None,
    resolution_time_minutes: float | None = None,
    csat_rating: float | None = None,
    customer_tier: str | None = None,
    language_fluency: str | None = None,
    feedback_category: str | None = None,
    agent_feedback: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Upsert measured outcomes for an assisted ticket and audit the submission."""
    reviewer = _clean_optional(reviewer_id, "reviewer_id")
    if reviewer is None:
        raise ValueError("reviewer_id is required")
    if not any(value is not None for value in (
        first_contact_resolution, escalated, repeat_contact,
        resolution_time_minutes, csat_rating, feedback_category, agent_feedback,
    )):
        raise ValueError("At least one outcome or feedback field is required")
    if resolution_time_minutes is not None and resolution_time_minutes < 0:
        raise ValueError("resolution_time_minutes cannot be negative")
    if csat_rating is not None and not 1 <= csat_rating <= 5:
        raise ValueError("csat_rating must be between 1 and 5")

    tier = _clean_optional(customer_tier, "customer_tier")
    fluency = _clean_optional(language_fluency, "language_fluency")
    category = _clean_optional(feedback_category, "feedback_category")
    feedback = _clean_optional(agent_feedback, "agent_feedback", max_length=2000)
    now = _now()
    values = {
        "ticket_id": ticket_id,
        "first_contact_resolution": first_contact_resolution,
        "escalated": escalated,
        "repeat_contact": repeat_contact,
        "resolution_time_minutes": resolution_time_minutes,
        "csat_rating": csat_rating,
        "customer_tier": tier,
        "language_fluency": fluency,
        "feedback_category": category,
        "agent_feedback": feedback,
        "reviewer_id": reviewer,
    }
    with closing(connect(database_url)) as connection:
        connection.execute(DECISIONS_SCHEMA)
        connection.execute(OUTCOME_SCHEMA)
        assisted = connection.execute(
            "SELECT 1 FROM decisions WHERE ticket_id=? LIMIT 1", (ticket_id,)
        ).fetchone()
        if assisted is None:
            raise OutcomeNotFound("Ticket has no recorded assistance decision")
        existing = connection.execute(
            "SELECT * FROM ticket_outcomes WHERE ticket_id=?", (ticket_id,)
        ).fetchone()
        created_at = existing["created_at"] if existing else now
        if existing:
            for field in (
                "first_contact_resolution", "escalated", "repeat_contact",
                "resolution_time_minutes", "csat_rating", "customer_tier",
                "language_fluency", "feedback_category", "agent_feedback",
            ):
                if values[field] is None:
                    values[field] = existing[field]
        connection.execute(
            """INSERT INTO ticket_outcomes (
                 ticket_id,first_contact_resolution,escalated,repeat_contact,
                 resolution_time_minutes,csat_rating,customer_tier,language_fluency,
                 feedback_category,agent_feedback,reviewer_id,created_at,updated_at
               ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(ticket_id) DO UPDATE SET
                 first_contact_resolution=excluded.first_contact_resolution,
                 escalated=excluded.escalated,repeat_contact=excluded.repeat_contact,
                 resolution_time_minutes=excluded.resolution_time_minutes,
                 csat_rating=excluded.csat_rating,customer_tier=excluded.customer_tier,
                 language_fluency=excluded.language_fluency,
                 feedback_category=excluded.feedback_category,agent_feedback=excluded.agent_feedback,
                 reviewer_id=excluded.reviewer_id,updated_at=excluded.updated_at""",
            (
                ticket_id,
                int(values["first_contact_resolution"]) if values["first_contact_resolution"] is not None else None,
                int(values["escalated"]) if values["escalated"] is not None else None,
                int(values["repeat_contact"]) if values["repeat_contact"] is not None else None,
                values["resolution_time_minutes"],
                values["csat_rating"],
                values["customer_tier"],
                values["language_fluency"],
                values["feedback_category"],
                values["agent_feedback"],
                reviewer,
                created_at,
                now,
            ),
        )
        connection.commit()

    log_decision(
        {
            "ticket_id": ticket_id,
            "stage": "ticket_outcome",
            "prediction_value": json.dumps(values, ensure_ascii=False),
            "action_taken": "outcome_recorded",
            "reason": "Agent-recorded observed outcomes and feedback; no causal attribution is made.",
            "requirement_ids": ["FR-08"],
        },
        database_url,
    )
    return get_ticket_outcome(ticket_id, database_url)


def get_ticket_outcome(
    ticket_id: str, database_url: str | None = None
) -> dict[str, Any] | None:
    with closing(connect(database_url)) as connection:
        connection.execute(OUTCOME_SCHEMA)
        row = connection.execute(
            "SELECT * FROM ticket_outcomes WHERE ticket_id=?", (ticket_id,)
        ).fetchone()
    if row is None:
        return None
    result = dict(row)
    for field in ("first_contact_resolution", "escalated", "repeat_contact"):
        if result[field] is not None:
            result[field] = bool(result[field])
    return result


def _group_metrics(rows: list[sqlite3.Row]) -> dict[str, Any]:
    outcome_fields = (
        "first_contact_resolution", "escalated", "repeat_contact",
        "resolution_time_minutes", "csat_rating",
    )

    def rate(field: str) -> float | None:
        values = [bool(row[field]) for row in rows if row[field] is not None]
        return statistics.mean(values) if values else None

    def mean(field: str) -> float | None:
        values = [float(row[field]) for row in rows if row[field] is not None]
        return statistics.mean(values) if values else None

    categories = Counter(row["feedback_category"] for row in rows if row["feedback_category"])
    return {
        "tickets_with_records": len(rows),
        "tickets_with_outcomes": sum(any(row[field] is not None for field in outcome_fields) for row in rows),
        "first_contact_resolution_observations": sum(row["first_contact_resolution"] is not None for row in rows),
        "escalation_observations": sum(row["escalated"] is not None for row in rows),
        "repeat_contact_observations": sum(row["repeat_contact"] is not None for row in rows),
        "resolution_time_observations": sum(row["resolution_time_minutes"] is not None for row in rows),
        "csat_observations": sum(row["csat_rating"] is not None for row in rows),
        "tickets_with_feedback": sum(bool(row["feedback_category"] or row["agent_feedback"]) for row in rows),
        "first_contact_resolution_rate": rate("first_contact_resolution"),
        "escalation_rate": rate("escalated"),
        "repeat_contact_rate": rate("repeat_contact"),
        "mean_resolution_time_minutes": mean("resolution_time_minutes"),
        "mean_csat_rating": mean("csat_rating"),
        "feedback_categories": dict(sorted(categories.items())),
    }


def summarize_ticket_outcomes(database_url: str | None = None) -> dict[str, Any]:
    with closing(connect(database_url)) as connection:
        connection.execute(OUTCOME_SCHEMA)
        rows = connection.execute(
            "SELECT * FROM ticket_outcomes ORDER BY ticket_id"
        ).fetchall()

    def group_by(field: str) -> dict[str, Any]:
        groups: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for row in rows:
            key = row[field] or "unknown"
            groups[str(key)].append(row)
        return {
            key: _group_metrics(group_rows)
            for key, group_rows in sorted(groups.items())
        }

    return {
        "tickets_with_records": len(rows),
        "tickets_with_recorded_outcomes": sum(
            any(row[field] is not None for field in (
                "first_contact_resolution", "escalated", "repeat_contact",
                "resolution_time_minutes", "csat_rating",
            ))
            for row in rows
        ),
        "by_customer_tier": group_by("customer_tier"),
        "by_language_fluency": group_by("language_fluency"),
        "interpretation": (
            "Descriptive observed outcomes and agent feedback for assisted tickets. "
            "These summaries do not establish that AI assistance caused an outcome."
        ),
    }
