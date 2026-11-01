"""Classify and log a 20-ticket sample for manual decision inspection."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import process_ticket
from src.tickets import load_ticket_records


def main() -> int:
    source = PROJECT_ROOT / "evaluation" / "data" / "validation_tickets.json"
    output = PROJECT_ROOT / "evaluation" / "results" / "classification_sample_20.jsonl"
    records = load_ticket_records(source)
    if len(records) < 20:
        print(f"Need at least 20 tickets in {source}; found {len(records)}.")
        return 1

    output.parent.mkdir(parents=True, exist_ok=True)
    routes: Counter[str] = Counter()
    with output.open("w", encoding="utf-8", newline="\n") as file:
        for record in records[:20]:
            result = process_ticket(record.ticket, generate_answer=False)
            routes[result["route"]] += 1
            file.write(
                json.dumps(
                    {
                        "ticket_id": record.ticket.ticket_id,
                        "intent": result["intent"],
                        "intent_confidence": result["intent_confidence"],
                        "urgency": result["urgency"],
                        "urgency_confidence": result["urgency_confidence"],
                        "confidence_kind": result["confidence_kind"],
                        "route": result["route"],
                        "reason": result["reason"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    print(f"Processed 20 tickets. Route counts: {dict(routes)}")
    print(f"Inspect decisions in: {output}")
    print("Each ticket has classification and routing rows in storage/decisions.db.")
    print("Non-urgent tickets remain in review until a validation-derived calibrator is configured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
