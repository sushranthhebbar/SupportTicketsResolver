"""Intent and urgency classification through the configured OpenRouter model."""

from __future__ import annotations

import json
import os
from typing import Any, Mapping

import requests
from dotenv import load_dotenv

from src.model_provider import (
    has_configured_api_key,
    post_with_rate_limit_retry,
    resolve_api_key,
    resolve_api_url,
)
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
SUPPORTED_PROMPT_VERSIONS = frozenset({"PR-03-v2", "PR-03-v4"})
# PR-03-v4 is PR-03-v2 plus these intent definitions and tie-break rules (urgency text
# unchanged). It stays an experiment until it passes the criteria in
# docs/development_error_analysis.md (H1); the runtime default remains PR-03-v2.
INTENT_DEFINITIONS = (
    "Intent definitions (choose the intent naming the customer's primary request or the "
    "capability that is failing): "
    "account_access = a person cannot log in, is locked out, or needs a user account or its "
    "access recovered, added, removed or changed; "
    "api_key_issue = creating, rotating, revoking, scoping or losing API keys, or a key that "
    "stopped working; "
    "api_usage_question = how to call an API correctly (parameters, pagination, behaviour) "
    "with no failure or limit involved; "
    "authentication_failure = requests or logins rejected (401/403, token or credential "
    "errors) although the credentials should be valid; "
    "billing_query = invoices, charges, pricing, payments or an unexpected bill; "
    "compliance_request = audit evidence, attestations, certifications, access/audit logs "
    "shown to an auditor, retention or legal/regulatory documentation; "
    "configuration_help = how to set up or change settings of a service already in use; "
    "data_export = extracting or downloading the customer's own data in bulk; "
    "data_residency = where data is physically stored or processed, region or location "
    "requirements; "
    "database_issue = failures of the managed database itself (connections, replication, "
    "corruption, restore, locks); "
    "deployment_failure = builds or deployments fail or hang; "
    "feature_request = asks for a capability that does not exist; "
    "integration_help = connecting or forwarding data to an external system (CI, log "
    "forwarding, monitoring, third-party tools) that is not working or being set up; "
    "onboarding = a new customer or team getting started or migrating to the platform; "
    "performance_degradation = the service works but is slow, latency or throughput has "
    "worsened, or resources are exhausted; "
    "quota_or_overage = hitting plan limits or spend caps, throttling caused by a quota, or "
    "overage terms; "
    "rate_limit = HTTP 429 or request-rate limits on the API; "
    "rollback_request = reverting to a previous version, deployment or configuration; "
    "security_incident = suspected or confirmed unauthorized access, exposed or leaked "
    "credentials or keys, data exposure, or an active attack; "
    "sso_configuration = SAML/OIDC/SCIM setup, or SSO login and provisioning problems; "
    "unclear_request = no actionable detail, a bare follow-up, or nothing that fits another "
    "intent; "
    "webhook_issue = webhook delivery, retries, duplicates, signatures or endpoint failures. "
    "Tie-breaks: a failure to forward or sync data to an external system is "
    "integration_help, unless it is specifically about webhook delivery (webhook_issue); a "
    "request for evidence shown to an auditor is compliance_request even if it needs an "
    "export, whereas a request to download one's data for its own sake is data_export; a "
    "rejected key or token is authentication_failure, key management is api_key_issue, and a "
    "key that may have been exposed or misused is security_incident; connection exhaustion "
    "or errors are database_issue, while slowness is performance_degradation; first-time "
    "setup or migration planning is onboarding, while changing settings of a live service is "
    "configuration_help; hitting a limit or cap is quota_or_overage, while a question about "
    "an amount charged is billing_query. "
)


def _confidence(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} confidence must be a number between 0 and 1")
    score = float(value)
    if not 0 <= score <= 1:
        raise ValueError(f"{field} confidence must be a number between 0 and 1")
    return score


def validate_classification(
    value: Mapping[str, Any],
    *,
    ticket: NormalizedTicket | None = None,
    prompt_version: str = CLASSIFIER_PROMPT_VERSION,
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
        "prompt_version": prompt_version,
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
    prompt_version: str = CLASSIFIER_PROMPT_VERSION,
) -> dict[str, Any]:
    """Classify one normalized ticket; the model infers urgency ambiguity itself.

    Evaluation-only labels and any ambiguity annotation are never sent as ticket
    input. The model returns its own ``urgency_ambiguous`` assessment.
    """
    if prompt_version not in SUPPORTED_PROMPT_VERSIONS:
        raise ValueError(f"Unsupported classifier prompt version: {prompt_version!r}")
    key = resolve_api_key(api_key)
    model_name = model or os.getenv("MODEL_NAME")
    if not has_configured_api_key(key):
        raise RuntimeError("MODEL_API_KEY (or a supported legacy provider key) is missing from the project .env file")
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
        "word urgent alone is not enough: "
        "if impact/timing is unclear, use medium and "
        "lower confidence. Do not use customer tier, expected route, or historical "
        "outcome as a proxy. If urgency cannot be distinguished from ticket evidence, "
        "or the text contains competing urgency signals, set urgency_ambiguous true "
        "and lower urgency_confidence. Set it false only when the text supports a "
        "clear urgency judgment. urgency_evidence must be a short exact excerpt "
        "supporting the urgency judgment, or empty when choosing low because no "
        "impact/deadline is stated. Classify from the ticket text and "
        "context only. "
        + (INTENT_DEFINITIONS if prompt_version == "PR-03-v4" else "")
        + "Ticket JSON follows:\n"
        + json.dumps(_ticket_payload(ticket), ensure_ascii=False)
    )
    response = post_with_rate_limit_retry(
        requester,
        resolve_api_url(endpoint),
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
    return validate_classification(parsed, ticket=ticket, prompt_version=prompt_version)
