import json

from src.logging_store import log_decision
from src.review_store import get_review_draft, list_review_drafts


def _log_ticket(database_url, ticket_id, urgency):
    if urgency is not None:
        log_decision(
            {
                "ticket_id": ticket_id,
                "stage": "classification",
                "prediction_value": json.dumps(
                    {"intent": "onboarding", "urgency": urgency, "urgency_confidence": 0.6,
                     "urgency_evidence": "ASAP", "urgency_ambiguous": False}
                ),
                "action_taken": "classified",
                "reason": "test",
            },
            database_url,
        )
    return log_decision(
        {
            "ticket_id": ticket_id,
            "stage": "answer_drafting",
            "prediction_value": json.dumps(
                {"status": "draft_ready", "draft": "See [DOC-A-1].", "citations": ["DOC-A-1"],
                 "ticket_context": {"channel": "email", "subject": "s", "body": "b"}}
            ),
            "sources_used": ["DOC-A-1"],
            "action_taken": "draft_ready",
            "reason": "test",
        },
        database_url,
    )


def test_queue_is_ordered_by_advisory_urgency_and_exposes_it(tmp_path):
    url = f"sqlite:///{tmp_path / 'u.db'}"
    ids = {name: _log_ticket(url, name, urgency)
           for name, urgency in (("T-LOW", "low"), ("T-NONE", None), ("T-HIGH", "high"), ("T-MED", "medium"))}
    queue = list_review_drafts("pending", url)
    assert [d["ticket_id"] for d in queue] == ["T-HIGH", "T-MED", "T-LOW", "T-NONE"]
    assert queue[0]["advisory_urgency"]["label"] == "high"
    assert queue[-1]["advisory_urgency"] is None
    assert get_review_draft(ids["T-MED"], url)["advisory_urgency"]["label"] == "medium"
