"""Deterministic validation and safety checks for generated reply drafts."""

from __future__ import annotations

import re
from typing import Any, Mapping


PROMPT_INJECTION_RE = re.compile(
    r"\b(ignore|override|disregard)\b.{0,60}\b(previous|above|system|developer)\b.{0,30}\b(instruction|prompt|rule)s?\b",
    re.IGNORECASE | re.DOTALL,
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"\b(?:sk|pk|rk|api)[-_][A-Za-z0-9_-]{16,}\b", re.IGNORECASE),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}", re.IGNORECASE),
    re.compile(r"\b(?:password|secret|api[_ -]?key|access[_ -]?token)\s*[:=]\s*['\"]?[^\s'\"]{12,}", re.IGNORECASE),
)
INLINE_CITATION_RE = re.compile(r"\[(DOC-[A-Za-z0-9_-]+)\]")


def safe_answer_failure(
    reason_code: str,
    reason: str,
    *,
    next_step: str = "escalate",
    status: str = "needs_human",
) -> dict[str, Any]:
    """Return a consistent no-send result when drafting cannot safely proceed."""
    return {
        "answer_status": status,
        "answer": "",
        "citations": [],
        "reason": reason,
        "recommended_next_step": next_step,
        "action": "block" if status == "blocked" else "review",
        "guardrail_results": {
            reason_code: {"passed": False, "reason": reason}
        },
        "prompt_version": "PR-02-v2",
    }


def check_ticket_input(subject: str, body: str) -> dict[str, Any] | None:
    """Return a blocked result if the ticket text carries credentials or instruction-like text.

    Runs before retrieval and drafting, so such a ticket never reaches the model for a reply.
    The matched categories are recorded, not the matched text.
    """
    text = f"{subject}\n{body}"
    found = []
    if PROMPT_INJECTION_RE.search(text):
        found.append("instruction_like_text")
    if any(pattern.search(text) for pattern in SECRET_VALUE_PATTERNS):
        found.append("credential_like_text")
    if not found:
        return None
    failure = safe_answer_failure(
        "input_integrity",
        "The ticket contains " + " and ".join(name.replace("_", " ") for name in found)
        + "; no draft was generated and an agent must review it.",
        status="blocked",
    )
    failure["guardrail_results"]["input_integrity"]["matched"] = found
    return failure


def validate_grounded_answer(
    payload: Mapping[str, Any],
    retrieved_sources: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Validate answer schema, evidence sufficiency, citation mapping, and safety."""
    if not isinstance(payload, Mapping) or not isinstance(retrieved_sources, list):
        return safe_answer_failure("malformed_input", "Reply validation received malformed input.")
    sufficient = payload.get("sufficient_evidence")
    draft = payload.get("draft")
    citations = payload.get("citations")
    reason = payload.get("reason")
    next_step = payload.get("next_step")
    if not isinstance(sufficient, bool):
        return safe_answer_failure("malformed_output", "Provider output omitted a valid evidence decision.")
    if not isinstance(draft, str) or not isinstance(citations, list):
        return safe_answer_failure("malformed_output", "Provider output did not match the reply schema.")
    if not isinstance(reason, str) or not isinstance(next_step, str):
        return safe_answer_failure("malformed_output", "Provider output omitted a reason or next step.")

    if not sufficient:
        if next_step not in {"ask_clarification", "escalate"}:
            next_step = "escalate"
        return {
            "answer_status": "needs_human",
            "answer": "",
            "citations": [],
            "reason": reason.strip() or "Retrieved evidence is insufficient to support a reply.",
            "recommended_next_step": next_step,
            "action": "review",
            "guardrail_results": {
                "evidence_sufficiency": {"passed": False, "reason": reason}
            },
            "prompt_version": "PR-02-v2",
        }

    if not draft.strip():
        return safe_answer_failure("malformed_output", "Provider marked evidence sufficient but returned no draft.")
    if any(not isinstance(citation, str) or not citation for citation in citations):
        return safe_answer_failure("malformed_output", "Citation entries must be non-empty source ID strings.")

    allowed_ids = {
        source.get("doc_id")
        for source in retrieved_sources
        if isinstance(source, Mapping)
        and isinstance(source.get("doc_id"), str)
        and source.get("doc_id")
    }
    inline_ids = set(INLINE_CITATION_RE.findall(draft))
    if not inline_ids:
        return safe_answer_failure(
            "citation_validation",
            "A grounded reply must cite at least one retrieved source inline.",
        )
    if not inline_ids <= allowed_ids:
        failure = safe_answer_failure(
            "citation_validation",
            "The draft cites a source that was not retrieved for this ticket.",
        )
        failure["guardrail_results"]["citation_validation"].update(
            {
                "structured_source_ids": sorted(set(citations)),
                "inline_source_ids": sorted(inline_ids),
            }
        )
        return failure

    # Inline citations are customer-visible evidence references. Validate them
    # against retrieval, then derive the redundant structured list from them so
    # provider disagreement cannot discard an otherwise safely cited draft.
    citation_metadata_reconciled = set(citations) != inline_ids
    cited_ids = inline_ids

    if PROMPT_INJECTION_RE.search(draft) or any(
        pattern.search(draft) for pattern in SECRET_VALUE_PATTERNS
    ):
        return safe_answer_failure(
            "unsafe_content",
            "The draft contains instruction-like or credential-like content and was blocked.",
            status="blocked",
        )

    return {
        "answer_status": "draft_ready",
        "answer": draft.strip(),
        "citations": sorted(cited_ids),
        "reason": reason.strip() or "Draft is grounded in retrieved documentation.",
        "recommended_next_step": "agent_review",
        "action": "draft_ready",
        "guardrail_results": {
            "evidence_sufficiency": {"passed": True},
            "citation_validation": {
                "passed": True,
                "source_ids": sorted(cited_ids),
                "metadata_reconciled": citation_metadata_reconciled,
            },
            "unsafe_content": {"passed": True},
        },
        "prompt_version": "PR-02-v2",
    }
