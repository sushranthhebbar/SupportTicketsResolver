import json

import pytest

from src.tickets import (
    SUPPORTED_CHANNELS,
    load_ticket_records,
    normalize_ticket,
)


def _ticket(**overrides):
    ticket = {
        "ticket_id": "TEST-0001",
        "channel": "chat",
        "subject": "",
        "body": "Help with a deployment.",
        "received_at": "2026-03-01T12:00:00Z",
        "customer_id": "CUST-1",
        "customer_name": "Example Customer",
        "customer_tier": "standard",
        "customer_region": "north_america",
        "language_fluency": "fluent",
        "labels": {"intent": "deployment_failure"},
        "history": {"escalated": False},
    }
    ticket.update(overrides)
    return ticket


def test_normalize_ticket_accepts_all_supported_channels():
    normalized = [
        normalize_ticket(_ticket(channel=channel))
        for channel in SUPPORTED_CHANNELS
    ]

    assert {ticket.channel for ticket in normalized} == SUPPORTED_CHANNELS
    assert all(ticket.to_dict()["ticket_id"] == "TEST-0001" for ticket in normalized)


def test_normalize_ticket_converts_timestamp_to_utc():
    ticket = normalize_ticket(
        _ticket(received_at="2026-03-01T12:00:00+05:30")
    )

    assert ticket.received_at == "2026-03-01T06:30:00Z"


def test_normalize_ticket_rejects_unsupported_channel():
    with pytest.raises(ValueError, match="Unsupported channel"):
        normalize_ticket(_ticket(channel="phone"))


def test_normalize_ticket_requires_subject_or_body():
    with pytest.raises(ValueError, match="subject or body"):
        normalize_ticket(_ticket(subject="", body=""))


def test_load_ticket_records_separates_evaluation_annotations(tmp_path):
    path = tmp_path / "tickets.json"
    path.write_text(json.dumps([_ticket()]), encoding="utf-8")

    [record] = load_ticket_records(path)

    assert record.labels == {"intent": "deployment_failure"}
    assert record.history == {"escalated": False}
    assert "labels" not in record.ticket.to_dict()
    assert "history" not in record.ticket.to_dict()


@pytest.mark.parametrize(
    "dataset_name",
    ["development_tickets.json", "validation_tickets.json"],
)
def test_supplied_ticket_datasets_cover_all_channels(dataset_name):
    from pathlib import Path

    dataset_path = (
        Path(__file__).resolve().parents[1]
        / "evaluation"
        / "data"
        / dataset_name
    )
    records = load_ticket_records(dataset_path)

    assert records
    assert {record.ticket.channel for record in records} == SUPPORTED_CHANNELS
