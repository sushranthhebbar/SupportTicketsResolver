"""Paired comparison of two classifier prompt versions on development tickets.

Reads two prediction files written by collect_calibration_predictions.py and the
development labels, and reports intent AND urgency metrics side by side: accuracy,
macro precision/recall/F1, per-class recall, paired discordant counts with an exact
McNemar test, scenario-level views, and the pre-registered H1 criteria from
docs/development_error_analysis.md. Validation tickets are never read.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from math import comb
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.scenarios import scenario_clusters, scenario_split
from src.tickets import load_ticket_records

EVAL_DIR = PROJECT_ROOT / "evaluation"
H1_MIN_INTEGRATION_RECALL = 0.50
H1_MIN_MACRO_RECALL = 0.87
H1_MAX_CLASS_RECALL_LOSS = 0.10
H1_MIN_NET_DISCORDANT_GAIN = 10


def mcnemar_exact(only_a: int, only_b: int) -> float:
    """Two-sided exact McNemar p-value from discordant counts."""
    n = only_a + only_b
    if n == 0:
        return 1.0
    tail = sum(comb(n, k) for k in range(0, min(only_a, only_b) + 1)) / 2**n
    return min(1.0, 2 * tail)


def class_metrics(gold: list[str], pred: list[str]) -> dict[str, dict[str, float | int]]:
    out: dict[str, dict[str, float | int]] = {}
    for label in sorted(set(gold) | set(pred)):
        tp = sum(g == label and p == label for g, p in zip(gold, pred))
        fp = sum(g != label and p == label for g, p in zip(gold, pred))
        fn = sum(g == label and p != label for g, p in zip(gold, pred))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        out[label] = {"n_gold": tp + fn, "precision": precision, "recall": recall, "f1": f1}
    return out


def macro(metrics: dict[str, dict[str, float | int]], key: str) -> float:
    rows = [m[key] for m in metrics.values() if m["n_gold"]]
    return sum(rows) / len(rows) if rows else 0.0


def load_predictions(path: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if not row.get("error"):
                rows[row["ticket_id"]] = row
    return rows


def evaluate(ids: list[str], field: str, gold: dict, a: dict, b: dict) -> dict:
    g = [gold[i][field] for i in ids]
    pa = [a[i][field] for i in ids]
    pb = [b[i][field] for i in ids]
    ca = [x == y for x, y in zip(g, pa)]
    cb = [x == y for x, y in zip(g, pb)]
    only_a = sum(x and not y for x, y in zip(ca, cb))
    only_b = sum(y and not x for x, y in zip(ca, cb))
    ma, mb = class_metrics(g, pa), class_metrics(g, pb)
    return {
        "n": len(ids), "acc_a": sum(ca) / len(ids), "acc_b": sum(cb) / len(ids),
        "only_a_correct": only_a, "only_b_correct": only_b,
        "mcnemar_p": mcnemar_exact(only_a, only_b),
        "macro_precision": (macro(ma, "precision"), macro(mb, "precision")),
        "macro_recall": (macro(ma, "recall"), macro(mb, "recall")),
        "macro_f1": (macro(ma, "f1"), macro(mb, "f1")),
        "per_class": {c: (ma.get(c, {}).get("n_gold", 0), ma.get(c, {}).get("recall", 0.0),
                          mb.get(c, {}).get("recall", 0.0)) for c in sorted(set(g))},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, default=EVAL_DIR / "calibration" / "development_predictions.jsonl")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--tickets", type=Path, default=EVAL_DIR / "data" / "development_tickets.json")
    args = parser.parse_args()
    if "validation" in args.tickets.name.lower():
        parser.error("Prompt comparison must not use the validation tickets.")

    records = load_ticket_records(args.tickets)
    gold = {r.ticket.ticket_id: dict(r.labels) for r in records}
    base, cand = load_predictions(args.baseline), load_predictions(args.candidate)
    ids = sorted(set(base) & set(cand))
    if not ids:
        parser.error("No tickets classified successfully in both files.")
    versions = ({r["prompt_version"] for r in base.values()}, {r["prompt_version"] for r in cand.values()})
    print(f"Baseline {sorted(versions[0])} vs candidate {sorted(versions[1])}; paired tickets: {len(ids)} "
          f"(baseline-only {len(set(base) - set(cand))}, candidate-only {len(set(cand) - set(base))})")
    split = scenario_split(records)
    scen = {i: n for n, group in enumerate(scenario_clusters(records)) for i in group}
    slices = {"all": ids,
              "scenario-holdout": [i for i in ids if split[i] == "holdout"],
              "scenario-fit": [i for i in ids if split[i] == "fit"]}

    results = {}
    for field in ("intent", "urgency"):
        for name, subset in slices.items():
            if subset:
                results[(field, name)] = evaluate(subset, field, gold, base, cand)
    print("\nfield     slice             n   acc base -> cand   only-base only-cand  McNemar p   macroP / macroR / macroF1 (base -> cand)")
    for (field, name), r in results.items():
        print(f"{field:8s}  {name:16s} {r['n']:4d}   {r['acc_a']:.3f} -> {r['acc_b']:.3f}"
              f"      {r['only_a_correct']:4d} {r['only_b_correct']:8d}   {r['mcnemar_p']:.3f}   "
              + " / ".join(f"{r[k][0]:.3f}->{r[k][1]:.3f}" for k in ("macro_precision", "macro_recall", "macro_f1")))

    intent_all = results[("intent", "all")]
    print("\nIntent per-class recall (gold n, base -> cand, change):")
    for label, (n, ra, rb) in intent_all["per_class"].items():
        flag = "  <-- loses >10 pts" if rb - ra < -H1_MAX_CLASS_RECALL_LOSS else ""
        print(f"  {label:24s} n={n:3d}  {ra:.2f} -> {rb:.2f}  ({rb - ra:+.2f}){flag}")

    # scenario-level view: intent errors cluster in few scenarios, so count them
    bad_a = {scen[i] for i in ids if base[i]["intent"] != gold[i]["intent"]}
    bad_b = {scen[i] for i in ids if cand[i]["intent"] != gold[i]["intent"]}
    print(f"\nScenarios (of {len({scen[i] for i in ids})}) with >=1 intent error: base {len(bad_a)} -> cand {len(bad_b)}; "
          f"fixed {len(bad_a - bad_b)}, newly broken {len(bad_b - bad_a)}")
    change = Counter((gold[i]["intent"], base[i]["intent"], cand[i]["intent"]) for i in ids
                     if base[i]["intent"] != cand[i]["intent"])
    print("Tickets whose intent changed (gold, base -> cand): top 12")
    for (g, a, b), n in change.most_common(12):
        print(f"  {n:3d}  gold={g:22s} {a} -> {b}  [{'now right' if b == g else 'was right' if a == g else 'both wrong'}]")

    # urgency side effects: the intent definitions must not disturb urgency
    flips = Counter((base[i]["urgency"], cand[i]["urgency"]) for i in ids if base[i]["urgency"] != cand[i]["urgency"])
    print(f"\nUrgency prediction changed on {sum(flips.values())}/{len(ids)} tickets: {dict(flips)}")
    for field in ("intent_confidence", "urgency_confidence"):
        mean = lambda d: sum(d[i][field] for i in ids) / len(ids)
        print(f"Mean {field}: {mean(base):.3f} -> {mean(cand):.3f}")
    for flag in ("urgency_ambiguous", "urgency_evidence_valid"):
        print(f"{flag} true: {sum(bool(base[i][flag]) for i in ids)} -> {sum(bool(cand[i][flag]) for i in ids)}")

    net = intent_all["only_b_correct"] - intent_all["only_a_correct"]
    integ = intent_all["per_class"].get("integration_help", (0, 0.0, 0.0))[2]
    worst = min((rb - ra for (_, ra, rb) in intent_all["per_class"].values()), default=0.0)
    criteria = {
        f"integration_help recall >= {H1_MIN_INTEGRATION_RECALL:.0%} (now {integ:.0%})": integ >= H1_MIN_INTEGRATION_RECALL,
        f"intent macro recall >= {H1_MIN_MACRO_RECALL} (now {intent_all['macro_recall'][1]:.3f})":
            intent_all["macro_recall"][1] >= H1_MIN_MACRO_RECALL,
        f"no class loses > {H1_MAX_CLASS_RECALL_LOSS:.0%} recall (worst {worst:+.2f})": worst >= -H1_MAX_CLASS_RECALL_LOSS,
        f"net discordant gain >= {H1_MIN_NET_DISCORDANT_GAIN} (now {net:+d})": net >= H1_MIN_NET_DISCORDANT_GAIN,
    }
    print("\nPre-registered H1 criteria (docs/development_error_analysis.md):")
    for text, ok in criteria.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {text}")
    print("H1 overall:", "PASS" if all(criteria.values()) else "NOT MET")
    print("\nCaveats: the intent tie-break rules were written after reading this development "
          "set's error pairs, and intent errors fall in ~15 scenarios, so gains here are optimistic "
          "and partly reflect label conventions. Do not tune further against these tickets.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
