import json

from src.escalation import build_escalation_summary
from src.logging_store import count_decisions
from src.pipeline import process_ticket
from src.tickets import normalize_ticket


def _ticket():
    return normalize_ticket(
        {
            "ticket_id": "T-ESC-1",
            "channel": "email",
            "subject": "Production deployment blocked",
            "body": "The release fails during database migration.",
            "received_at": "2026-01-01T00:00:00Z",
        }
    )


def _classification():
    return {
        "intent": "deployment_failure",
        "intent_confidence": 0.96,
        "urgency": "high",
        "urgency_confidence": 0.92,
        "urgency_evidence": "release fails",
        "urgency_evidence_valid": True,
        "urgency_ambiguous": False,
        "model_name": "test-classifier",
    }


def test_escalation_summary_keeps_sources_separate_and_flags_missing_context():
    summary = build_escalation_summary(
        _ticket(),
        route_reason="High urgency requires immediate human attention.",
        relevant_documents=[
            {"doc_id": "DOC-DB-001", "title": "Migration recovery", "passage": "Restore the last valid snapshot."}
        ],
        intent="deployment_failure",
        urgency="high",
    )

    assert summary["issue_from_ticket"]["body"] == "The release fails during database migration."
    assert summary["ticket_history"]["status"] == "not_provided"
    assert summary["troubleshooting_attempted"]["status"] == "not_provided"
    assert summary["relevant_documentation"]["items"][0]["doc_id"] == "DOC-DB-001"
    assert summary["system_assessment"]["source"].startswith("model/system inference")
    assert len(summary["unresolved_uncertainty"]) == 2
    assert summary["requires_agent_review"] is True


def test_escalation_pipeline_returns_and_logs_summary(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'escalation.db'}"
    sources = [{"doc_id": "DOC-DB-001", "title": "Migration recovery", "passage": "Restore a snapshot."}]
    result = process_ticket(
        _ticket(),
        classifier=lambda _ticket: _classification(),
        database_url=database_url,
        retriever=lambda _query: sources,
        generate_answer=False,
        ticket_history=[{"timestamp": "2026-01-01T00:01:00Z", "actor": "agent", "text": "Requested migration logs."}],
        troubleshooting_attempted=["Requested migration logs"],
    )

    summary = result["escalation_summary"]
    assert result["route"] == "escalate"
    assert summary["ticket_history"]["status"] == "provided"
    assert summary["troubleshooting_attempted"]["items"] == ["Requested migration logs"]
    assert summary["unresolved_uncertainty"] == [
        "No missing context was detected; agent should verify the summary before escalation."
    ]
    assert count_decisions(database_url) == 3

    import sqlite3

    with sqlite3.connect(database_url.removeprefix("sqlite:///")) as connection:
        row = connection.execute(
            "SELECT prediction_value FROM decisions WHERE stage='escalation_summary'"
        ).fetchone()
    assert json.loads(row[0])["ticket_id"] == "T-ESC-1"
