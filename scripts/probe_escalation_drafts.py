"""Probe retrieval and drafting on tickets that router-v4 would auto-route but the labels say escalate.

Selection (development tickets only, from stored predictions): tickets whose calibrated
intent confidence clears the threshold, whose intent is not a must-not intent (so
router-v4 would send them to ``auto_respond``), and whose gold ``expected_route`` is
``escalate``. For each, the real retriever and drafter run exactly as the pipeline would
on the auto-respond path. Nothing is sent to anyone. The question answered is how often
a confident, cited draft is produced for a ticket that should have gone to a person.

Resumable: tickets already present in the output file are skipped, so the run can be
split across days to stay inside provider token quotas.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.calibration import collection_order, load_artifact
from src.routing import MUST_NOT_AUTO_RESPOND_INTENTS, route_ticket
from src.tickets import load_ticket_records

EVAL_DIR = PROJECT_ROOT / "evaluation"
DEFAULT_OUTPUT = EVAL_DIR / "calibration" / "escalation_draft_probe.jsonl"
logger = logging.getLogger("probe")


def select_tickets(records, predictions, artifact):
    """Return (ticket_record, prediction) pairs router-v4 would auto-respond but gold says escalate."""
    by_id = {r.ticket.ticket_id: r for r in records}
    selected = []
    for pred in predictions:
        if pred.get("error") or pred["ticket_id"] not in by_id:
            continue
        record = by_id[pred["ticket_id"]]
        calibrated = artifact.calibrate(pred)
        if calibrated is None:
            continue
        route = route_ticket(pred, calibrated_confidence=calibrated)["route"]
        if route == "auto_respond" and record.labels.get("expected_route") == "escalate":
            selected.append((record, pred))
    return selected


def load_predictions(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarise(rows):
    total = len(rows)
    if not total:
        return {"n": 0}

    def share(predicate, subset=None):
        subset = rows if subset is None else subset
        return {"n": len(subset), "draft_ready": sum(1 for r in subset if r["action"] == "draft_ready")}

    return {
        "n": total,
        "action": dict(Counter(r["action"] for r in rows)),
        "draft_ready_rate": sum(1 for r in rows if r["action"] == "draft_ready") / total,
        "by_answerable_from_docs": {
            str(flag): share(None, [r for r in rows if r["answerable_from_docs"] is flag])
            for flag in (True, False)
        },
        "by_gold_must_not": {
            str(flag): share(None, [r for r in rows if r["must_not_auto_respond"] is flag])
            for flag in (True, False)
        },
        "by_intent_correct": {
            str(flag): share(None, [r for r in rows if r["intent_correct"] is flag])
            for flag in (True, False)
        },
        "expected_doc_retrieved": share(None, [r for r in rows if r["expected_doc_hit"]]),
        "no_retrieval_support": sum(1 for r in rows if r["action"] == "review" and r["reason_code"] == "no_retrieved_evidence"),
        "evidence_insufficient": sum(1 for r in rows if "evidence_sufficiency" in r["failed_guardrails"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickets", type=Path, default=EVAL_DIR / "data" / "development_tickets.json")
    parser.add_argument("--predictions", type=Path, default=EVAL_DIR / "calibration" / "development_predictions.jsonl")
    parser.add_argument("--calibration", type=Path, default=EVAL_DIR / "calibration" / "calibration-v2.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-tickets", type=int, default=40,
                        help="New tickets to probe in this invocation (default 40).")
    parser.add_argument("--request-interval", type=float, default=3.0,
                        help="Minimum seconds between model requests (default 3).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show the selection and what would run; make no retrieval or model calls.")
    parser.add_argument("--summary-only", action="store_true", help="Summarise the output file and exit.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if "validation" in args.tickets.name.lower():
        parser.error("The probe must not use the validation tickets.")
    os.environ["MODEL_MIN_REQUEST_INTERVAL_SECONDS"] = str(max(0.0, args.request_interval))

    if args.summary_only:
        rows = load_predictions(args.output)
        print(json.dumps(summarise([r for r in rows if "action" in r]), indent=2))
        return 0

    records = load_ticket_records(args.tickets)
    artifact = load_artifact(args.calibration)
    selection = select_tickets(records, load_predictions(args.predictions), artifact)
    selection.sort(key=lambda pair: collection_order(pair[0].ticket.ticket_id))
    done = set()
    if args.output.exists():
        done = {r["ticket_id"] for r in load_predictions(args.output)}
    todo = [pair for pair in selection if pair[0].ticket.ticket_id not in done][: max(0, args.max_tickets)]
    logger.info("%d tickets would auto-respond but are expected to escalate; %d already probed; probing %d now.",
                len(selection), len(done), len(todo))
    if args.dry_run:
        print(f"Selected {len(selection)}; would probe {len(todo)} (first 5 shown):")
        for record, pred in todo[:5]:
            print(f"  {record.ticket.ticket_id} intent={pred['intent']} gold={record.labels['intent']} "
                  f"answerable_from_docs={record.labels.get('answerable_from_docs')}")
        return 0

    from src.answering import draft_grounded_reply
    from src.retrieve import search_documentation

    args.output.parent.mkdir(parents=True, exist_ok=True)
    errors = 0
    with args.output.open("a", encoding="utf-8", newline="\n") as file:
        for index, (record, pred) in enumerate(todo, 1):
            ticket, labels = record.ticket, record.labels
            row = {
                "ticket_id": ticket.ticket_id,
                "predicted_intent": pred["intent"],
                "gold_intent": labels["intent"],
                "intent_correct": pred["intent"] == labels["intent"],
                "answerable_from_docs": labels.get("answerable_from_docs"),
                "must_not_auto_respond": labels.get("must_not_auto_respond"),
                "expected_doc_ids": labels.get("expected_doc_ids", []),
            }
            try:
                query = "\n".join(p for p in (ticket.subject, ticket.body) if p.strip())
                sources = list(search_documentation(query))
                result = draft_grounded_reply(ticket, sources)
                retrieved = [s.get("doc_id") for s in sources]
                failed = [k for k, v in result.get("guardrail_results", {}).items() if not v.get("passed", True)]
                row.update({
                    "retrieved_doc_ids": retrieved,
                    "expected_doc_hit": bool(set(row["expected_doc_ids"]) & set(retrieved)),
                    "action": result.get("action"),
                    "answer_status": result.get("answer_status"),
                    "citations": result.get("citations", []),
                    "draft": result.get("answer", ""),
                    "reason": result.get("reason"),
                    "failed_guardrails": failed,
                    "reason_code": failed[0] if failed else None,
                    "model_name": result.get("model_name"),
                })
            except Exception as exc:
                errors += 1
                row["error"] = f"{type(exc).__name__}: {exc}"
                logger.warning("%s failed: %s", ticket.ticket_id, row["error"])
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
            file.flush()
            logger.info("[%d/%d] %s -> %s", index, len(todo), ticket.ticket_id, row.get("action", "error"))
    rows = [r for r in load_predictions(args.output) if "action" in r]
    print(json.dumps(summarise(rows), indent=2))
    print(f"Probed {len(todo) - errors}, errors {errors}. Rows: {args.output}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
