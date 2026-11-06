"""Repeatable routing policy for classified tickets."""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_MIN_CALIBRATED_CONFIDENCE = 0.80
ROUTER_VERSION = "router-v4"
# Intents whose tickets must never be auto-answered (matches the dataset's
# must_not_auto_respond rule); they always go to a human specialist.
MUST_NOT_AUTO_RESPOND_INTENTS = frozenset(
    {"security_incident", "compliance_request", "feature_request", "unclear_request"}
)
ROUTING_REQUIREMENTS = ["FR-07", "FR-09"]


def route_ticket(
    classification: Mapping[str, Any],
    *,
    calibrated_confidence: Mapping[str, float] | None = None,
    min_confidence: float = DEFAULT_MIN_CALIBRATED_CONFIDENCE,
) -> dict[str, Any]:
    """Escalate must-not-auto-respond intents, review uncertain intents, auto-respond otherwise.

    Urgency is purely advisory: it is surfaced to agents for prioritisation and never
    changes the route (high urgency is not complexity; urgency labels depend on
    customer context that is not in the ticket text).
    Raw model self-reported confidence is not treated as calibrated. Until a
    validation-derived confidence mapping is supplied, the safe action is review.
    """
    if not 0 <= min_confidence <= 1:
        raise ValueError("min_confidence must be between 0 and 1")
    intent = classification.get("intent")
    if intent in MUST_NOT_AUTO_RESPOND_INTENTS:
        action, reason = "escalate", f"Intent '{intent}' must never be auto-answered; specialist handling required."
    else:
        intent_score = (calibrated_confidence or {}).get("intent")
        if not (
            isinstance(intent_score, (int, float)) and not isinstance(intent_score, bool) and 0 <= intent_score <= 1
        ):
            action, reason = "review", "Calibrated intent confidence is unavailable; human review required."
        elif intent_score < min_confidence:
            action, reason = "review", "Calibrated intent confidence is below the routing threshold."
        else:
            action, reason = "auto_respond", "Calibrated intent confidence meets the routing threshold."
    return {
        "route": action,
        "action": action,
        "reason": reason,
        "threshold_applied": min_confidence,
        "calibrated_confidence": dict(calibrated_confidence or {}),
        "router_version": ROUTER_VERSION,
    }
