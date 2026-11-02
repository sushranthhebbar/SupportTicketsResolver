"""Persistent agent-review workflow for grounded reply drafts."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from typing import Any, Mapping

from src.guardrails import INLINE_CITATION_RE, validate_grounded_answer
from src.logging_store import connect, log_decision


CUSTOMER_DISCLOSURE = (
    "This response was prepared with AI assistance and reviewed by a support agent."
)
REVIEW_SCHEMA = """
CREATE TABLE IF NOT EXISTS agent_reviews (
    draft_decision_id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'approved', 'rejected')),
    current_draft TEXT NOT NULL,
    reviewer_id TEXT,
    last_action TEXT NOT NULL,
    rejection_reason TEXT,
    customer_disclosure TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


class ReviewNotFound(LookupError):
    pass


class ReviewConflict(RuntimeError):
    pass


class ReviewValidationError(ValueError):
    pass


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _decode_prediction(row: sqlite3.Row) -> dict[str, Any]:
    try:
        prediction = json.loads(row["prediction_value"] or "{}")
    except (TypeError, json.JSONDecodeError) as exc:
        raise ReviewValidationError("Stored draft is malformed") from exc
    if not isinstance(prediction, dict) or prediction.get("status") != "draft_ready":
        raise ReviewNotFound("No reviewable draft exists for this decision")
    sources = json.loads(row["sources_used_json"] or "[]")
    if not isinstance(sources, list):
        sources = []
    details = prediction.get("retrieved_sources", [])
    if not isinstance(details, list):
        details = []
    source_ids = [source for source in sources if isinstance(source, str)]
    normalized_details = []
    for source in details:
        if isinstance(source, Mapping) and isinstance(source.get("doc_id"), str):
            normalized_details.append({
                "doc_id": source["doc_id"],
                "title": source.get("title") if isinstance(source.get("title"), str) else "",
                "passage": source.get("passage") if isinstance(source.get("passage"), str) else "",
            })
    if not source_ids:
        source_ids = [source["doc_id"] for source in normalized_details]
    return {
        "decision_id": row["decision_id"],
        "ticket_id": row["ticket_id"],
        "draft": prediction.get("draft", ""),
        "citations": prediction.get("citations", []),
        "ticket_context": prediction.get("ticket_context", {}),
        "source_ids": source_ids,
        "sources": normalized_details or [{"doc_id": source_id, "title": "", "passage": ""} for source_id in source_ids],
    }


def _read_draft(connection: sqlite3.Connection, decision_id: str) -> dict[str, Any]:
    row = connection.execute(
        """SELECT decision_id, ticket_id, prediction_value, sources_used_json
           FROM decisions WHERE decision_id=? AND stage='answer_drafting'""",
        (decision_id,),
    ).fetchone()
    if row is None:
        raise ReviewNotFound("Draft not found")
    return _decode_prediction(row)


def _review_state(connection: sqlite3.Connection, decision_id: str) -> sqlite3.Row | None:
    connection.execute(REVIEW_SCHEMA)
    return connection.execute(
        "SELECT * FROM agent_reviews WHERE draft_decision_id=?", (decision_id,)
    ).fetchone()


def _view(draft: Mapping[str, Any], state: sqlite3.Row | None) -> dict[str, Any]:
    status = state["status"] if state else "pending"
    current_draft = state["current_draft"] if state else draft["draft"]
    citations = sorted(set(INLINE_CITATION_RE.findall(current_draft)))
    return {
        "decision_id": draft["decision_id"],
        "ticket_id": draft["ticket_id"],
        "ticket_context": draft["ticket_context"],
        "status": status,
        "draft": current_draft,
        "was_edited": current_draft != draft["draft"],
        "citations": citations,
        "source_ids": draft["source_ids"],
        "sources": draft["sources"],
        "customer_disclosure": CUSTOMER_DISCLOSURE,
        "reviewer_id": state["reviewer_id"] if state else None,
        "last_action": state["last_action"] if state else "draft_created",
        "rejection_reason": state["rejection_reason"] if state else None,
    }


def _all_drafts(database_url: str | None = None) -> list[dict[str, Any]]:
    with closing(connect(database_url)) as connection:
        connection.execute(REVIEW_SCHEMA)
        rows = connection.execute(
            """SELECT decision_id, ticket_id, prediction_value, sources_used_json
               FROM decisions WHERE stage='answer_drafting' ORDER BY timestamp DESC"""
        ).fetchall()
        result = []
        for row in rows:
            try:
                draft = _decode_prediction(row)
            except ReviewNotFound:
                continue
            result.append(_view(draft, _review_state(connection, draft["decision_id"])))
        return result


def list_review_drafts(
    status: str = "pending", database_url: str | None = None
) -> list[dict[str, Any]]:
    if status not in {"pending", "approved", "rejected", "all"}:
        raise ReviewValidationError("status must be pending, approved, rejected, or all")
    drafts = _all_drafts(database_url)
    return drafts if status == "all" else [draft for draft in drafts if draft["status"] == status]


def get_review_draft(decision_id: str, database_url: str | None = None) -> dict[str, Any]:
    with closing(connect(database_url)) as connection:
        connection.execute(REVIEW_SCHEMA)
        draft = _read_draft(connection, decision_id)
        return _view(draft, _review_state(connection, decision_id))


def get_ticket_decision_history(
    ticket_id: str, database_url: str | None = None
) -> dict[str, Any]:
    with closing(connect(database_url)) as connection:
        rows = connection.execute(
            """SELECT decision_id,timestamp,stage,model_name,model_version,
                      prediction_value,sources_used_json,action_taken,reason,
                      guardrail_results_json,requirement_ids_json
               FROM decisions WHERE ticket_id=? ORDER BY timestamp, rowid""",
            (ticket_id,),
        ).fetchall()
    if not rows:
        raise ReviewNotFound("No assisted-ticket history found")
    events = []
    for row in rows:
        def parse_json(value: str | None, fallback: Any) -> Any:
            try:
                return json.loads(value) if value else fallback
            except (TypeError, json.JSONDecodeError):
                return fallback

        events.append(
            {
                "decision_id": row["decision_id"],
                "timestamp": row["timestamp"],
                "stage": row["stage"],
                "model_name": row["model_name"],
                "model_version": row["model_version"],
                "prediction": parse_json(row["prediction_value"], row["prediction_value"]),
                "sources_used": parse_json(row["sources_used_json"], []),
                "action_taken": row["action_taken"],
                "reason": row["reason"],
                "guardrail_results": parse_json(row["guardrail_results_json"], {}),
                "requirement_ids": parse_json(row["requirement_ids_json"], []),
            }
        )
    return {"ticket_id": ticket_id, "events": events}


def _validate_draft(draft: Mapping[str, Any], text: str) -> list[str]:
    citation_ids = sorted(set(INLINE_CITATION_RE.findall(text)))
    allowed = set(draft["source_ids"])
    validation = validate_grounded_answer(
        {
            "sufficient_evidence": True,
            "draft": text,
            "citations": citation_ids,
            "reason": "Agent-reviewed draft",
            "next_step": "ask_clarification",
        },
        [{"doc_id": source_id, "passage": "Previously retrieved source."} for source_id in allowed],
    )
    if validation["answer_status"] != "draft_ready":
        raise ReviewValidationError(validation["reason"])
    return citation_ids


def review_draft(
    decision_id: str,
    *,
    action: str,
    reviewer_id: str,
    edited_draft: str | None = None,
    rejection_reason: str | None = None,
    escalation_reason: str | None = None,
    database_url: str | None = None,
) -> dict[str, Any]:
    reviewer = reviewer_id.strip()
    if not reviewer or len(reviewer) > 120:
        raise ReviewValidationError("reviewer_id must contain 1 to 120 characters")
    if action not in {"edit", "approve", "reject", "escalate"}:
        raise ReviewValidationError("action must be edit, approve, reject, or escalate")

    with closing(connect(database_url)) as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(REVIEW_SCHEMA)
        draft = _read_draft(connection, decision_id)
        state = _review_state(connection, decision_id)
        status = state["status"] if state else "pending"
        if status in {"approved", "rejected"}:
            raise ReviewConflict(f"Draft is already {status}")

        current = state["current_draft"] if state else draft["draft"]
        if action == "edit":
            if not isinstance(edited_draft, str) or not edited_draft.strip():
                raise ReviewValidationError("edited_draft is required for edit")
            current = edited_draft.strip()
            citations = _validate_draft(draft, current)
            new_status = "pending"
            rejection = None
            decision_reason = "Agent edited the draft; it remains pending approval."
        elif action == "approve":
            if edited_draft is not None:
                raise ReviewValidationError("Edit the draft before approving it")
            citations = _validate_draft(draft, current)
            new_status = "approved"
            rejection = None
            decision_reason = "Agent approved the cited draft for downstream delivery."
        else:
            citations = sorted(set(INLINE_CITATION_RE.findall(current)))
            if action == "reject":
                if edited_draft is not None:
                    raise ReviewValidationError("A rejected draft cannot include edited_draft")
                if not isinstance(rejection_reason, str) or not rejection_reason.strip():
                    raise ReviewValidationError("rejection_reason is required for reject")
                new_status = "rejected"
                rejection = rejection_reason.strip()[:1000]
                decision_reason = rejection
            else:
                if edited_draft is not None or rejection_reason is not None:
                    raise ReviewValidationError("Escalation cannot include draft edits or rejection reason")
                if not isinstance(escalation_reason, str) or not escalation_reason.strip():
                    raise ReviewValidationError("escalation_reason is required for escalate")
                new_status = "pending"
                rejection = None
                decision_reason = "Agent recorded escalation: " + escalation_reason.strip()[:1000]

        now = _iso_now()
        created = state["created_at"] if state else now
        connection.execute(
            """INSERT INTO agent_reviews (
                 draft_decision_id,ticket_id,status,current_draft,reviewer_id,last_action,
                 rejection_reason,customer_disclosure,created_at,updated_at
               ) VALUES (?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(draft_decision_id) DO UPDATE SET
                 status=excluded.status,current_draft=excluded.current_draft,
                 reviewer_id=excluded.reviewer_id,last_action=excluded.last_action,
                 rejection_reason=excluded.rejection_reason,
                 customer_disclosure=excluded.customer_disclosure,updated_at=excluded.updated_at""",
            (decision_id, draft["ticket_id"], new_status, current, reviewer, action,
             rejection, CUSTOMER_DISCLOSURE, created, now),
        )
        connection.commit()

    log_decision(
        {
            "ticket_id": draft["ticket_id"],
            "stage": "agent_review",
            "prediction_value": json.dumps(
                {
                    "draft_decision_id": decision_id,
                    "status": new_status,
                    "draft": current,
                    "citations": citations,
                    "customer_disclosure": CUSTOMER_DISCLOSURE,
                    "reviewer_id": reviewer,
                    "rejection_reason": rejection,
                },
                ensure_ascii=False,
            ),
            "sources_used": citations,
            "action_taken": action,
            "reason": decision_reason,
            "requirement_ids": ["FR-04", "FR-07"],
        },
        database_url,
    )
    return get_review_draft(decision_id, database_url)
