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

from src.calibration import collection_order, text_key
from src.classification import CLASSIFIER_PROMPT_VERSION, classify_ticket
from src.scenarios import tuning_ticket_ids
from src.tickets import load_ticket_records

DEFAULT_INPUT = PROJECT_ROOT / "evaluation" / "data" / "development_tickets.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "evaluation" / "calibration" / "development_predictions.jsonl"
logger = logging.getLogger("calibration")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-tickets", type=int, default=100,
                        help="New tickets to classify in this invocation (default 100).")
    parser.add_argument("--request-interval", type=float, default=3.0,
                        help="Minimum seconds between model requests (default 3).")
    parser.add_argument("--prompt-version", default=CLASSIFIER_PROMPT_VERSION,
                        help="Classifier prompt version to run (default: the runtime version).")
    parser.add_argument("--include-tuning-tickets", action="store_true",
                        help="Do not exclude prompt-tuning tickets (for prompt-version comparisons).")
    parser.add_argument("--only-ids-from", type=Path,
                        help="Restrict the pool to ticket IDs present in this predictions file "
                             "(e.g. the PR-03-v2 baseline) for a paired prompt comparison.")
    parser.add_argument("--retry-errors", action="store_true",
                        help="Re-attempt tickets whose earlier attempt recorded an error.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    os.environ["MODEL_MIN_REQUEST_INTERVAL_SECONDS"] = str(max(0.0, args.request_interval))

    records = load_ticket_records(args.input)
    excluded = set() if args.include_tuning_tickets else tuning_ticket_ids()
    excluded_texts = {
        text_key(r.ticket.subject, r.ticket.body) for r in records if r.ticket.ticket_id in excluded
    }
    pool = [
        r for r in records
        if text_key(r.ticket.subject, r.ticket.body) not in excluded_texts
    ]
    if args.only_ids_from:
        wanted = {
            json.loads(line)["ticket_id"]
            for line in args.only_ids_from.read_text(encoding="utf-8").splitlines()
            if line.strip() and not json.loads(line).get("error")
        }
        pool = [r for r in pool if r.ticket.ticket_id in wanted]
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
            row = {"ticket_id": ticket.ticket_id}
            try:
                result = classify_ticket(ticket, prompt_version=args.prompt_version)
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
