"""Build descriptive dashboard metrics from persisted decisions and outcomes."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from contextlib import closing
from typing import Any

from src.logging_store import SCHEMA as DECISIONS_SCHEMA
from src.logging_store import connect
from src.outcome_store import summarize_ticket_outcomes


def _object(value: Any) -> dict[str, Any]:
    if not isinstance(value, str):
        return {}
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def build_dashboard_summary(database_url: str | None = None) -> dict[str, Any]:
    """Summarize logged system activity without inferring unobserved outcomes."""
    with closing(connect(database_url)) as connection:
        connection.execute(DECISIONS_SCHEMA)
        rows = connection.execute(
            """SELECT timestamp,ticket_id,stage,prediction_value,action_taken,
                      guardrail_results_json
               FROM decisions ORDER BY timestamp, decision_id"""
        ).fetchall()

    per_ticket: dict[str, dict[str, Any]] = {}
    daily_volume: Counter[str] = Counter()
    route_counts: Counter[str] = Counter()
    intent_counts: Counter[str] = Counter()
    urgency_counts: Counter[str] = Counter()
    channels: Counter[str] = Counter()
    guardrail_failures: Counter[str] = Counter()
    latest_timestamp: str | None = None

    for row in rows:
        ticket_id = row["ticket_id"]
        stage = row["stage"]
        item = per_ticket.setdefault(ticket_id, {})
        latest_timestamp = row["timestamp"]
        if stage == "classification":
            prediction = _object(row["prediction_value"])
            item["classification"] = prediction
            date = str(row["timestamp"])[:10]
            daily_volume[date] += 1
            if prediction.get("intent"):
                intent_counts[str(prediction["intent"])] += 1
            if prediction.get("urgency"):
                urgency_counts[str(prediction["urgency"])] += 1
            if prediction.get("channel"):
                channels[str(prediction["channel"])] += 1
        elif stage == "routing":
            item["route"] = row["action_taken"]
            route_counts[str(row["action_taken"])] += 1
        elif stage == "answer_drafting":
            guardrails = _object(row["guardrail_results_json"])
            for name, result in guardrails.items():
                if isinstance(result, dict) and result.get("passed") is False:
                    guardrail_failures[str(name)] += 1

    outcomes = summarize_ticket_outcomes(database_url)
    assisted_tickets = len(per_ticket)
    with_outcomes = int(outcomes["tickets_with_recorded_outcomes"])
    return {
        "generated_from": "persisted_decision_log_and_agent_recorded_outcomes",
        "assisted_tickets": assisted_tickets,
        "last_decision_at": latest_timestamp,
        "daily_ticket_volume": dict(sorted(daily_volume.items())),
        "routes": dict(sorted(route_counts.items())),
        "intents": dict(sorted(intent_counts.items())),
        "urgencies": dict(sorted(urgency_counts.items())),
        "channels": dict(sorted(channels.items())),
        "guardrail_failures": dict(sorted(guardrail_failures.items())),
        "outcome_coverage": {
            "tickets_with_observed_outcomes": with_outcomes,
            "assisted_tickets": assisted_tickets,
            "coverage_rate": with_outcomes / assisted_tickets if assisted_tickets else None,
        },
        "outcomes": outcomes,
        "latency": {
            "available": False,
            "reason": "Per-ticket latency is not yet persisted by the pipeline.",
        },
        "interpretation": (
            "Counts describe recorded system decisions. Outcome summaries are based on "
            "agent-recorded observations and do not establish that AI assistance caused them."
        ),
    }
