"""Score the two-assessor draft review: hallucination rate, citation accuracy, agreement.

Reads evaluation/human_review/assessor_A.csv and assessor_B.csv (columns: ticket_id,
hallucination Y/N, citations_total, citations_unsupported, notes). Reports each assessor's
rates, percent agreement and Cohen's kappa on the hallucination call, lists disagreements, and
writes evaluation/human_review/review_summary.json. The rate "either flagged" is the cautious
figure; a consensus figure needs the assessors to resolve the listed disagreements.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parents[1] / "evaluation" / "human_review"


def load(name: str) -> dict[str, dict]:
    rows = {}
    with open(DIR / f"{name}.csv", newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            h = row["hallucination"].strip().upper()
            if h not in {"Y", "N"}:
                raise SystemExit(f"{name}: ticket {row['ticket_id']} needs hallucination Y or N (got {h!r})")
            try:
                total, bad = int(row["citations_total"]), int(row["citations_unsupported"])
            except ValueError:
                raise SystemExit(f"{name}: ticket {row['ticket_id']} needs whole-number citation counts")
            if not 0 <= bad <= total:
                raise SystemExit(f"{name}: ticket {row['ticket_id']} has unsupported citations outside 0..total")
            rows[row["ticket_id"]] = {"h": h == "Y", "total": total, "bad": bad, "notes": row["notes"]}
    return rows


def kappa(a: list[bool], b: list[bool]) -> float | None:
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    expected = pa * pb + (1 - pa) * (1 - pb)
    return None if expected == 1 else (observed - expected) / (1 - expected)


def main() -> int:
    a, b = load("assessor_A"), load("assessor_B")
    if set(a) != set(b):
        raise SystemExit("The two sheets cover different tickets")
    ids = sorted(a)
    summary = {"tickets": len(ids)}
    for name, rows in (("A", a), ("B", b)):
        total = sum(r["total"] for r in rows.values())
        bad = sum(r["bad"] for r in rows.values())
        summary[f"assessor_{name}"] = {
            "hallucination_rate": sum(r["h"] for r in rows.values()) / len(ids),
            "hallucinated_drafts": sum(r["h"] for r in rows.values()),
            "citations_total": total,
            "citations_unsupported": bad,
            "citation_accuracy": (total - bad) / total if total else None,
        }
    ha, hb = [a[i]["h"] for i in ids], [b[i]["h"] for i in ids]
    disagreements = [i for i in ids if a[i]["h"] != b[i]["h"]]
    summary["agreement"] = {
        "percent_agreement": 1 - len(disagreements) / len(ids),
        "cohens_kappa": kappa(ha, hb),
        "disagreements": disagreements,
    }
    summary["hallucination_rate_either_flagged"] = sum(x or y for x, y in zip(ha, hb)) / len(ids)
    summary["hallucination_rate_both_flagged"] = sum(x and y for x, y in zip(ha, hb)) / len(ids)
    (DIR / "review_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
