"""Cluster-bootstrap confidence intervals and a fairness breakdown for development predictions.

Development tickets only; stored classifier predictions are reused, so no model calls are
made. Paraphrases of one scenario are near-duplicates, so tickets are resampled by scenario
cluster (not individually); intervals from naive per-ticket resampling would be too narrow.

Reports 95% percentile intervals for headline metrics and, for each customer attribute
(channel, tier, region, language fluency), each group's metrics plus its difference from
all other tickets, with an interval for that difference.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.calibration import load_artifact
from src.routing import MUST_NOT_AUTO_RESPOND_INTENTS, route_ticket
from src.scenarios import scenario_clusters
from src.tickets import load_ticket_records

EVAL_DIR = PROJECT_ROOT / "evaluation"
URGENCY_ORDER = {"low": 0, "medium": 1, "high": 2}
ATTRIBUTES = ("channel", "customer_tier", "customer_region", "language_fluency")
# metric name -> (description, ticket predicate for the denominator)
METRICS = {
    "intent_accuracy": "intent exactly matches the label",
    "urgency_exact": "urgency exactly matches the label",
    "urgency_within_one": "urgency within one level of the label",
    "must_not_caught": "gold must-not-auto-respond tickets predicted as a must-not intent",
    "auto_respond_rate": "tickets router-v4 + calibration-v2 would auto-respond",
    "unsafe_auto_rate": "tickets auto-responded although the label expects escalation",
}


def ticket_facts(records, predictions, artifact):
    """One dict per classified ticket: attribute values plus (hit, counted) per metric."""
    facts = {}
    for record in records:
        pred = predictions.get(record.ticket.ticket_id)
        if pred is None or pred.get("error"):
            continue
        labels, ticket = record.labels, record.ticket
        calibrated = artifact.calibrate(pred) if artifact else None
        route = route_ticket(pred, calibrated_confidence=calibrated)["route"]
        gap = abs(URGENCY_ORDER[pred["urgency"]] - URGENCY_ORDER[labels["urgency"]])
        must_not = bool(labels.get("must_not_auto_respond"))
        facts[ticket.ticket_id] = {
            "attrs": {
                "channel": ticket.channel,
                **{name: ticket.customer_context.get(name) for name in ATTRIBUTES[1:]},
            },
            "metrics": {
                "intent_accuracy": (pred["intent"] == labels["intent"], True),
                "urgency_exact": (gap == 0, True),
                "urgency_within_one": (gap <= 1, True),
                "must_not_caught": (pred["intent"] in MUST_NOT_AUTO_RESPOND_INTENTS, must_not),
                "auto_respond_rate": (route == "auto_respond", True),
                "unsafe_auto_rate": (
                    route == "auto_respond" and labels.get("expected_route") == "escalate", True
                ),
            },
        }
    return facts


def tally(ids, facts, metric, predicate=lambda f: True):
    hits = total = 0
    for ticket_id in ids:
        fact = facts[ticket_id]
        if not predicate(fact):
            continue
        hit, counted = fact["metrics"][metric]
        if counted:
            total += 1
            hits += 1 if hit else 0
    return hits, total


def interval(values):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    return [values[int(0.025 * (len(values) - 1))], values[int(round(0.975 * (len(values) - 1)))]]


def rate(hits, total):
    return hits / total if total else None


def bootstrap(clusters, facts, metric, *, predicate=lambda f: True, other=None, reps, rng):
    """CI for the metric on ``predicate`` tickets (or its difference vs ``other`` tickets)."""
    per_cluster = [
        (tally(c, facts, metric, predicate), tally(c, facts, metric, other) if other else None)
        for c in clusters
    ]
    draws = []
    for _ in range(reps):
        sample = [per_cluster[rng.randrange(len(per_cluster))] for _ in per_cluster]
        h = sum(s[0][0] for s in sample)
        n = sum(s[0][1] for s in sample)
        if other is None:
            draws.append(rate(h, n))
        else:
            ho = sum(s[1][0] for s in sample)
            no = sum(s[1][1] for s in sample)
            draws.append(None if not n or not no else h / n - ho / no)
    return interval(draws)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tickets", type=Path, default=EVAL_DIR / "data" / "development_tickets.json")
    parser.add_argument("--predictions", type=Path, default=EVAL_DIR / "calibration" / "development_predictions.jsonl")
    parser.add_argument("--calibration", type=Path, default=EVAL_DIR / "calibration" / "calibration-v2.json")
    parser.add_argument("--output", type=Path, default=EVAL_DIR / "results" / "development_accuracy_uncertainty.json")
    parser.add_argument("--reps", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261106)
    args = parser.parse_args()
    if "validation" in args.tickets.name.lower():
        parser.error("This analysis must not use the validation tickets.")

    records = load_ticket_records(args.tickets)
    predictions = {}
    for line in args.predictions.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            predictions[row["ticket_id"]] = row
    facts = ticket_facts(records, predictions, load_artifact(args.calibration))
    clusters = [[i for i in c if i in facts] for c in scenario_clusters(records)]
    clusters = [c for c in clusters if c]
    rng = random.Random(args.seed)
    everyone = list(facts)

    report = {
        "n_tickets": len(facts),
        "n_scenario_clusters": len(clusters),
        "bootstrap_reps": args.reps,
        "seed": args.seed,
        "note": "95% percentile intervals from resampling scenario clusters. Development tickets only.",
        "overall": {},
        "fairness": {},
    }
    for metric, description in METRICS.items():
        hits, total = tally(everyone, facts, metric)
        report["overall"][metric] = {
            "description": description, "n": total, "value": rate(hits, total),
            "ci95": bootstrap(clusters, facts, metric, reps=args.reps, rng=rng),
        }
    for attribute in ATTRIBUTES:
        groups = sorted({f["attrs"][attribute] for f in facts.values() if f["attrs"][attribute] is not None})
        report["fairness"][attribute] = {}
        for group in groups:
            in_group = lambda f, a=attribute, g=group: f["attrs"][a] == g
            outside = lambda f, a=attribute, g=group: f["attrs"][a] != g
            entry = {"n": sum(1 for f in facts.values() if in_group(f)), "metrics": {}}
            for metric in METRICS:
                hits, total = tally(everyone, facts, metric, in_group)
                entry["metrics"][metric] = {
                    "n": total,
                    "value": rate(hits, total),
                    "difference_vs_rest": (
                        None if not total else rate(hits, total) - rate(*tally(everyone, facts, metric, outside))
                    ),
                    "difference_ci95": bootstrap(
                        clusters, facts, metric, predicate=in_group, other=outside, reps=args.reps, rng=rng
                    ) if total else None,
                }
            report["fairness"][attribute][group] = entry
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"{len(facts)} tickets, {len(clusters)} scenario clusters. Wrote {args.output}\n")
    for metric, row in report["overall"].items():
        low, high = row["ci95"]
        print(f"{metric:20s} {row['value']:.3f}  95% CI [{low:.3f}, {high:.3f}]  n={row['n']}")
    print("\nGroup differences vs all other tickets (flag * = interval excludes 0):")
    for attribute, groups in report["fairness"].items():
        for group, entry in groups.items():
            cells = []
            for metric in ("intent_accuracy", "urgency_exact", "must_not_caught", "unsafe_auto_rate"):
                m = entry["metrics"][metric]
                if m["value"] is None or m["difference_ci95"] is None:
                    cells.append(f"{metric[:12]}=n/a")
                    continue
                low, high = m["difference_ci95"]
                flag = "*" if low > 0 or high < 0 else " "
                cells.append(f"{metric[:12]}={m['value']:.2f}({m['difference_vs_rest']:+.2f}){flag}")
            print(f"{attribute:17s} {str(group):14s} n={entry['n']:3d}  " + "  ".join(cells))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
