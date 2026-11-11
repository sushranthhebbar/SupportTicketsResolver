"""Segment fairness table (Governance Framework section 3) from a saved results file.

No model calls. Segments: customer tier, language fluency, and ticket length (body words,
split at the median). Measures per segment: intent accuracy, retrieval hit (an expected
article is among the retrieved sources, answerable tickets only) and draft-ready rate.
Intervals are Wilson 95%; they treat tickets as independent, so they are narrower than
the scenario-cluster intervals in validation_accuracy_uncertainty.json.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    z, p = 1.96, k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickets", default="evaluation/data/validation_tickets.json")
    ap.add_argument("--results", default="evaluation/results/validation_final_pr03v4.jsonl")
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    tickets = {t["ticket_id"]: t for t in json.load(open(a.tickets))}
    results = {}
    for line in open(a.results):
        row = json.loads(line)
        if not row.get("error") and row.get("result"):
            results[row["ticket_id"]] = row["result"]
    ids = sorted(results)
    words = {i: len(tickets[i]["body"].split()) for i in ids}
    cut = statistics.median(words.values())

    def segs(i):
        t = tickets[i]
        return {
            "tier: enterprise": t["customer_tier"] == "enterprise",
            "tier: business": t["customer_tier"] == "business",
            "tier: standard": t["customer_tier"] == "standard",
            "fluent English": t["language_fluency"] == "fluent",
            "non-fluent English": t["language_fluency"] == "non_fluent",
            f"short (body <= {cut:g} words)": words[i] <= cut,
            f"long (body > {cut:g} words)": words[i] > cut,
        }

    names = list(segs(ids[0]))
    rows = []
    for name in names:
        members = [i for i in ids if segs(i)[name]]
        n = len(members)
        acc = sum(results[i]["intent"] == tickets[i]["labels"]["intent"] for i in members)
        ans = [i for i in members if tickets[i]["labels"].get("answerable_from_docs")]
        hit = sum(
            bool(set(tickets[i]["labels"].get("expected_doc_ids") or [])
                 & {s["doc_id"] for s in results[i]["retrieved_sources"]})
            for i in ans
        )
        dr = sum(results[i]["answer_status"] == "draft_ready" for i in members)
        rows.append({
            "segment": name, "n": n,
            "intent_accuracy": [acc, n, acc / n, wilson(acc, n)],
            "retrieval_hit": [hit, len(ans), hit / len(ans) if ans else None, wilson(hit, len(ans))],
            "draft_ready": [dr, n, dr / n, wilson(dr, n)],
        })
    for m in ("intent_accuracy", "retrieval_hit", "draft_ready"):
        best = max(r[m][2] for r in rows if r[m][2] is not None)
        for r in rows:
            r[m].append(None if r[m][2] is None else round((r[m][2] - best) * 100, 1))
    json.dump({"median_body_words": cut, "rows": rows}, open(a.output, "w"), indent=2)
    for r in rows:
        f = lambda m: "n/a" if r[m][2] is None else f"{r[m][2]*100:.0f}% ({r[m][0]}/{r[m][1]}, {r[m][3][0]*100:.0f}-{r[m][3][1]*100:.0f}) {r[m][4]:+.0f}"
        print(f"{r['segment']:28s} n={r['n']:3d} | intent {f('intent_accuracy')} | retr {f('retrieval_hit')} | draft {f('draft_ready')}")


if __name__ == "__main__":
    main()
