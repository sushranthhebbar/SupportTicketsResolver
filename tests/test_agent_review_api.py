import json
import sqlite3

import httpx
import pytest
import pytest_asyncio

from src.app import app
from src.logging_store import log_decision
from src.review_store import CUSTOMER_DISCLOSURE


@pytest_asyncio.fixture
async def review_client(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'review.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("AGENT_API_TOKEN", "test-agent-token")
    decision_id = log_decision(
        {
            "ticket_id": "T-REVIEW-1",
            "stage": "answer_drafting",
            "prediction_value": json.dumps(
                {
                    "status": "draft_ready",
                    "draft": "Follow the migration guide [DOC-DB-001].",
                    "citations": ["DOC-DB-001"],
                    "ticket_context": {
                        "channel": "email",
                        "subject": "Migration blocked",
                        "body": "The deployment cannot finish.",
                    },
                }
            ),
            "sources_used": ["DOC-DB-001"],
            "action_taken": "draft_ready",
            "reason": "Grounded in retrieved documentation.",
        },
        database_url,
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        client.headers.update({"Authorization": "Bearer test-agent-token"})
        yield client, decision_id, database_url


@pytest.mark.asyncio
async def test_agent_can_edit_then_approve_and_approval_is_audited(review_client):
    client, decision_id, database_url = review_client
    queue = await client.get("/api/review/drafts")
    assert queue.status_code == 200
    assert queue.json()[0]["decision_id"] == decision_id

    edited = await client.post(
        f"/api/review/drafts/{decision_id}/edit",
        json={
            "reviewer_id": "agent-17",
            "edited_draft": "Please follow the migration guide [DOC-DB-001].",
        },
    )
    assert edited.status_code == 200
    assert edited.json()["status"] == "pending"
    assert edited.json()["was_edited"] is True

    approved = await client.post(
        f"/api/review/drafts/{decision_id}/approve",
        json={"reviewer_id": "agent-17"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["source_ids"] == ["DOC-DB-001"]
    assert approved.json()["ticket_context"]["body"] == "The deployment cannot finish."
    assert approved.json()["customer_disclosure"] == CUSTOMER_DISCLOSURE
    history = await client.get("/api/review/tickets/T-REVIEW-1/history")
    assert history.status_code == 200
    events = history.json()["events"]
    assert any(event["stage"] == "answer_drafting" for event in events)
    assert [event["action_taken"] for event in events if event["stage"] == "agent_review"] == ["edit", "approve"]

    outcome = await client.post(
        "/api/review/tickets/T-REVIEW-1/outcome",
        json={
            "reviewer_id": "agent-17",
            "first_contact_resolution": True,
            "escalated": False,
            "customer_tier": "business",
            "language_fluency": "non_fluent",
            "feedback_category": "draft_accurate",
        },
    )
    assert outcome.status_code == 200
    summary = await client.get("/api/review/outcomes/summary")
    assert summary.status_code == 200
    assert summary.json()["by_customer_tier"]["business"]["first_contact_resolution_rate"] == 1.0
    with sqlite3.connect(database_url.removeprefix("sqlite:///")) as connection:
        rows = connection.execute(
            "SELECT action_taken, requirement_ids_json FROM decisions WHERE stage='agent_review'"
        ).fetchall()
    assert [row[0] for row in rows] == ["edit", "approve"]
    assert all("FR-04" in row[1] for row in rows)


@pytest.mark.asyncio
async def test_agent_can_reject_and_final_review_cannot_be_reversed(review_client):
    client, decision_id, _database_url = review_client
    rejected = await client.post(
        f"/api/review/drafts/{decision_id}/reject",
        json={"reviewer_id": "agent-18", "rejection_reason": "The article is outdated."},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"

    approve = await client.post(
        f"/api/review/drafts/{decision_id}/approve",
        json={"reviewer_id": "agent-18"},
    )
    assert approve.status_code == 409


@pytest.mark.asyncio
async def test_agent_can_record_escalation_in_ticket_history(review_client):
    client, decision_id, _database_url = review_client
    response = await client.post(
        f"/api/review/drafts/{decision_id}/escalate",
        json={"reviewer_id": "agent-20", "escalation_reason": "Needs a database specialist."},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["last_action"] == "escalate"
    history = await client.get("/api/review/tickets/T-REVIEW-1/history")
    assert any(
        event["stage"] == "agent_review" and event["action_taken"] == "escalate"
        for event in history.json()["events"]
    )


@pytest.mark.asyncio
async def test_review_api_requires_token_and_rejects_ungrounded_edits(review_client):
    client, decision_id, _database_url = review_client
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as unauthenticated:
        assert (await unauthenticated.get("/api/review/drafts")).status_code == 401

    response = await client.post(
        f"/api/review/drafts/{decision_id}/edit",
        json={
            "reviewer_id": "agent-19",
            "edited_draft": "Use the unverified instructions [DOC-OTHER-999].",
        },
    )
    assert response.status_code == 422
