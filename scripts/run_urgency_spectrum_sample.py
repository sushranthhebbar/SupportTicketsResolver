"""Run a diverse PR-03 v2 sample, keeping reference labels offline."""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import process_ticket
from src.tickets import load_ticket_records


SOURCE = PROJECT_ROOT / "evaluation" / "data" / "development_tickets.json"
OUTPUT = PROJECT_ROOT / "evaluation" / "results" / "urgency_spectrum_development.jsonl"
REPORT = PROJECT_ROOT / "evaluation" / "results" / "urgency_spectrum_development.report.json"

# Eighteen varied, distinct-text examples spanning high/medium/low annotations.
SPECTRUM_IDS = [
    "DEV-0139", "DEV-0460", "DEV-0225", "DEV-0180", "DEV-0484", "DEV-0452",
    "DEV-0039", "DEV-0088", "DEV-0302", "DEV-0491", "DEV-0029", "DEV-0013",
    "DEV-0194", "DEV-0241", "DEV-0010", "DEV-0413", "DEV-0420", "DEV-0463",
]

# Each pair has identical normalized subject/body text but conflicting source labels.
CONFLICT_PAIRS = [
    ("DEV-0015", "DEV-0210"),
    ("DEV-0009", "DEV-0122"),
    ("DEV-0026", "DEV-0055"),
    ("DEV-0059", "DEV-0433"),
    ("DEV-0199", "DEV-0457"),
    ("DEV-0147", "DEV-0412"),
]
SAMPLE_IDS = SPECTRUM_IDS + [ticket_id for pair in CONFLICT_PAIRS for ticket_id in pair]


def _text_key(record: dict[str, Any]) -> str:
    text = f"{record.get('subject', '')} {record.get('body', '')}"
    return " ".join(text.casefold().split())


def main() -> int:
    records = load_ticket_records(SOURCE)
    by_id = {record.ticket.ticket_id: record for record in records}
    missing = sorted(set(SAMPLE_IDS) - by_id.keys())
    if missing:
        print(f"Sample IDs missing from source: {missing}", file=sys.stderr)
        return 1
    selected = [by_id[ticket_id] for ticket_id in SAMPLE_IDS]
    if len(set(SAMPLE_IDS)) != 30:
        print("Sample selection must contain 30 unique ticket IDs.", file=sys.stderr)
        return 1
    for first_id, second_id in CONFLICT_PAIRS:
        first, second = by_id[first_id], by_id[second_id]
        if (
            _text_key(first.ticket.to_dict()) != _text_key(second.ticket.to_dict())
            or first.labels.get("urgency") == second.labels.get("urgency")
        ):
            print(f"Invalid conflicting-text pair: {first_id}, {second_id}", file=sys.stderr)
            return 1

    all_text_labels: dict[str, set[str]] = defaultdict(set)
    for record in records:
        label = record.labels.get("urgency")
        if isinstance(label, str):
            all_text_labels[_text_key(record.ticket.to_dict())].add(label)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    routes: Counter[str] = Counter()
    ambiguity_count = supported_evidence_count = successful = 0
    expected_matches = comparable = 0
    predictions_by_text: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rows: list[dict[str, Any]] = []
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as file:
        for index, record in enumerate(selected, 1):
            try:
                prediction = process_ticket(record.ticket, generate_answer=False)
                successful += 1
                route = prediction["route"]
                routes[route] += 1
                ambiguity_count += bool(prediction.get("urgency_ambiguous"))
                supported_evidence_count += bool(prediction.get("urgency_evidence_valid"))
                expected = record.labels.get("urgency")
                if isinstance(expected, str):
                    comparable += 1
                    expected_matches += prediction.get("urgency") == expected
                row = {
                    "ticket_id": record.ticket.ticket_id,
                    "intent": prediction.get("intent"),
                    "intent_confidence_raw": prediction.get("intent_confidence"),
                    "urgency": prediction.get("urgency"),
                    "urgency_confidence_raw": prediction.get("urgency_confidence"),
                    "urgency_evidence": prediction.get("urgency_evidence"),
                    "urgency_evidence_valid": prediction.get("urgency_evidence_valid"),
                    "urgency_ambiguous": prediction.get("urgency_ambiguous"),
                    "route": route,
                    "reason": prediction.get("reason"),
                    "reference_urgency_offline_only": expected,
                    "reference_text_labels_conflict": len(all_text_labels[_text_key(record.ticket.to_dict())]) > 1,
                    "model": prediction.get("model_name"),
                    "prompt_version": prediction.get("prompt_version"),
                    "error": None,
                }
                predictions_by_text[_text_key(record.ticket.to_dict())].append(row)
            except Exception as exc:  # Keep the full sample running per ticket.
                row = {
                    "ticket_id": record.ticket.ticket_id,
                    "reference_urgency_offline_only": record.labels.get("urgency"),
                    "reference_text_labels_conflict": len(all_text_labels[_text_key(record.ticket.to_dict())]) > 1,
                    "route": None,
                    "error": {"type": type(exc).__name__, "message": str(exc)},
                }
            rows.append(row)
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
            file.flush()
            print(f"Processed {index}/{len(selected)}: {record.ticket.ticket_id}")

    repeated_prediction_disagreements = []
    for key, group in predictions_by_text.items():
        predicted = {row.get("urgency") for row in group}
        if len(group) > 1 and len(predicted) > 1:
            repeated_prediction_disagreements.append(
                {
                    "ticket_ids": [row["ticket_id"] for row in group],
                    "predicted_urgencies": sorted(str(value) for value in predicted),
                }
            )

    report = {
        "sample_info": {
            "source_path": str(SOURCE),
            "results_path": str(OUTPUT),
            "tickets_selected": len(selected),
            "tickets_processed": successful,
            "errors": len(selected) - successful,
            "selection": "18 diverse tickets plus 6 identical-text pairs with conflicting reference urgency labels.",
            "reference_labels_sent_to_classifier": False,
        },
        "observations": {
            "route_counts": dict(sorted(routes.items())),
            "classifier_marked_urgency_ambiguous": ambiguity_count,
            "evidence_quotes_supported_by_ticket": supported_evidence_count,
            "raw_match_to_supplied_reference_labels": {
                "matches": expected_matches,
                "compared": comparable,
                "note": "Descriptive only. The sample intentionally includes contradictory reference labels; this is not a standalone quality score.",
            },
            "reference_conflict_tickets_in_sample": sum(
                row.get("reference_text_labels_conflict", False) for row in rows
            ),
            "identical_text_prediction_disagreements": repeated_prediction_disagreements,
        },
        "results_path": str(OUTPUT),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Completed {successful}/{len(selected)}; route counts: {dict(routes)}")
    print(f"Report: {REPORT}")
    return 0 if successful == len(selected) else 1


if __name__ == "__main__":
    raise SystemExit(main())
