"""Collect live classifier predictions on development tickets for calibration.

Classification only (no drafting, no decision-log writes). The run is resumable:
tickets already present in the output file are skipped, so it can be repeated
across days to stay inside provider token quotas. Tickets used for prompt tuning
and all validation tickets are excluded so calibration stays independent of them.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.calibration import collection_order, split_for_text, text_key
from src.classification import classify_ticket
from src.tickets import load_ticket_records

DEFAULT_INPUT = PROJECT_ROOT / "evaluation" / "data" / "development_tickets.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "evaluation" / "calibration" / "development_predictions.jsonl"
TUNING_ID_SOURCES = (
    "evaluation/results/development_citation_probe_input.json",
    "evaluation/results/development_citation_probe_v2_16_input.json",
)
TUNING_JSONL_SOURCES = (
    "evaluation/results/urgency_spectrum_development.jsonl",
    "evaluation/results/urgency_pr03_v3_16.jsonl",
)
logger = logging.getLogger("calibration")


def tuning_ticket_ids() -> set[str]:
    ids: set[str] = set()
    for relative in TUNING_ID_SOURCES:
        path = PROJECT_ROOT / relative
        if path.exists():
            for item in json.loads(path.read_text(encoding="utf-8")):
                ids.add(item if isinstance(item, str) else item.get("ticket_id"))
    for relative in TUNING_JSONL_SOURCES:
        path = PROJECT_ROOT / relative
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    ids.add(json.loads(line)["ticket_id"])
    return {ticket_id for ticket_id in ids if ticket_id}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-tickets", type=int, default=100,
                        help="New tickets to classify in this invocation (default 100).")
    parser.add_argument("--request-interval", type=float, default=3.0,
                        help="Minimum seconds between model requests (default 3).")
    parser.add_argument("--retry-errors", action="store_true",
                        help="Re-attempt tickets whose earlier attempt recorded an error.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    os.environ["MODEL_MIN_REQUEST_INTERVAL_SECONDS"] = str(max(0.0, args.request_interval))

    records = load_ticket_records(args.input)
    excluded = tuning_ticket_ids()
    excluded_texts = {
        text_key(r.ticket.subject, r.ticket.body) for r in records if r.ticket.ticket_id in excluded
    }
    pool = [
        r for r in records
        if text_key(r.ticket.subject, r.ticket.body) not in excluded_texts
    ]
    pool.sort(key=lambda r: collection_order(r.ticket.ticket_id))
    logger.info("%d development tickets; %d excluded as prompt-tuning text; %d in pool.",
                len(records), len(records) - len(pool), len(pool))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    done: dict[str, dict] = {}
    if args.output.exists():
        for line in args.output.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                done[row["ticket_id"]] = row
    skip = {
        ticket_id for ticket_id, row in done.items()
        if not (args.retry_errors and row.get("error"))
    }
    todo = [r for r in pool if r.ticket.ticket_id not in skip][: max(0, args.max_tickets)]
    logger.info("%d already attempted; classifying %d now.", len(skip), len(todo))

    errors = 0
    with args.output.open("a", encoding="utf-8", newline="\n") as file:
        for index, record in enumerate(todo, 1):
            ticket = record.ticket
            row = {
                "ticket_id": ticket.ticket_id,
                "split": split_for_text(text_key(ticket.subject, ticket.body)),
            }
            try:
                result = classify_ticket(ticket)
                row.update({k: result[k] for k in (
                    "intent", "intent_confidence", "urgency", "urgency_confidence",
                    "urgency_evidence_valid", "urgency_ambiguous", "model_name", "prompt_version",
                )})
            except Exception as exc:  # recorded so a rerun can retry it deliberately
                errors += 1
                row["error"] = f"{type(exc).__name__}: {exc}"
                logger.warning("%s failed: %s", ticket.ticket_id, row["error"])
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
            file.flush()
            logger.info("[%d/%d] %s", index, len(todo), ticket.ticket_id)
    remaining = len(pool) - len(skip) - len(todo)
    print(f"Done. {len(todo) - errors} classified, {errors} errors, ~{max(0, remaining)} left in pool.")
    print(f"Predictions: {args.output}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
