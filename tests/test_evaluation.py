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


def test_urgency_noise_analysis_reports_ceiling_and_adjacent_accuracy():
    from src.evaluation import _urgency_noise_analysis
    from src.tickets import load_ticket_records
    import tempfile, pathlib

    def rec(i, body, urgency):
        r = _record(f"T-{i}", intent="onboarding", urgency=urgency, route="auto_respond",
                    answerable=True, doc_ids=[], fcr=True)
        r["body"] = body
        return r

    data = [rec(1, "same text", "low"), rec(2, "same text", "medium"), rec(3, "same text", "medium"),
            rec(4, "unique one", "high"), rec(5, "unique two", "low")]
    with tempfile.TemporaryDirectory() as folder:
        path = pathlib.Path(folder) / "d.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        records = load_ticket_records(path)
    guesses = ["medium", "medium", "medium", "medium", "high"]
    rows = [{"result": {"urgency": g}, "expected": r.labels} for g, r in zip(guesses, records)]
    out = _urgency_noise_analysis(records, rows)
    assert out["exact_accuracy"] == 2 / 5
    assert out["noise_ceiling_accuracy"] == (2 + 1 + 1) / 5
    assert out["conflict_free_exact_accuracy"] == 0
    assert out["conflicting_text_exact_accuracy"] == 2 / 3
    assert out["within_one_level_accuracy"] == 4 / 5


def test_run_evaluation_resumes_and_retries_failed_tickets(tmp_path):
    records = [
        _record(f"T-{n}", intent="billing_query", urgency="low", route="auto_respond",
                answerable=True, doc_ids=["DOC-1"], fcr=True)
        for n in range(1, 5)
    ]
    input_path = tmp_path / "tickets.json"
    _write_dataset(input_path, records)
    results_path = tmp_path / "results.jsonl"
    calls = []
    fail_once = {"T-2"}

    def processor(ticket):
        calls.append(ticket.ticket_id)
        if ticket.ticket_id in fail_once:
            fail_once.discard(ticket.ticket_id)
            raise RuntimeError("rate limited")
        return {"route": "auto_respond", "intent": "billing_query", "urgency": "low"}

    partial = run_evaluation(input_path, results_path, processor, resume=True, max_new_tickets=2)
    assert partial["run_info"]["complete"] is False
    assert partial["run_info"]["tickets_processed"] == 2
    assert partial["run_info"]["processing_errors"] == 1
    assert not (tmp_path / "results.report.json").exists()

    final = run_evaluation(input_path, results_path, processor, resume=True)
    assert final["run_info"]["tickets_processed"] == 4
    assert final["run_info"]["processing_errors"] == 0
    assert calls == ["T-1", "T-2", "T-2", "T-3", "T-4"]  # T-1 reused, T-2 retried
    rows = [json.loads(line) for line in results_path.read_text(encoding="utf-8").splitlines()]
    assert [row["ticket_id"] for row in rows] == ["T-1", "T-2", "T-3", "T-4"]
