import pytest

from src.calibration import (
    CalibrationArtifact,
    build_artifact,
    fit_isotonic,
    precision_at_threshold,
    predict_isotonic,
    split_for_text,
    text_key,
)
from src.pipeline import process_ticket
from src.tickets import normalize_ticket


def test_isotonic_pools_violations_and_is_monotone():
    blocks = fit_isotonic([0.5, 0.6, 0.7, 0.9, 0.9], [True, False, False, True, True])
    values = [b["value"] for b in blocks]
    assert values == sorted(values)
    assert blocks[0]["x_min"] == 0.5 and blocks[0]["x_max"] == 0.7
    assert blocks[0]["value"] == pytest.approx(1 / 3)
    assert blocks[-1]["value"] == 1.0


def test_predict_is_conservative_between_and_outside_blocks():
    blocks = fit_isotonic([0.5, 0.9], [False, True])
    assert predict_isotonic(blocks, 0.2) == 0.0
    assert predict_isotonic(blocks, 0.7) == 0.0  # between blocks takes the lower block
    assert predict_isotonic(blocks, 0.9) == 1.0
    assert predict_isotonic(blocks, 1.0) == 1.0
    with pytest.raises(ValueError):
        predict_isotonic(blocks, 1.5)


def test_small_blocks_are_pooled_so_one_ticket_cannot_set_a_high_value():
    scores = [0.6] * 12 + [0.9] * 12 + [0.98]
    correct = [False] * 8 + [True] * 4 + [True] * 6 + [False] * 6 + [True]
    blocks = fit_isotonic(scores, correct, min_block_n=5)
    assert all(b["n"] >= 5 for b in blocks)
    assert predict_isotonic(blocks, 0.98) == pytest.approx(7 / 13)
    assert [b["value"] for b in blocks] == sorted(b["value"] for b in blocks)
    assert fit_isotonic(scores, correct)[-1]["value"] == 1.0


def test_fit_rejects_invalid_input():
    with pytest.raises(ValueError):
        fit_isotonic([], [])
    with pytest.raises(ValueError):
        fit_isotonic([1.2], [True])


def test_split_is_deterministic_and_text_based():
    key = text_key("Subject", "  Same   text ")
    assert key == text_key("subject", "same text")
    assert split_for_text(key) == split_for_text(key)
    assert {split_for_text(f"text {i}") for i in range(50)} == {"fit", "holdout"}


def test_precision_at_threshold_reports_per_class_sample_size():
    result = precision_at_threshold(["a", "a", "b", "b"], [0.9, 0.9, 0.9, 0.5], [True, False, True, True], 0.8)
    assert result["n_selected"] == 3
    assert result["per_class"]["a"]["precision"] == 0.5
    assert result["per_class"]["a"]["sufficient_sample"] is False
    assert "b" in result["per_class"] and result["per_class"]["b"]["n"] == 1


def _rows(prefix, n, conf, correct):
    return [
        {"ticket_id": f"{prefix}{i}", "intent_pred": "billing_query", "intent_conf": conf,
         "intent_correct": correct, "urgency_pred": "medium", "urgency_conf": conf,
         "urgency_correct": correct}
        for i in range(n)
    ]


def _artifact(correct=True):
    fit = _rows("F", 10, 0.9, correct)
    hold = _rows("H", 5, 0.9, correct)
    return build_artifact(fit, hold, model_name="m", prompt_version="PR-03-v2", version="t-1")


def test_artifact_calibrates_only_matching_model_and_prompt():
    artifact = CalibrationArtifact(_artifact())
    base = {"intent_confidence": 0.9, "urgency_confidence": 0.9, "model_name": "m", "prompt_version": "PR-03-v2"}
    assert artifact.calibrate(base) == {"intent": 1.0, "urgency": 1.0}
    assert artifact.calibrate({**base, "prompt_version": "PR-03-v3"}) is None
    assert artifact.calibrate({**base, "model_name": "other"}) is None
    assert _artifact()["metrics"]["intent"]["holdout"]["n"] == 5


def test_pipeline_uses_configured_artifact_and_falls_back_to_review(tmp_path, monkeypatch):
    import json

    from src.calibration import save_artifact

    path = tmp_path / "cal.json"
    save_artifact(_artifact(), path)
    monkeypatch.setenv("CALIBRATION_ARTIFACT", str(path))
    ticket = normalize_ticket(
        {"ticket_id": "T-1", "channel": "chat", "body": "How do I export my data?",
         "received_at": "2026-01-01T00:00:00Z"}
    )

    def classifier(model="m", prompt="PR-03-v2"):
        return lambda _t: {
            "intent": "billing_query", "intent_confidence": 0.9, "urgency": "low",
            "urgency_confidence": 0.9, "urgency_evidence": "", "urgency_evidence_valid": True,
            "urgency_ambiguous": False, "model_name": model, "prompt_version": prompt,
        }

    db = f"sqlite:///{tmp_path / 'd.db'}"
    kwargs = dict(database_url=db, generate_answer=False)
    matched = process_ticket(ticket, classifier=classifier(), **kwargs)
    assert matched["route"] == "auto_respond" and matched["calibration_version"] == "t-1"
    mismatched = process_ticket(ticket, classifier=classifier(prompt="PR-03-v3"), **kwargs)
    assert mismatched["route"] == "review" and mismatched["calibration_version"] is None
    monkeypatch.delenv("CALIBRATION_ARTIFACT")
    assert process_ticket(ticket, classifier=classifier(), **kwargs)["route"] == "review"


def _record(ticket_id, body):
    from src.tickets import TicketRecord

    return TicketRecord(
        ticket=normalize_ticket(
            {"ticket_id": ticket_id, "channel": "chat", "body": body, "received_at": "2026-01-01T00:00:00Z"}
        ),
        labels={},
        history={},
    )


def test_scenario_split_keeps_paraphrases_together():
    from src.scenarios import scenario_clusters, scenario_split

    records = [
        _record("A1", "log forwarding to our external system stopped last night and has not resumed"),
        _record("A2", "Log forwarding to our external system stopped yesterday night and has not resumed."),
        _record("B1", "invoice shows a charge for a service we never used please check"),
        _record("B2", "invoice shows a charge for a service we never used, can you check"),
        _record("C1", "how do I rotate the signing secret for webhooks"),
    ]
    clusters = scenario_clusters(records)
    assert sorted(map(sorted, clusters)) == [["A1", "A2"], ["B1", "B2"], ["C1"]]
    split = scenario_split(records)
    assert split["A1"] == split["A2"] and split["B1"] == split["B2"]
    assert set(split.values()) <= {"fit", "holdout"}


def test_prompt_v4_adds_intent_definitions_and_unknown_versions_fail(monkeypatch):
    import json as _json

    from src.classification import classify_ticket

    sent = {}

    class Response:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"model": "m", "choices": [{"message": {"content": _json.dumps({
                "intent": "billing_query", "intent_confidence": 0.9, "urgency": "low",
                "urgency_confidence": 0.8, "urgency_evidence": "", "urgency_ambiguous": False})}}]}

    class Requester:
        def post(self, _url, **kwargs):
            sent["prompt"] = kwargs["json"]["messages"][0]["content"]
            return Response()

    ticket = _record("T", "question about my invoice").ticket
    kwargs = dict(api_key="real-key", model="m", endpoint="http://x", requester=Requester())
    v2 = classify_ticket(ticket, prompt_version="PR-03-v2", **kwargs)
    assert "Intent definitions" not in sent["prompt"] and v2["prompt_version"] == "PR-03-v2"
    v4 = classify_ticket(ticket, prompt_version="PR-03-v4", **kwargs)
    assert "Intent definitions" in sent["prompt"] and v4["prompt_version"] == "PR-03-v4"
    default = classify_ticket(ticket, **kwargs)
    assert default["prompt_version"] == "PR-03-v4"  # runtime default
    with pytest.raises(ValueError, match="prompt version"):
        classify_ticket(ticket, prompt_version="PR-03-v9", **kwargs)


def test_mcnemar_exact_matches_known_values():
    import importlib.util
    from pathlib import Path

    spec = importlib.util.spec_from_file_location(
        "compare_prompt_runs", Path(__file__).resolve().parents[1] / "scripts" / "compare_prompt_runs.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.mcnemar_exact(0, 0) == 1.0
    assert module.mcnemar_exact(10, 0) == pytest.approx(2 / 1024)
    assert module.mcnemar_exact(5, 5) == 1.0
