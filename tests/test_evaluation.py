import json

import pytest

from src.evaluation import run_evaluation


def _record(ticket_id, *, intent, urgency, route, answerable, doc_ids, fcr):
    return {
        "ticket_id": ticket_id,
        "channel": "email",
        "subject": "Need help",
        "body": "A support question.",
        "received_at": "2026-03-01T12:00:00Z",
        "customer_id": "CUST-1",
        "customer_name": "Example Customer",
        "customer_tier": "standard",
        "customer_region": "north_america",
        "language_fluency": "fluent",
        "labels": {
            "intent": intent,
            "urgency": urgency,
            "expected_route": route,
            "answerable_from_docs": answerable,
            "expected_doc_ids": doc_ids,
            "must_not_auto_respond": False,
        },
        "history": {
            "first_contact_resolution": fcr,
            "resolution_time_minutes": 30,
            "csat_rating": 4,
            "escalated": not fcr,
            "repeat_contact": False,
        },
    }


def _write_dataset(path, records):
    path.write_text(json.dumps(records), encoding="utf-8")


def test_run_evaluation_writes_results_and_metrics_without_label_leakage(tmp_path):
    input_path = tmp_path / "tickets.json"
    results_path = tmp_path / "results.jsonl"
    report_path = tmp_path / "metrics.json"
    _write_dataset(
        input_path,
        [
            _record(
                "TEST-1",
                intent="deployment_failure",
                urgency="high",
                route="auto_respond",
                answerable=True,
                doc_ids=["DOC-DEPLOY-001"],
                fcr=True,
            ),
            _record(
                "TEST-2",
                intent="unclear_request",
                urgency="low",
                route="escalate",
                answerable=False,
                doc_ids=[],
                fcr=False,
            ),
        ],
    )
    processor_inputs = []

    def processor(ticket):
        processor_inputs.append(ticket.to_dict())
        if ticket.ticket_id == "TEST-1":
            return {
                "intent": "deployment_failure",
                "urgency": "high",
                "route": "auto_respond",
                "retrieved_sources": [{"doc_id": "DOC-DEPLOY-001"}],
                "citations": [{"doc_id": "DOC-DEPLOY-001"}],
                "latency_seconds": 0.2,
            }
        return {
            "intent": "unclear_request",
            "urgency": "low",
            "route": "escalate",
            "retrieved_sources": [],
            "citations": [],
            "latency_seconds": 0.4,
        }

    report = run_evaluation(
        input_path,
        results_path,
        processor,
        report_path=report_path,
        system_version="test-1",
    )

    output_rows = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines()]
    saved_report = json.loads(report_path.read_text(encoding="utf-8"))

    assert len(output_rows) == 2
    assert all("labels" not in row and "history" not in row for row in processor_inputs)
    assert report["run_info"]["tickets_processed"] == 2
    assert report["run_info"]["processing_errors"] == 0
    assert report["run_info"]["report_path"] == str(report_path)
    assert report["technical"]["routing_accuracy"] == 1.0
    assert report["technical"]["retrieval_hit_rate_on_answerable_tickets"] == 1.0
    assert report["technical"]["citation_document_match_rate"] == 1.0
    assert report["governance"]["urgency_label_conflicts"]["conflicting_duplicate_text_groups"] == 1
    assert report["governance"]["urgency_label_conflicts"]["tickets_in_conflicting_groups"] == 2
    assert report["technical"]["latency_seconds"]["median"] == pytest.approx(0.3)
    assert report["business"]["historical_baseline"]["first_contact_resolution_rate"] == 0.5
    assert report["business"]["system_first_contact_resolution"] is None
    assert saved_report["run_info"]["system_version"] == "test-1"


def test_run_evaluation_records_ticket_errors_and_continues(tmp_path):
    input_path = tmp_path / "tickets.json"
    results_path = tmp_path / "results.jsonl"
    _write_dataset(
        input_path,
        [
            _record(
                "TEST-FAIL",
                intent="unclear_request",
                urgency="medium",
                route="escalate",
                answerable=False,
                doc_ids=[],
                fcr=False,
            ),
            _record(
                "TEST-OK",
                intent="unclear_request",
                urgency="medium",
                route="escalate",
                answerable=False,
                doc_ids=[],
                fcr=False,
            ),
        ],
    )

    def processor(ticket):
        if ticket.ticket_id == "TEST-FAIL":
            raise RuntimeError("temporary provider failure")
        return {"intent": "unclear_request", "urgency": "medium", "route": "escalate"}

    report = run_evaluation(input_path, results_path, processor)
    output_rows = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines()]

    assert report["run_info"]["tickets_in_input"] == 2
    assert report["run_info"]["tickets_processed"] == 1
    assert report["run_info"]["processing_errors"] == 1
    assert output_rows[0]["error"]["type"] == "RuntimeError"
    assert output_rows[1]["result"]["route"] == "escalate"
