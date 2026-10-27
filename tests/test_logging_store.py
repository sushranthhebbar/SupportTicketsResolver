import json

import pytest

from src.logging_store import count_decisions, initialize_database, log_decision


def test_decision_log_round_trip(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'decisions.db'}"
    path = initialize_database(database_url)

    decision_id = log_decision(
        {
            "decision_id": "decision-test-1",
            "ticket_id": "ticket-test-1",
            "stage": "classification",
            "action_taken": "review",
            "reason": "Confidence below threshold",
            "sources_used": ["DOC-001"],
            "guardrail_results": {"passed": True},
        },
        database_url,
    )

    assert path.exists()
    assert decision_id == "decision-test-1"
    assert count_decisions(database_url) == 1

    import sqlite3

    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT ticket_id, sources_used_json, guardrail_results_json "
            "FROM decisions WHERE decision_id = ?",
            (decision_id,),
        ).fetchone()

    assert row[0] == "ticket-test-1"
    assert json.loads(row[1]) == ["DOC-001"]
    assert json.loads(row[2]) == {"passed": True}


@pytest.mark.parametrize("missing_field", ["ticket_id", "stage", "action_taken", "reason"])
def test_decision_log_requires_core_fields(tmp_path, missing_field):
    database_url = f"sqlite:///{tmp_path / 'decisions.db'}"
    decision = {
        "ticket_id": "ticket-test-1",
        "stage": "classification",
        "action_taken": "review",
        "reason": "Needs human review",
    }
    decision[missing_field] = ""

    with pytest.raises(ValueError, match=missing_field):
        log_decision(decision, database_url)
