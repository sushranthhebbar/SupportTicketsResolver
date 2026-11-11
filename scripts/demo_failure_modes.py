"""Induce each failure condition in acceptance criterion A11 and show the system degrading.

Conditions: model provider disconnected entirely, provider rejecting the key, provider
timeout, rate limiting (HTTP 429), no retrieval hit, and a malformed ticket in the input.
Disconnection and the bad key are induced for real; timeout and 429 use stub HTTP
responses because they cannot be forced on demand. Decisions go to a throwaway database.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.answering import draft_grounded_reply
from src.evaluation import run_evaluation
from src.pipeline import process_ticket
from src.tickets import normalize_ticket

TMP = Path(tempfile.mkdtemp())
DB = f"sqlite:///{TMP / 'failure_demo.db'}"
SOURCE = {"doc_id": "DOC-API-001", "title": "Rate limits", "passage": "Requests are limited per minute."}
RAW = {
    "channel": "email", "subject": "Rate limits", "body": "How do API rate limits work?",
    "received_at": "2026-11-11T09:00:00Z",
}
CLASSIFICATION = {
    "intent": "rate_limit", "intent_confidence": 0.9, "urgency": "low", "urgency_confidence": 0.9,
    "urgency_evidence": "", "urgency_evidence_valid": True, "urgency_ambiguous": False,
}


def ticket(ticket_id):
    return normalize_ticket({"ticket_id": ticket_id, **RAW})


class Stub:
    def __init__(self, status=None, error=None):
        self.status, self.error = status, error

    def post(self, *args, **kwargs):
        if self.error:
            raise self.error
        response = requests.Response()
        response.status_code = self.status
        response.headers["Retry-After"] = "0"
        return response


def show(label, outcome):
    print(f"{label:48s} -> {outcome}")


def main() -> int:
    dataset = TMP / "tickets.json"
    dataset.write_text(json.dumps([
        {**RAW, "ticket_id": f"FM-00{i}", "labels": {"intent": "rate_limit", "urgency": "low"}} for i in (1, 2)
    ]))

    original_url = os.environ.get("MODEL_API_URL")
    print("1. Provider disconnected entirely (unreachable address), harness run of 2 tickets")
    os.environ["MODEL_API_URL"] = "http://127.0.0.1:9/v1/chat/completions"
    run_evaluation(dataset, TMP / "out.jsonl", lambda t: process_ticket(t, database_url=DB, generate_answer=True))
    rows_ = [json.loads(line) for line in (TMP / "out.jsonl").read_text().splitlines()]
    show("run finished, report written", f"rows={len(rows_)} errors={sum(1 for r in rows_ if r['error'])}")
    rows = [json.loads(line) for line in (TMP / "out.jsonl").read_text().splitlines()]
    show("per-ticket error recorded", rows[0]["error"]["type"])
    result = process_ticket(ticket("FM-010"), classifier=lambda _t: CLASSIFICATION, database_url=DB, retriever=lambda _q: [SOURCE])
    show("provider down at drafting stage (live)", f"answer_status={result['answer_status']} route={result['route']} next={result['recommended_next_step']}")

    print("\n2. Provider rejects the key (live call, wrong key)")
    os.environ["MODEL_API_URL"] = original_url or ""
    if not original_url:
        os.environ.pop("MODEL_API_URL")
    bad = draft_grounded_reply(ticket("FM-020"), [SOURCE], api_key="bad-key-for-test-0000")
    show("draft with a rejected key", f"answer_status={bad['answer_status']} guardrail={list(bad['guardrail_results'])}")

    print("\n3. Provider timeout and rate limiting (stubbed HTTP)")
    t = draft_grounded_reply(ticket("FM-030"), [SOURCE], api_key="k" * 20, model="m", requester=Stub(error=requests.Timeout()))
    show("timeout", f"answer_status={t['answer_status']} next={t['recommended_next_step']}")
    r = draft_grounded_reply(ticket("FM-031"), [SOURCE], api_key="k" * 20, model="m", requester=Stub(status=429))
    show("HTTP 429 after retries", f"answer_status={r['answer_status']} next={r['recommended_next_step']}")

    print("\n4. No retrieval hit")
    n = process_ticket(ticket("FM-040"), classifier=lambda _t: CLASSIFICATION, database_url=DB, retriever=lambda _q: [])
    show("retriever returns nothing", f"answer_status={n['answer_status']} route={n['route']} action={n['action']}")
    e = process_ticket(ticket("FM-041"), classifier=lambda _t: CLASSIFICATION, database_url=DB, retriever=lambda _q: 1 / 0)
    show("retriever raises", f"answer_status={e['answer_status']} route={e['route']}")

    print("\n5. Malformed input")
    bad_set = TMP / "bad.json"
    bad_set.write_text(json.dumps([
        {**RAW, "ticket_id": "FM-050", "labels": {"intent": "rate_limit", "urgency": "low"}},
        {"ticket_id": "FM-051", "channel": "fax", "subject": "", "body": ""},
        {**RAW, "ticket_id": "FM-052", "labels": {"intent": "rate_limit", "urgency": "low"}},
    ]))
    try:
        report = run_evaluation(bad_set, TMP / "bad_out.jsonl", lambda t: {"route": "review", "intent": "rate_limit", "urgency": "low"})
        rejected = report["run_info"]["rejected_tickets"]
        show("one malformed ticket in a file of three", f"run completed, rejected={[(r['ticket_id'], r['reason']) for r in rejected]}")
    except Exception as exc:  # noqa: BLE001
        show("one malformed ticket in a file of three", f"RUN STOPPED: {type(exc).__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
