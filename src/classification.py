"""Intent and urgency classification through the configured OpenRouter model."""

from __future__ import annotations

import json
import os
from typing import Any, Mapping

import requests
from dotenv import load_dotenv

from src.tickets import NormalizedTicket, PROJECT_ROOT


load_dotenv(PROJECT_ROOT / ".env")

INTENT_LABELS = frozenset(
    {
        "account_access", "api_key_issue", "api_usage_question",
        "authentication_failure", "billing_query", "compliance_request",
        "configuration_help", "data_export", "data_residency", "database_issue",
        "deployment_failure", "feature_request", "integration_help", "onboarding",
        "performance_degradation", "quota_or_overage", "rate_limit",
        "rollback_request", "security_incident", "sso_configuration",
        "unclear_request", "webhook_issue",
    }
)
URGENCY_LABELS = frozenset({"low", "medium", "high"})
CLASSIFIER_PROMPT_VERSION = "PR-03-v2"


def _confidence(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} confidence must be a number between 0 and 1")
    score = float(value)
    if not 0 <= score <= 1:
        raise ValueError(f"{field} confidence must be a number between 0 and 1")
    return score


def validate_classification(
    value: Mapping[str, Any], *, ticket: NormalizedTicket | None = None
) -> dict[str, Any]:
    """Validate model-produced labels, evidence, ambiguity, and raw scores.

    ``urgency_ambiguous`` is required model output. It is not read from the input
    ticket or from evaluation-only annotations.
    """
    intent = value.get("intent")
    urgency = value.get("urgency")
    if intent not in INTENT_LABELS:
        raise ValueError(f"Unsupported intent label: {intent!r}")
    if urgency not in URGENCY_LABELS:
        raise ValueError(f"Unsupported urgency label: {urgency!r}")
    evidence = value.get("urgency_evidence")
    if not isinstance(evidence, str):
        raise ValueError("urgency_evidence must be a string")
    ambiguous = value.get("urgency_ambiguous")
    if not isinstance(ambiguous, bool):
        raise ValueError("urgency_ambiguous must be a boolean")
    evidence_valid = True
    if ticket is not None and evidence.strip():
        normalized_evidence = " ".join(evidence.casefold().split())
        normalized_ticket_text = " ".join(
            f"{ticket.subject} {ticket.body}".casefold().split()
        )
        evidence_valid = normalized_evidence in normalized_ticket_text
    return {
        "intent": intent,
        "intent_confidence": _confidence(value.get("intent_confidence"), "intent"),
        "urgency": urgency,
        "urgency_confidence": _confidence(value.get("urgency_confidence"), "urgency"),
        "confidence_kind": "raw_model_estimate",
        "urgency_evidence": evidence.strip(),
        "urgency_evidence_valid": evidence_valid,
        "urgency_ambiguous": ambiguous,
        "model_name": value.get("model_name"),
        "model_version": value.get("model_version"),
        "prompt_version": CLASSIFIER_PROMPT_VERSION,
    }


def _ticket_payload(ticket: NormalizedTicket) -> dict[str, Any]:
    return ticket.to_dict()


def classify_ticket(
    ticket: NormalizedTicket,
    *,
    model: str | None = None,
    api_key: str | None = None,
    endpoint: str | None = None,
    requester: Any = requests,
) -> dict[str, Any]:
    """Classify one normalized ticket; the model infers urgency ambiguity itself.

    Evaluation-only labels and any ambiguity annotation are never sent as ticket
    input. The model returns its own ``urgency_ambiguous`` assessment.
    """
    key = api_key or os.getenv("OPENROUTER_API_KEY")
    model_name = model or os.getenv("MODEL_NAME")
    if not key or key == "your_key_here":
        raise RuntimeError("OPENROUTER_API_KEY is missing from the project .env file")
    if not model_name:
        raise RuntimeError("MODEL_NAME is missing from the project .env file")

    prompt = (
        "Classify the support ticket for intent and urgency. Return only one JSON object "
        "with keys intent, intent_confidence, urgency, urgency_confidence, "
        "urgency_evidence, urgency_ambiguous. Intent must "
        f"be one of: {', '.join(sorted(INTENT_LABELS))}. Urgency must be low, medium, "
        "or high. Confidence values are your raw estimates from 0 to 1, not calibrated "
        "probabilities. Urgency means how soon action is needed to prevent material "
        "harm or meet a consequential deadline; assess current impact and time-to-harm. "
        "High means immediate action to contain active credential compromise, data "
        "loss/corruption, critical production unavailability or severe customer impact, "
        "or an imminent consequential deadline. Medium means a real current issue but "
        "limited scope, a workaround, or no evidence of immediate/irreversible harm. "
        "Low means no current material harm or consequential near-term deadline, such "
        "as routine questions, planned work, feature requests, or minor issues. The "
        "word urgent alone is not enough: if impact/timing is unclear, use medium and "
        "lower confidence. Do not use customer tier, expected route, or historical "
        "outcome as a proxy. If urgency cannot be distinguished from ticket evidence, "
        "or the text contains competing urgency signals, set urgency_ambiguous true "
        "and lower urgency_confidence. Set it false only when the text supports a "
        "clear urgency judgment. urgency_evidence must be a short exact excerpt "
        "supporting the urgency judgment, or empty when choosing low because no "
        "impact/deadline is stated. Classify from the ticket text and "
        "context only. Ticket JSON follows:\n"
        + json.dumps(_ticket_payload(ticket), ensure_ascii=False)
    )
    response = requester.post(
        endpoint or os.getenv(
            "OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions"
        ),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        },
        timeout=60,
    )
    response.raise_for_status()
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = "".join(item.get("text", "") for item in content if isinstance(item, dict))
    parsed = json.loads(content)
    if not isinstance(parsed, Mapping):
        raise ValueError("Classifier response must be a JSON object")
    parsed = dict(parsed)
    parsed["model_name"] = result.get("model", model_name)
    return validate_classification(parsed, ticket=ticket)
