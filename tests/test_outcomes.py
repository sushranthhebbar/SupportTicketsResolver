import pytest

from src.logging_store import log_decision
from src.outcome_store import (
    OutcomeNotFound,
    record_ticket_outcome,
    summarize_ticket_outcomes,
)


def _record_assisted(ticket_id, database_url):
    return log_decision(
        {
            "ticket_id": ticket_id,
            "stage": "classification",
            "prediction_value": "{}",
            "action_taken": "classified",
            "reason": "Ticket assistance recorded.",
        },
        database_url,
    )


def test_records_assisted_ticket_outcomes_and_reports_by_customer_segments(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'outcomes.db'}"
    _record_assisted("T-OUT-1", database_url)
    _record_assisted("T-OUT-2", database_url)

    record_ticket_outcome(
        "T-OUT-1",
        reviewer_id="agent-1",
        first_contact_resolution=True,
        escalated=False,
        repeat_contact=False,
        resolution_time_minutes=20,
        csat_rating=4,
        customer_tier="business",
        language_fluency="non_fluent",
        feedback_category="draft_accurate",
        database_url=database_url,
    )
    updated = record_ticket_outcome(
        "T-OUT-1",
        reviewer_id="agent-2",
        agent_feedback="The provided source resolved the question.",
        database_url=database_url,
    )
    assert updated["first_contact_resolution"] is True
    assert updated["csat_rating"] == 4

    record_ticket_outcome(
        "T-OUT-2",
        reviewer_id="agent-2",
        first_contact_resolution=False,
        escalated=True,
        repeat_contact=True,
        resolution_time_minutes=40,
        csat_rating=2,
        customer_tier="enterprise",
        language_fluency="fluent",
        feedback_category="missing_context",
        database_url=database_url,
    )
    summary = summarize_ticket_outcomes(database_url)
    assert summary["tickets_with_recorded_outcomes"] == 2
    assert summary["by_customer_tier"]["business"]["first_contact_resolution_rate"] == 1.0
    assert summary["by_customer_tier"]["enterprise"]["escalation_rate"] == 1.0
    assert summary["by_language_fluency"]["non_fluent"]["mean_csat_rating"] == 4
    assert "do not establish" in summary["interpretation"]


def test_outcomes_require_assistance_and_valid_ranges(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'invalid-outcomes.db'}"
    with pytest.raises(OutcomeNotFound):
        record_ticket_outcome(
            "UNASSISTED",
            reviewer_id="agent-1",
            first_contact_resolution=True,
            database_url=database_url,
        )

    _record_assisted("T-OUT-3", database_url)
    with pytest.raises(ValueError, match="csat_rating"):
        record_ticket_outcome(
            "T-OUT-3",
            reviewer_id="agent-1",
            csat_rating=7,
            database_url=database_url,
        )
