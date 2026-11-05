"""Fit intent/urgency isotonic calibrators from collected development predictions.

Fits on the ``fit`` split only and reports Brier score, reliability bins, and
per-class precision on the held-out ``holdout`` split. Validation tickets are
never read. The artifact is written but NOT activated: set CALIBRATION_ARTIFACT
after reviewing the held-out results.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.calibration import build_artifact, save_artifact, split_for_text, text_key
from src.tickets import load_ticket_records

EVAL_DIR = PROJECT_ROOT / "evaluation"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickets", type=Path, default=EVAL_DIR / "data" / "development_tickets.json")
    parser.add_argument("--predictions", type=Path,
                        default=EVAL_DIR / "calibration" / "development_predictions.jsonl")
    parser.add_argument("--output", type=Path, default=EVAL_DIR / "calibration" / "calibration-v1.json")
    parser.add_argument("--version", default="calibration-v1")
    parser.add_argument("--threshold", type=float, default=0.80)
    args = parser.parse_args()
    if "validation" in args.tickets.name.lower():
        parser.error("Calibration must not use the validation tickets.")

    labels = {r.ticket.ticket_id: r for r in load_ticket_records(args.tickets)}
    urgency_by_text: dict[str, set[str]] = {}
    for record in labels.values():
        urgency_by_text.setdefault(text_key(record.ticket.subject, record.ticket.body), set()).add(
            record.labels["urgency"]
        )

    rows, skipped, models, prompts = {"fit": [], "holdout": []}, 0, set(), set()
    for line in args.predictions.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        pred = json.loads(line)
        if pred.get("error"):
            skipped += 1
            continue
        record = labels[pred["ticket_id"]]
        key = text_key(record.ticket.subject, record.ticket.body)
        split = split_for_text(key)
        models.add(pred["model_name"])
        prompts.add(pred["prompt_version"])
        rows[split].append(
            {
                "ticket_id": pred["ticket_id"],
                "intent_pred": pred["intent"],
                "intent_conf": pred["intent_confidence"],
                "intent_correct": pred["intent"] == record.labels["intent"],
                "urgency_pred": pred["urgency"],
                "urgency_conf": pred["urgency_confidence"],
                "urgency_correct": pred["urgency"] == record.labels["urgency"],
                "urgency_label_conflict": len(urgency_by_text[key]) > 1,
            }
        )
    if len(models) != 1 or len(prompts) != 1:
        parser.error(f"Predictions mix models/prompts (models={models}, prompts={prompts}).")
    if not rows["fit"] or not rows["holdout"]:
        parser.error("Need predictions in both the fit and holdout splits; collect more first.")

    artifact = build_artifact(
        rows["fit"], rows["holdout"],
        model_name=models.pop(), prompt_version=prompts.pop(),
        threshold=args.threshold, version=args.version,
        notes={
            "prediction_errors_skipped": skipped,
            "urgency_label_conflicts_in_fit": sum(r["urgency_label_conflict"] for r in rows["fit"]),
            "urgency_label_conflicts_in_holdout": sum(r["urgency_label_conflict"] for r in rows["holdout"]),
            "urgency_labels": "Supplied labels used unchanged, including conflicting duplicate-text labels.",
        },
    )
    save_artifact(artifact, args.output)

    print(f"Wrote {args.output}  (fit n={len(rows['fit'])}, holdout n={len(rows['holdout'])})")
    for field in ("intent", "urgency"):
        for split in ("fit", "holdout"):
            m = artifact["metrics"][field][split]
            p = m["precision_at_threshold"]
            precision = "n/a" if p["precision"] is None else f"{p['precision']:.3f}"
            print(
                f"{field:8s} {split:8s} acc={m['accuracy']:.3f} "
                f"brier raw={m['brier_raw']:.3f} cal={m['brier_calibrated']:.3f} "
                f"| >= {p['threshold']}: n={p['n_selected']} precision={precision}"
            )
    print("Artifact is NOT active. Review held-out results, then set CALIBRATION_ARTIFACT to enable it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
