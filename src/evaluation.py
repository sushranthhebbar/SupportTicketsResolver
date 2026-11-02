"""Run a ticket processor over a dataset and write evaluation artifacts."""

from __future__ import annotations

import json
import math
import statistics
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from src.tickets import PROJECT_ROOT, NormalizedTicket, TicketRecord, load_ticket_records


TicketProcessor = Callable[[NormalizedTicket], Mapping[str, Any]]


def _rate(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _classification_metrics(
    rows: list[dict[str, Any]], expected_field: str, predicted_field: str
) -> dict[str, Any]:
    scored_rows = [row for row in rows if row["result"] is not None]
    expected = [row["expected"].get(expected_field) for row in scored_rows]
    predicted = [
        row["result"].get(predicted_field) for row in scored_rows
    ]
    classes = sorted(
        {value for value in expected + predicted if isinstance(value, str)}
    )
    per_class: dict[str, Any] = {}
    precisions: list[float] = []
    recalls: list[float] = []
    for label in classes:
        true_positive = sum(
            actual == label and guess == label
            for actual, guess in zip(expected, predicted)
        )
        false_positive = sum(
            actual != label and guess == label
            for actual, guess in zip(expected, predicted)
        )
        false_negative = sum(
            actual == label and guess != label
            for actual, guess in zip(expected, predicted)
        )
        precision = _rate(true_positive, true_positive + false_positive)
        recall = _rate(true_positive, true_positive + false_negative)
        if precision is None and any(actual == label for actual in expected):
            precision = 0.0
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "support": sum(actual == label for actual in expected),
        }
        if precision is not None:
            precisions.append(precision)
        if recall is not None:
            recalls.append(recall)
    return {
        "per_class": per_class,
        "macro_precision": statistics.mean(precisions) if precisions else None,
        "macro_recall": statistics.mean(recalls) if recalls else None,
        "scored_tickets": len(scored_rows),
        "excluded_processing_errors": len(rows) - len(scored_rows),
    }


def _source_ids(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    found: set[str] = set()
    for item in value:
        if isinstance(item, str) and item:
            found.add(item)
        elif isinstance(item, Mapping):
            source_id = item.get("doc_id") or item.get("source_id")
            if isinstance(source_id, str) and source_id:
                found.add(source_id)
    return found


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _historical_baseline(records: list[TicketRecord]) -> dict[str, Any]:
    histories = [record.history for record in records]

    def boolean_rate(field: str) -> float | None:
        values = [history[field] for history in histories if isinstance(history.get(field), bool)]
        if not values:
            return None
        return sum(values) / len(values)

    def numeric_mean(field: str) -> float | None:
        values = [
            float(history[field])
            for history in histories
            if isinstance(history.get(field), (int, float))
            and not isinstance(history.get(field), bool)
        ]
        return statistics.mean(values) if values else None

    return {
        "first_contact_resolution_rate": boolean_rate("first_contact_resolution"),
        "escalation_rate": boolean_rate("escalated"),
        "repeat_contact_rate": boolean_rate("repeat_contact"),
        "mean_resolution_time_minutes": numeric_mean("resolution_time_minutes"),
        "mean_satisfaction_rating": numeric_mean("csat_rating"),
        "first_response_time": None,
        "first_response_time_note": (
            "The supplied ticket records do not contain first-response timestamps."
        ),
    }


def _urgency_label_conflicts(records: list[TicketRecord]) -> dict[str, Any]:
    """Report, but do not rewrite, conflicting urgency labels on repeated ticket text."""
    groups: dict[str, list[TicketRecord]] = {}
    for record in records:
        text = f"{record.ticket.subject} {record.ticket.body}"
        key = " ".join(text.casefold().split())
        if key:
            groups.setdefault(key, []).append(record)
    conflicts = []
    affected_ids: set[str] = set()
    for group in groups.values():
        if len(group) < 2:
            continue
        labels = {record.labels.get("urgency") for record in group}
        if len(labels) > 1:
            ticket_ids = [record.ticket.ticket_id for record in group]
            affected_ids.update(ticket_ids)
            conflicts.append(
                {
                    "ticket_ids": ticket_ids,
                    "urgency_labels": sorted(
                        str(label) for label in labels if isinstance(label, str)
                    ),
                }
            )
    return {
        "conflicting_duplicate_text_groups": len(conflicts),
        "tickets_in_conflicting_groups": len(affected_ids),
        "groups": conflicts,
        "note": (
            "Ground-truth label conflicts are reported without changing labels. "
            "Interpret urgency metrics with this data-quality signal; ambiguous "
            "runtime cases should be sent for human review."
        ),
    }


def build_metrics(
    records: list[TicketRecord], rows: list[dict[str, Any]], system_version: str
) -> dict[str, Any]:
    action_counts: Counter[str] = Counter()
    latency_values: list[float] = []
    retrieval_eligible = retrieval_hits = 0
    citation_eligible = citation_matches = 0
    unsafe_auto_responses = private_data_detections = 0

    for record, row in zip(records, rows):
        result = row["result"] or {}
        action = result.get("action") or result.get("route")
        if isinstance(action, str):
            action_counts[action] += 1
        latency = result.get("latency_seconds", row.get("latency_seconds"))
        if isinstance(latency, (int, float)):
            latency_values.append(float(latency))

        expected_docs = set(record.labels.get("expected_doc_ids", []))
        retrieved = _source_ids(
            result.get("retrieved_sources", result.get("sources"))
        )
        if row["result"] is not None and record.labels.get("answerable_from_docs") is True and expected_docs:
            retrieval_eligible += 1
            retrieval_hits += bool(expected_docs & retrieved)

        cited = _source_ids(result.get("citations"))
        if row["result"] is not None and cited and expected_docs:
            citation_eligible += len(cited)
            citation_matches += len(cited & expected_docs)

        if row["result"] is not None and record.labels.get("must_not_auto_respond") is True and action == "auto_respond":
            unsafe_auto_responses += 1
        detections = result.get("private_data_detections", [])
        if isinstance(detections, list):
            private_data_detections += len(detections)
        elif detections is True:
            private_data_detections += 1

    successful = sum(row["result"] is not None for row in rows)
    failed = len(rows) - successful
    expected_routes = [record.labels.get("expected_route") for record in records]
    route_matches = sum(
        expected == ((row["result"] or {}).get("route") or (row["result"] or {}).get("action"))
        for expected, row in zip(expected_routes, rows)
        if isinstance(expected, str) and row["result"] is not None
    )
    route_count = sum(
        isinstance(expected, str) and row["result"] is not None
        for expected, row in zip(expected_routes, rows)
    )

    return {
        "run_info": {
            "run_at_utc": datetime.now(timezone.utc).isoformat(),
            "system_version": system_version,
            "tickets_in_input": len(records),
            "tickets_processed": successful,
            "processing_errors": failed,
        },
        "volume": {
            "actions": dict(sorted(action_counts.items())),
            "blocked_by_guardrails": action_counts.get("block", 0),
        },
        "business": {
            "historical_baseline": _historical_baseline(records),
            "system_first_contact_resolution": None,
            "system_satisfaction": None,
            "note": "System business outcomes require observed customer or agent outcomes; they are not inferred from historical labels.",
        },
        "technical": {
            "intent_classification": _classification_metrics(rows, "intent", "intent"),
            "urgency_classification": _classification_metrics(rows, "urgency", "urgency"),
            "routing_accuracy": _rate(route_matches, route_count),
            "routing_scored_tickets": route_count,
            "routing_excluded_processing_errors": len(rows) - successful,
            "retrieval_hit_rate_on_answerable_tickets": _rate(
                retrieval_hits, retrieval_eligible
            ),
            "retrieval_hit_count": retrieval_hits,
            "retrieval_eligible_count": retrieval_eligible,
            "citation_document_match_rate": _rate(
                citation_matches, citation_eligible
            ),
            "citation_document_match_note": "Document-ID match is a proxy; sentence-level citation support requires human review.",
            "latency_seconds": {
                "median": statistics.median(latency_values) if latency_values else None,
                "p95": _percentile(latency_values, 0.95),
                "measured_tickets": len(latency_values),
            },
        },
        "governance": {
            "must_not_auto_respond_violations": unsafe_auto_responses,
            "private_data_detections_reported_by_processor": private_data_detections,
            "urgency_label_conflicts": _urgency_label_conflicts(records),
            "hallucination_rate": None,
            "hallucination_rate_note": "Requires human review of generated responses.",
            "confidence_calibration": None,
            "confidence_calibration_note": "Requires a calibrated confidence output and a defined calibration method.",
            "decision_log_reconciliation": None,
            "decision_log_note": "Requires connection to the persistent decision log.",
        },
    }


def _resolve_path(path: str | Path) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved


def run_evaluation(
    input_path: str | Path,
    output_path: str | Path,
    processor: TicketProcessor,
    *,
    report_path: str | Path | None = None,
    system_version: str = "unspecified",
) -> dict[str, Any]:
    """Process each ticket once and write per-ticket JSONL and a JSON report.

    The processor receives only ``NormalizedTicket``. Dataset labels and
    historical outcomes are retained by the harness for scoring and baselines.
    Per-ticket exceptions are recorded so one bad record does not stop the run.
    """
    records = load_ticket_records(input_path)
    rows: list[dict[str, Any]] = []
    for record in records:
        started = time.perf_counter()
        result: dict[str, Any] | None = None
        error: dict[str, str] | None = None
        try:
            processed = processor(record.ticket)
            if not isinstance(processed, Mapping):
                raise TypeError("Ticket processor must return a mapping")
            result = dict(processed)
        except Exception as exc:  # Keep the unattended run moving per A11.
            error = {"type": type(exc).__name__, "message": str(exc)}
        elapsed = time.perf_counter() - started
        if result is not None:
            result.setdefault("latency_seconds", elapsed)

        rows.append(
            {
                "ticket_id": record.ticket.ticket_id,
                "result": result,
                "error": error,
                "latency_seconds": elapsed,
                "expected": {
                    key: record.labels.get(key)
                    for key in (
                        "intent",
                        "urgency",
                        "expected_route",
                        "answerable_from_docs",
                        "expected_doc_ids",
                        "must_not_auto_respond",
                    )
                },
            }
        )

    output_file = _resolve_path(output_path)
    report_file = _resolve_path(report_path) if report_path else output_file.with_suffix(".report.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8", newline="\n") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = build_metrics(records, rows, system_version)
    report["run_info"].update(
        {
            "input_path": str(_resolve_path(input_path)),
            "results_path": str(output_file),
            "report_path": str(report_file),
        }
    )
    with report_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write("\n")
    return report
