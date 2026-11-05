"""Classification, routing, grounded drafting, and decision logging pipeline."""

from __future__ import annotations

import json
from typing import Any, Callable, Mapping, Sequence

from src.calibration import configured_artifact
from src.classification import classify_ticket
from src.escalation import build_escalation_summary
from src.logging_store import log_decision
from src.routing import route_ticket
from src.tickets import NormalizedTicket


Classifier = Callable[[NormalizedTicket], Mapping[str, Any]]
Retriever = Callable[[str], list[Mapping[str, Any]]]
Answerer = Callable[[NormalizedTicket, list[Mapping[str, Any]]], Mapping[str, Any]]


def process_ticket(
    ticket: NormalizedTicket,
    *,
    classifier: Classifier = classify_ticket,
    calibrated_confidence: Mapping[str, float] | None = None,
    min_confidence: float = 0.80,
    database_url: str | None = None,
    retriever: Retriever | None = None,
    answerer: Answerer | None = None,
    generate_answer: bool = True,
    ticket_history: Sequence[str | Mapping[str, Any]] | None = None,
    troubleshooting_attempted: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Classify, route, optionally draft a grounded reply, and persist decisions.

    Drafts are always for agent review. Retrieval/drafting failures produce a safe
    review result rather than aborting the evaluation batch.
    """
    classification = dict(classifier(ticket))
    calibration_version = None
    if calibrated_confidence is None:
        artifact = configured_artifact()
        if artifact is not None:
            calibrated_confidence = artifact.calibrate(classification)
            if calibrated_confidence is not None:
                calibration_version = artifact.version
    routing = route_ticket(
        classification,
        calibrated_confidence=calibrated_confidence,
        min_confidence=min_confidence,
    )
    routing["calibration_version"] = calibration_version
    retrieved_sources: list[Mapping[str, Any]] = []
    answer_result: dict[str, Any] | None = None
    escalation_summary: dict[str, Any] | None = None
    documentation_lookup_error: str | None = None
    if routing["route"] == "escalate":
        try:
            if retriever is None:
                from src.retrieve import search_documentation

                retriever = search_documentation
            query = "\n".join(part for part in (ticket.subject, ticket.body) if part.strip())
            retrieved_sources = list(retriever(query))
        except Exception as exc:
            documentation_lookup_error = type(exc).__name__
        escalation_summary = build_escalation_summary(
            ticket,
            route_reason=routing["reason"],
            ticket_history=ticket_history,
            troubleshooting_attempted=troubleshooting_attempted,
            relevant_documents=retrieved_sources,
            documentation_lookup_error=documentation_lookup_error,
            intent=classification.get("intent"),
            urgency=classification.get("urgency"),
        )
    elif generate_answer:
        try:
            if retriever is None:
                from src.retrieve import search_documentation

                retriever = search_documentation
            if answerer is None:
                from src.answering import draft_grounded_reply

                answerer = draft_grounded_reply
            query = "\n".join(part for part in (ticket.subject, ticket.body) if part.strip())
            retrieved_sources = list(retriever(query))
            answer_result = dict(answerer(ticket, retrieved_sources))
        except Exception:
            from src.guardrails import safe_answer_failure

            answer_result = safe_answer_failure(
                "retrieval_or_drafting_failure",
                "Retrieval or drafting failed; no reply was generated.",
                next_step="retry_later",
            )
        if answer_result.get("action") in {"review", "block"}:
            routing["route"] = "review"
            routing["action"] = "review"
            routing["reason"] = (
                "Grounded reply requires human review: "
                + str(answer_result.get("reason") or "evidence or safety check failed")
            )

    common = {
        "ticket_id": ticket.ticket_id,
        "model_name": classification.get("model_name"),
        "model_version": classification.get("model_version"),
        "prompt_version": classification.get("prompt_version", "PR-03-v2"),
        "requirement_ids": ["FR-09"],
        "input_summary": f"Ticket {ticket.ticket_id} received on {ticket.channel}.",
    }
    log_decision(
        {
            **common,
            "stage": "classification",
            "prediction_value": json.dumps(
                {
                    "channel": ticket.channel,
                    **{key: classification.get(key) for key in (
                        "intent", "intent_confidence", "urgency", "urgency_confidence",
                        "confidence_kind", "urgency_evidence", "urgency_evidence_valid",
                        "urgency_ambiguous",
                    )},
                },
                ensure_ascii=False,
            ),
            "prediction_confidence": min(
                classification["intent_confidence"], classification["urgency_confidence"]
            ),
            "action_taken": "classified",
            "reason": "Intent and urgency classified using PR-03.",
        },
        database_url,
    )
    if answer_result is not None:
        retrieved_ids = [
            source.get("doc_id")
            for source in retrieved_sources
            if isinstance(source.get("doc_id"), str) and source.get("doc_id")
        ]
        log_decision(
            {
                **common,
                "model_name": answer_result.get("model_name"),
                "stage": "answer_drafting",
                "prediction_value": json.dumps(
                    {
                        "status": answer_result.get("answer_status"),
                        "draft": answer_result.get("answer", ""),
                        "citations": answer_result.get("citations", []),
                        "ticket_context": {
                            "channel": ticket.channel,
                            "subject": ticket.subject,
                            "body": ticket.body,
                        },
                        "retrieved_sources": [
                            {
                                "doc_id": source.get("doc_id"),
                                "title": source.get("title"),
                                "passage": source.get("passage"),
                            }
                            for source in retrieved_sources
                            if isinstance(source.get("doc_id"), str)
                        ],
                    },
                    ensure_ascii=False,
                ),
                "sources_used": retrieved_ids,
                "action_taken": answer_result.get("action", "review"),
                "reason": str(answer_result.get("reason") or "No answer reason supplied."),
                "guardrail_results": answer_result.get("guardrail_results", {}),
                "prompt_version": answer_result.get("prompt_version", "PR-02-v2"),
                "requirement_ids": ["FR-03", "FR-04", "FR-05", "FR-07", "B-08", "B-09"],
            },
            database_url,
        )
    if escalation_summary is not None:
        log_decision(
            {
                **common,
                "stage": "escalation_summary",
                "prediction_value": json.dumps(escalation_summary, ensure_ascii=False),
                "sources_used": [
                    source.get("doc_id")
                    for source in retrieved_sources
                    if isinstance(source.get("doc_id"), str)
                ],
                "action_taken": "prepared_for_agent_review",
                "reason": "FR-06 escalation summary prepared from ticket and available context.",
                "requirement_ids": ["FR-06"],
            },
            database_url,
        )
    log_decision(
        {
            **common,
            "stage": "routing",
            "prediction_value": routing["route"],
            "prediction_confidence": min(routing["calibrated_confidence"].values())
            if routing["calibrated_confidence"] else None,
            "threshold_applied": routing["threshold_applied"],
            "action_taken": routing["route"],
            "reason": routing["reason"],
            "requirement_ids": ["FR-07", "FR-09", "B-10"],
        },
        database_url,
    )
    source_summaries = [
        {
            "doc_id": source.get("doc_id"),
            "title": source.get("title"),
            "distance": source.get("distance"),
        }
        for source in retrieved_sources
    ]
    final_action = (
        "block"
        if answer_result and answer_result.get("action") == "block"
        else routing["route"]
    )
    return {
        **classification,
        **routing,
        "retrieved_sources": source_summaries,
        "answer_status": answer_result.get("answer_status") if answer_result else "not_generated",
        "answer": answer_result.get("answer", "") if answer_result else "",
        "citations": answer_result.get("citations", []) if answer_result else [],
        "answer_reason": answer_result.get("reason") if answer_result else None,
        "recommended_next_step": answer_result.get("recommended_next_step") if answer_result else None,
        "escalation_summary": escalation_summary,
        "guardrail_results": answer_result.get("guardrail_results", {}) if answer_result else {},
        "route": routing["route"],
        "action": final_action,
        "latency_seconds": None,
    }
