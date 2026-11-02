"""Authenticated local API for reviewing and approving grounded reply drafts."""

from __future__ import annotations

import hmac
import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from src.dashboard import build_dashboard_summary
from src.logging_store import PROJECT_ROOT
from src.outcome_store import (
    OutcomeNotFound,
    get_ticket_outcome,
    record_ticket_outcome,
    summarize_ticket_outcomes,
)
from src.review_store import (
    ReviewConflict,
    ReviewNotFound,
    ReviewValidationError,
    get_review_draft,
    get_ticket_decision_history,
    list_review_drafts,
    review_draft,
)


load_dotenv(PROJECT_ROOT / ".env")
app = FastAPI(title="Support Tickets Resolver Agent Review", version="0.1.0")
bearer = HTTPBearer(auto_error=False)
REVIEW_PAGE = PROJECT_ROOT / "static" / "review.html"
DASHBOARD_PAGE = PROJECT_ROOT / "static" / "dashboard.html"


class EditDraftRequest(BaseModel):
    reviewer_id: str = Field(min_length=1, max_length=120)
    edited_draft: str = Field(min_length=1, max_length=20000)


class ApproveDraftRequest(BaseModel):
    reviewer_id: str = Field(min_length=1, max_length=120)


class RejectDraftRequest(BaseModel):
    reviewer_id: str = Field(min_length=1, max_length=120)
    rejection_reason: str = Field(min_length=1, max_length=1000)


class EscalateDraftRequest(BaseModel):
    reviewer_id: str = Field(min_length=1, max_length=120)
    escalation_reason: str = Field(min_length=1, max_length=1000)


class TicketOutcomeRequest(BaseModel):
    reviewer_id: str = Field(min_length=1, max_length=120)
    first_contact_resolution: bool | None = None
    escalated: bool | None = None
    repeat_contact: bool | None = None
    resolution_time_minutes: float | None = Field(default=None, ge=0)
    csat_rating: float | None = Field(default=None, ge=1, le=5)
    customer_tier: str | None = Field(default=None, max_length=120)
    language_fluency: str | None = Field(default=None, max_length=120)
    feedback_category: Literal[
        "draft_accurate", "missing_context", "wrong_source", "unsafe", "tone", "other"
    ] | None = None
    agent_feedback: str | None = Field(default=None, max_length=2000)


def _require_agent(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    expected = os.getenv("AGENT_API_TOKEN", "").strip()
    if not expected or expected == "set_a_long_random_agent_token":
        raise HTTPException(status_code=503, detail="Agent review API is not configured")
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not hmac.compare_digest(credentials.credentials, expected)
    ):
        raise HTTPException(
            status_code=401,
            detail="Valid agent bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return expected


def _database_url() -> str | None:
    return os.getenv("DATABASE_URL")


def _run_review(operation, *args, **kwargs):
    try:
        return operation(*args, **kwargs)
    except ReviewNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReviewConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ReviewValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OutcomeNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/review", include_in_schema=False)
def review_page() -> FileResponse:
    return FileResponse(REVIEW_PAGE, media_type="text/html")


@app.get("/dashboard", include_in_schema=False)
def dashboard_page() -> FileResponse:
    return FileResponse(DASHBOARD_PAGE, media_type="text/html")


@app.get("/api/dashboard/summary")
def dashboard_summary(_agent: str = Depends(_require_agent)) -> dict:
    return build_dashboard_summary(_database_url())


@app.get("/api/review/drafts")
def review_queue(
    status: Literal["pending", "approved", "rejected", "all"] = Query("pending"),
    _agent: str = Depends(_require_agent),
) -> list[dict]:
    return _run_review(list_review_drafts, status, _database_url())


@app.get("/api/review/drafts/{decision_id}")
def read_review_draft(
    decision_id: str, _agent: str = Depends(_require_agent)
) -> dict:
    return _run_review(get_review_draft, decision_id, _database_url())


@app.get("/api/review/tickets/{ticket_id}/history")
def ticket_decision_history(
    ticket_id: str, _agent: str = Depends(_require_agent)
) -> dict:
    return _run_review(get_ticket_decision_history, ticket_id, _database_url())


@app.get("/api/review/tickets/{ticket_id}/outcome")
def read_ticket_outcome(
    ticket_id: str, _agent: str = Depends(_require_agent)
) -> dict | None:
    return get_ticket_outcome(ticket_id, _database_url())


@app.post("/api/review/tickets/{ticket_id}/outcome")
def save_ticket_outcome(
    ticket_id: str,
    request: TicketOutcomeRequest,
    _agent: str = Depends(_require_agent),
) -> dict:
    values = request.model_dump(exclude_unset=True)
    reviewer_id = values.pop("reviewer_id")
    return _run_review(
        record_ticket_outcome,
        ticket_id,
        reviewer_id=reviewer_id,
        database_url=_database_url(),
        **values,
    )


@app.get("/api/review/outcomes/summary")
def ticket_outcome_summary(_agent: str = Depends(_require_agent)) -> dict:
    return summarize_ticket_outcomes(_database_url())


@app.post("/api/review/drafts/{decision_id}/edit")
def edit_review_draft(
    decision_id: str,
    request: EditDraftRequest,
    _agent: str = Depends(_require_agent),
) -> dict:
    return _run_review(
        review_draft,
        decision_id,
        action="edit",
        reviewer_id=request.reviewer_id,
        edited_draft=request.edited_draft,
        database_url=_database_url(),
    )


@app.post("/api/review/drafts/{decision_id}/approve")
def approve_review_draft(
    decision_id: str,
    request: ApproveDraftRequest,
    _agent: str = Depends(_require_agent),
) -> dict:
    return _run_review(
        review_draft,
        decision_id,
        action="approve",
        reviewer_id=request.reviewer_id,
        database_url=_database_url(),
    )


@app.post("/api/review/drafts/{decision_id}/reject")
def reject_review_draft(
    decision_id: str,
    request: RejectDraftRequest,
    _agent: str = Depends(_require_agent),
) -> dict:
    return _run_review(
        review_draft,
        decision_id,
        action="reject",
        reviewer_id=request.reviewer_id,
        rejection_reason=request.rejection_reason,
        database_url=_database_url(),
    )


@app.post("/api/review/drafts/{decision_id}/escalate")
def escalate_review_draft(
    decision_id: str,
    request: EscalateDraftRequest,
    _agent: str = Depends(_require_agent),
) -> dict:
    return _run_review(
        review_draft,
        decision_id,
        action="escalate",
        reviewer_id=request.reviewer_id,
        escalation_reason=request.escalation_reason,
        database_url=_database_url(),
    )
