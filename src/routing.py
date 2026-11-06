"""Repeatable routing policy for classified tickets."""

from __future__ import annotations

from typing import Any, Mapping


DEFAULT_MIN_CALIBRATED_CONFIDENCE = 0.80
ROUTER_VERSION = "router-v2"
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
    """Escalate must-not-auto-respond intents and high urgency, review uncertain cases, auto-respond otherwise.

    Raw model self-reported confidence is not treated as calibrated. Until a
    validation-derived confidence mapping is supplied, the safe action is review.
    """
    if not 0 <= min_confidence <= 1:
        raise ValueError("min_confidence must be between 0 and 1")
    intent = classification.get("intent")
    urgency = classification.get("urgency")
    if intent in MUST_NOT_AUTO_RESPOND_INTENTS:
        action, reason = "escalate", f"Intent '{intent}' must never be auto-answered; specialist handling required."
    elif classification.get("urgency_ambiguous", True) or not classification.get(
        "urgency_evidence_valid", False
    ):
        action = "review"
        reason = "Urgency is ambiguous or unsupported by ticket text; human review required."
    elif urgency == "high":
        action, reason = "escalate", "High urgency requires immediate human attention."
    else:
        scores = calibrated_confidence or {}
        intent_score = scores.get("intent")
        urgency_score = scores.get("urgency")
        valid = all(
            isinstance(score, (int, float)) and not isinstance(score, bool) and 0 <= score <= 1
            for score in (intent_score, urgency_score)
        )
        if not valid:
            action, reason = "review", "Calibrated confidence is unavailable; human review required."
        elif min(intent_score, urgency_score) < min_confidence:
            action, reason = "review", "Calibrated confidence is below the routing threshold."
        else:
            action, reason = "auto_respond", "Both calibrated confidence scores meet the routing threshold."
    return {
        "route": action,
        "action": action,
        "reason": reason,
        "threshold_applied": min_confidence,
        "calibrated_confidence": dict(calibrated_confidence or {}),
        "router_version": ROUTER_VERSION,
    }
