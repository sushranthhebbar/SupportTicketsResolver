import json

import requests

from src.answering import draft_grounded_reply
from src.logging_store import count_decisions
from src.pipeline import process_ticket
from src.tickets import normalize_ticket


SOURCE = {
    "doc_id": "DOC-HELP-001",
    "title": "API setup",
    "passage": "Create a key in the account settings and assign the required permissions.",
}


def _ticket():
    return normalize_ticket(
        {
            "ticket_id": "T-ANSWER-1",
            "channel": "email",
            "subject": "API key setup",
            "body": "How do I create a key?",
            "received_at": "2026-01-01T00:00:00Z",
        }
    )


def _payload(**overrides):
    value = {
        "sufficient_evidence": True,
        "draft": "Create a key in account settings and assign permissions [DOC-HELP-001].",
        "citations": ["DOC-HELP-001"],
        "reason": "The passage describes key creation and permissions.",
        "next_step": "ask_clarification",
    }
    value.update(overrides)
    return value


class _Response:
    def __init__(self, content=None, status=200):
        self.content = content
        self.status = status

    def raise_for_status(self):
        if self.status >= 400:
            response = requests.Response()
            response.status_code = self.status
            raise requests.HTTPError(response=response)

    def json(self):
        return {
            "model": "test-model",
            "choices": [{"message": {"content": json.dumps(self.content)}}],
        }


class _Requester:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.payload = None

    def post(self, _url, **kwargs):
        self.payload = kwargs["json"]
        if self.error:
            raise self.error
        return self.response


def _call(payload, sources=None, requester=None):
    return draft_grounded_reply(
        _ticket(),
        [SOURCE] if sources is None else sources,
        model="test-model",
        api_key="test-key",
        requester=requester or _Requester(_Response(payload)),
    )


def test_no_retrieved_sources_declines_without_calling_provider():
    requester = _Requester(error=AssertionError("provider must not be called"))
    result = _call(_payload(), sources=[], requester=requester)
    assert result["answer_status"] == "needs_human"
    assert result["answer"] == ""
    assert result["recommended_next_step"] == "ask_clarification"
    assert requester.payload is None
    malformed = draft_grounded_reply(_ticket(), None, requester=requester)  # type: ignore[arg-type]
    assert malformed["answer_status"] == "needs_human"
    assert "malformed_input" in malformed["guardrail_results"]


def test_insufficient_evidence_returns_no_confirmed_draft():
    result = _call(
        _payload(
            sufficient_evidence=False,
            draft="",
            citations=[],
            reason="The docs do not cover account-specific status.",
            next_step="ask_clarification",
        )
    )
    assert result["answer_status"] == "needs_human"
    assert result["answer"] == ""
    assert result["recommended_next_step"] == "ask_clarification"


def test_grounded_draft_requires_retrieved_inline_citations():
    result = _call(_payload())
    assert result["answer_status"] == "draft_ready"
    assert result["citations"] == ["DOC-HELP-001"]
    assert result["recommended_next_step"] == "agent_review"
    assert "[DOC-HELP-001]" in result["answer"]

    bad_citation = _call(
        _payload(
            draft="Create a key [DOC-NOT-RETRIEVED].",
            citations=["DOC-NOT-RETRIEVED"],
        )
    )
    assert bad_citation["answer_status"] == "needs_human"
    assert bad_citation["answer"] == ""


def test_unsafe_credential_like_answer_is_blocked():
    result = _call(
        _payload(draft="Use this key: sk-abcdefghijklmnop123 [DOC-HELP-001].")
    )
    assert result["answer_status"] == "blocked"
    assert result["action"] == "block"
    assert result["answer"] == ""


def test_malformed_provider_json_fails_safely():
    class MalformedResponse(_Response):
        def json(self):
            return {"choices": [{"message": {"content": "{bad json"}}]}

    result = _call(
        _payload(), requester=_Requester(MalformedResponse())
    )
    assert result["answer_status"] == "needs_human"
    assert result["answer"] == ""
    assert "malformed_output" in result["guardrail_results"]


def test_timeout_and_rate_limit_return_retryable_safe_results():
    timeout = _call(_payload(), requester=_Requester(error=requests.Timeout()))
    assert timeout["guardrail_results"]["provider_timeout"]["passed"] is False

    limited = _call(_payload(), requester=_Requester(_Response(status=429)))
    assert limited["guardrail_results"]["provider_rate_limit"]["passed"] is False
    assert limited["recommended_next_step"] == "retry_later"


def test_pipeline_logs_grounded_draft_and_sources(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'answer-decisions.db'}"
    classification = {
        "intent": "api_usage_question",
        "intent_confidence": 0.95,
        "urgency": "low",
        "urgency_confidence": 0.94,
        "urgency_evidence": "",
        "urgency_evidence_valid": True,
        "urgency_ambiguous": False,
        "model_name": "test-classifier",
    }
    draft = {
        "answer_status": "draft_ready",
        "answer": "Create a key [DOC-HELP-001].",
        "citations": ["DOC-HELP-001"],
        "reason": "Supported by the retrieved setup article.",
        "recommended_next_step": "agent_review",
        "action": "draft_ready",
        "guardrail_results": {"citation_validation": {"passed": True}},
        "prompt_version": "PR-02-v1",
        "model_name": "test-answerer",
    }
    result = process_ticket(
        _ticket(),
        classifier=lambda _ticket: classification,
        calibrated_confidence={"intent": 0.95, "urgency": 0.94},
        database_url=database_url,
        retriever=lambda _query: [SOURCE],
        answerer=lambda _ticket, _sources: draft,
    )
    assert result["answer_status"] == "draft_ready"
    assert result["route"] == "auto_respond"
    assert result["action"] == "auto_respond"
    assert result["retrieved_sources"][0]["doc_id"] == "DOC-HELP-001"
    assert count_decisions(database_url) == 3


def test_pipeline_retrieval_failure_returns_review_result(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'retrieval-failure.db'}"

    def failing_retriever(_query):
        raise RuntimeError("index unavailable")

    result = process_ticket(
        _ticket(),
        classifier=lambda _ticket: {
            "intent": "api_usage_question",
            "intent_confidence": 0.9,
            "urgency": "low",
            "urgency_confidence": 0.9,
            "urgency_evidence": "",
            "urgency_evidence_valid": True,
            "urgency_ambiguous": False,
        },
        database_url=database_url,
        retriever=failing_retriever,
    )
    assert result["answer_status"] == "needs_human"
    assert result["route"] == "review"
    assert count_decisions(database_url) == 3
