import json

import pytest

from src.classification import classify_ticket, validate_classification
from src.logging_store import count_decisions
from src.pipeline import process_ticket
from src.routing import route_ticket
from src.tickets import normalize_ticket


def _ticket():
    return normalize_ticket(
        {
            "ticket_id": "T-1",
            "channel": "chat",
            "body": "Production API is returning errors.",
            "received_at": "2026-01-01T00:00:00Z",
            "labels": {"intent": "secret-label"},
        }
    )


def _classification(**overrides):
    value = {
        "intent": "deployment_failure",
        "intent_confidence": 0.91,
        "urgency": "medium",
        "urgency_confidence": 0.84,
        "urgency_evidence": "Production API is returning errors.",
        "urgency_evidence_valid": True,
        "urgency_ambiguous": False,
    }
    value.update(overrides)
    return value


def test_validate_classification_rejects_bad_labels_and_scores():
    with pytest.raises(ValueError, match="Unsupported intent"):
        validate_classification(_classification(intent="other"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        validate_classification(_classification(urgency_confidence=1.1))


def test_classifier_sends_only_normalized_ticket_and_parses_response():
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "model": "test-model",
                "choices": [{"message": {"content": json.dumps(_classification())}}],
            }

    class Requester:
        payload = None

        def post(self, _url, **kwargs):
            self.payload = kwargs["json"]
            return Response()

    requester = Requester()
    result = classify_ticket(
        _ticket(), model="test-model", api_key="test-key", requester=requester
    )
    assert result["intent"] == "deployment_failure"
    assert result["confidence_kind"] == "raw_model_estimate"
    assert result["urgency_evidence_valid"] is True
    prompt = requester.payload["messages"][0]["content"]
    assert "secret-label" not in prompt
    assert '"ticket_id": "T-1"' in prompt
    assert "urgency_ambiguous" not in _ticket().to_dict()
    ticket_payload = json.loads(prompt.split("Ticket JSON follows:\n", 1)[1])
    assert "urgency_ambiguous" not in ticket_payload
    assert "urgency_ambiguous" in prompt.split("Ticket JSON follows:\n", 1)[0]


def test_routing_ignores_urgency_and_requires_calibration():
    assert route_ticket(_classification(urgency="high"))["route"] == "review"
    assert route_ticket(
        _classification(urgency="high"), calibrated_confidence={"intent": 0.9}
    )["route"] == "auto_respond"
    assert route_ticket(_classification(intent="security_incident"))["route"] == "escalate"
    assert route_ticket(_classification())["route"] == "review"
    calibrated = {"intent": 0.9, "urgency": 0.82}
    assert route_ticket(_classification(), calibrated_confidence=calibrated)["route"] == "auto_respond"
    # Urgency confidence is advisory and does not gate auto-response; intent does.
    assert route_ticket(
        _classification(), calibrated_confidence={"intent": 0.9, "urgency": 0.2}
    )["route"] == "auto_respond"
    assert route_ticket(
        _classification(), calibrated_confidence={"intent": 0.79, "urgency": 0.99}
    )["route"] == "review"
    assert route_ticket(_classification(), calibrated_confidence={"urgency": 0.99})["route"] == "review"


def test_ambiguous_or_unsupported_urgency_does_not_change_route():
    calibrated = {"intent": 0.99, "urgency": 0.1}
    assert route_ticket(
        _classification(urgency_ambiguous=True), calibrated_confidence=calibrated
    )["route"] == "auto_respond"
    assert route_ticket(
        _classification(urgency_evidence_valid=False), calibrated_confidence=calibrated
    )["route"] == "auto_respond"
    unsupported = validate_classification(
        _classification(urgency_evidence="The whole service is down."), ticket=_ticket()
    )
    assert unsupported["urgency_evidence_valid"] is False
    assert route_ticket(unsupported, calibrated_confidence=calibrated)["route"] == "auto_respond"


def test_pipeline_logs_classification_and_routing(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'decisions.db'}"
    result = process_ticket(
        _ticket(),
        classifier=lambda _ticket: _classification(),
        calibrated_confidence={"intent": 0.9, "urgency": 0.9},
        database_url=database_url,
        generate_answer=False,
    )
    assert result["route"] == "auto_respond"
    assert count_decisions(database_url) == 2


def test_must_not_auto_respond_intents_always_escalate():
    calibrated = {"intent": 0.99, "urgency": 0.99}
    for intent in ("security_incident", "compliance_request", "feature_request", "unclear_request"):
        for overrides in ({}, {"urgency": "low"}, {"urgency_ambiguous": True}):
            result = route_ticket(
                _classification(intent=intent, **overrides), calibrated_confidence=calibrated
            )
            assert result["route"] == "escalate", (intent, overrides)
    assert route_ticket(_classification(), calibrated_confidence=calibrated)["route"] == "auto_respond"
