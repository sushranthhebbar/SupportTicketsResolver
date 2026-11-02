import json

import httpx
import pytest
import pytest_asyncio

from src.app import app
from src.dashboard import build_dashboard_summary
from src.logging_store import log_decision
from src.outcome_store import record_ticket_outcome


@pytest_asyncio.fixture
async def dashboard_client(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'dashboard.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("AGENT_API_TOKEN", "dashboard-test-token")
    log_decision(
        {
            "timestamp": "2026-11-01T10:00:00+00:00",
            "ticket_id": "T-DASH-1",
            "stage": "classification",
            "prediction_value": json.dumps({"channel": "email", "intent": "billing", "urgency": "medium"}),
            "action_taken": "classified",
            "reason": "Classified ticket.",
        },
        database_url,
    )
    log_decision(
        {
            "timestamp": "2026-11-01T10:00:01+00:00",
            "ticket_id": "T-DASH-1",
            "stage": "routing",
            "prediction_value": "review",
            "action_taken": "review",
            "reason": "Confidence requires review.",
        },
        database_url,
    )
    log_decision(
        {
            "timestamp": "2026-11-01T10:00:02+00:00",
            "ticket_id": "T-DASH-1",
            "stage": "answer_drafting",
            "prediction_value": "{}",
            "action_taken": "review",
            "reason": "Insufficient evidence.",
            "guardrail_results": {"evidence_sufficiency": {"passed": False}},
        },
        database_url,
    )
    record_ticket_outcome(
        "T-DASH-1",
        reviewer_id="agent-1",
        first_contact_resolution=True,
        customer_tier="business",
        language_fluency="non_fluent",
        database_url=database_url,
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        client.headers.update({"Authorization": "Bearer dashboard-test-token"})
        yield client, database_url


def test_dashboard_summary_aggregates_logged_activity_and_outcome_coverage(dashboard_client):
    _client, database_url = dashboard_client
    summary = build_dashboard_summary(database_url)
    assert summary["assisted_tickets"] == 1
    assert summary["daily_ticket_volume"] == {"2026-11-01": 1}
    assert summary["routes"] == {"review": 1}
    assert summary["channels"] == {"email": 1}
    assert summary["guardrail_failures"] == {"evidence_sufficiency": 1}
    assert summary["outcome_coverage"]["coverage_rate"] == 1.0
    assert summary["latency"]["available"] is False
    assert "do not establish" in summary["interpretation"]


@pytest.mark.asyncio
async def test_dashboard_page_and_summary_require_authenticated_data_access(dashboard_client):
    client, _database_url = dashboard_client
    page = await client.get("/dashboard")
    assert page.status_code == 200
    assert "Support operations dashboard" in page.text
    summary = await client.get("/api/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json()["assisted_tickets"] == 1
    client.headers.pop("Authorization")
    assert (await client.get("/api/dashboard/summary")).status_code == 401
