"""Build source-separated, agent-reviewable escalation summaries."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from src.tickets import NormalizedTicket


def _clean_text(value: Any) -> str:
    return " ".join(value.split()) if isinstance(value, str) else ""


def _history_items(history: Sequence[str | Mapping[str, Any]] | None) -> list[dict[str, str]]:
    items = []
    for entry in history or ():
        if isinstance(entry, str):
            text = _clean_text(entry)
            if text:
                items.append({"text": text})
        elif isinstance(entry, Mapping):
            timestamp = _clean_text(entry.get("timestamp"))
            actor = _clean_text(entry.get("actor") or entry.get("role") or entry.get("speaker"))
            text = _clean_text(
                entry.get("text") or entry.get("content") or entry.get("message") or entry.get("body")
            )
            item = {key: value for key, value in (
                ("timestamp", timestamp), ("actor", actor), ("text", text)
            ) if value}
            if item:
                items.append(item)
    return items


def _documents(sources: Sequence[Mapping[str, Any]] | None) -> list[dict[str, str]]:
    result = []
    for source in sources or ():
        doc_id = _clean_text(source.get("doc_id"))
        title = _clean_text(source.get("title"))
        passage = _clean_text(source.get("passage"))
        if doc_id or title or passage:
            item = {key: value for key, value in (
                ("doc_id", doc_id), ("title", title), ("passage", passage)
            ) if value}
            result.append(item)
    return result


def build_escalation_summary(
    ticket: NormalizedTicket,
    *,
    route_reason: str,
    ticket_history: Sequence[str | Mapping[str, Any]] | None = None,
    troubleshooting_attempted: Sequence[str] | None = None,
    relevant_documents: Sequence[Mapping[str, Any]] | None = None,
    documentation_lookup_error: str | None = None,
    intent: str | None = None,
    urgency: str | None = None,
) -> dict[str, Any]:
    """Summarize evidence without inventing missing history or troubleshooting.

    Ticket text, conversation history, agent-supplied troubleshooting, retrieved
    documents, and model/system assessments remain separate so an agent can assess
    the provenance of every statement before forwarding the summary.
    """
    history = _history_items(ticket_history)
    troubleshooting = [
        text for item in troubleshooting_attempted or ()
        if (text := _clean_text(item))
    ]
    documents = _documents(relevant_documents)
    open_questions = []
    if not history:
        open_questions.append("No prior ticket conversation was provided; review the thread.")
    if not troubleshooting:
        open_questions.append("Troubleshooting attempts were not provided; confirm what has been tried.")
    if documentation_lookup_error:
        open_questions.append("Documentation lookup failed; check the knowledge base manually.")
    elif not documents:
        open_questions.append("No relevant documentation was retrieved; verify whether an article applies.")

    return {
        "ticket_id": ticket.ticket_id,
        "requires_agent_review": True,
        "issue_from_ticket": {"subject": ticket.subject, "body": ticket.body},
        "ticket_history": {"status": "provided" if history else "not_provided", "entries": history},
        "troubleshooting_attempted": {
            "status": "provided" if troubleshooting else "not_provided",
            "items": troubleshooting,
        },
        "relevant_documentation": {
            "status": "lookup_failed" if documentation_lookup_error else (
                "found" if documents else "none_found"
            ),
            "items": documents,
        },
        "system_assessment": {
            "source": "model/system inference; agent must verify",
            "intent": intent,
            "urgency": urgency,
            "routing_reason": _clean_text(route_reason),
        },
        "unresolved_uncertainty": open_questions or [
            "No missing context was detected; agent should verify the summary before escalation."
        ],
    }
