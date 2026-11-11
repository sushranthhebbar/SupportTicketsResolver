"""Load and normalize support tickets from the supplied datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_CHANNELS = frozenset({"email", "chat", "docs_comment", "forum"})
CUSTOMER_CONTEXT_FIELDS = (
    "customer_id",
    "customer_name",
    "customer_tier",
    "customer_region",
    "language_fluency",
)


@dataclass(frozen=True)
class NormalizedTicket:
    """Ticket fields shared across all supported intake channels."""

    ticket_id: str
    channel: str
    subject: str
    body: str
    received_at: str
    customer_context: Mapping[str, str | None]

    def to_dict(self) -> dict[str, Any]:
        """Return a plain-data representation for downstream components."""
        return {
            "ticket_id": self.ticket_id,
            "channel": self.channel,
            "subject": self.subject,
            "body": self.body,
            "received_at": self.received_at,
            "customer_context": dict(self.customer_context),
        }


@dataclass(frozen=True)
class TicketRecord:
    """A normalized ticket plus labels/outcomes reserved for evaluation."""

    ticket: NormalizedTicket
    labels: Mapping[str, Any]
    history: Mapping[str, Any]


def _required_text(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field!r} must be a non-empty string")
    return value.strip()


def _optional_text(record: Mapping[str, Any], field: str) -> str:
    value = record.get(field, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{field!r} must be a string when provided")
    return value


def _normalize_timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("'received_at' must be a non-empty ISO 8601 timestamp")
    timestamp_text = value.strip()
    if timestamp_text.endswith("Z"):
        timestamp_text = f"{timestamp_text[:-1]}+00:00"
    try:
        timestamp = datetime.fromisoformat(timestamp_text)
    except ValueError as exc:
        raise ValueError("'received_at' must be a valid ISO 8601 timestamp") from exc
    if timestamp.tzinfo is None:
        raise ValueError("'received_at' must include a timezone")
    return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_ticket(record: Mapping[str, Any]) -> NormalizedTicket:
    """Validate and normalize one ticket without evaluation-only annotations.

    ``labels`` and ``history`` from the supplied datasets are intentionally not
    included in the returned ticket. They belong to offline evaluation and must
    not leak into a runtime classification or answer-generation input.
    """
    if not isinstance(record, Mapping):
        raise ValueError("Each ticket record must be a JSON object")

    ticket_id = _required_text(record, "ticket_id")
    channel = _required_text(record, "channel").lower()
    if channel not in SUPPORTED_CHANNELS:
        allowed = ", ".join(sorted(SUPPORTED_CHANNELS))
        raise ValueError(f"Unsupported channel {channel!r}; expected one of: {allowed}")

    subject = _optional_text(record, "subject")
    body = _optional_text(record, "body")
    if not subject.strip() and not body.strip():
        raise ValueError("A ticket must contain a subject or body")

    raw_customer_context: dict[str, str | None] = {}
    for field in CUSTOMER_CONTEXT_FIELDS:
        value = record.get(field)
        if value is None:
            raw_customer_context[field] = None
        elif isinstance(value, str):
            raw_customer_context[field] = value.strip() or None
        else:
            raise ValueError(f"{field!r} must be a string when provided")

    return NormalizedTicket(
        ticket_id=ticket_id,
        channel=channel,
        subject=subject,
        body=body,
        received_at=_normalize_timestamp(record.get("received_at")),
        customer_context=raw_customer_context,
    )


def load_ticket_records(
    path: str | Path, rejected: list[dict[str, Any]] | None = None
) -> list[TicketRecord]:
    """Load a JSON ticket list, separating runtime fields from annotations.

    An invalid ticket raises ValueError unless ``rejected`` is given; then it is skipped
    and described in that list, so one malformed record does not stop a whole run.
    """
    source_path = Path(path)
    if not source_path.is_absolute():
        source_path = PROJECT_ROOT / source_path

    with source_path.open(encoding="utf-8") as file:
        records: Any = json.load(file)
    if not isinstance(records, list):
        raise ValueError("Ticket dataset must contain a top-level JSON list")

    loaded: list[TicketRecord] = []
    for index, raw_record in enumerate(records):
        try:
            ticket = normalize_ticket(raw_record)
        except ValueError as exc:
            if rejected is None:
                raise ValueError(f"Invalid ticket at dataset index {index}: {exc}") from exc
            rejected.append(
                {
                    "index": index,
                    "ticket_id": raw_record.get("ticket_id") if isinstance(raw_record, Mapping) else None,
                    "reason": str(exc),
                }
            )
            continue

        labels = raw_record.get("labels", {})
        history = raw_record.get("history", {})
        if not isinstance(labels, Mapping):
            raise ValueError(f"Ticket {ticket.ticket_id!r} has invalid labels")
        if not isinstance(history, Mapping):
            raise ValueError(f"Ticket {ticket.ticket_id!r} has invalid history")

        loaded.append(
            TicketRecord(
                ticket=ticket,
                labels=dict(labels),
                history=dict(history),
            )
        )
    return loaded
