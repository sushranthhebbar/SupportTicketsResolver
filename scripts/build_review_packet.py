"""Build the reading packet and blank scoring sheets for the two-assessor draft review.

Reads the 50 draft_ready drafts of the final validation run from the decision log. The packet
shows the ticket, the draft and the retrieved passages (cited ones marked). It contains no
gold labels and none of the author's own review notes, so assessors judge independently.
"""

from __future__ import annotations

import csv
import json
import random
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUT = PROJECT_ROOT / "evaluation" / "human_review"
COLUMNS = ["ticket_id", "hallucination", "citations_total", "citations_unsupported", "notes"]


def main() -> int:
    tiers = {t["ticket_id"]: t["customer_tier"] for t in json.load(open(PROJECT_ROOT / "evaluation/data/validation_tickets.json"))}
    con = sqlite3.connect(PROJECT_ROOT / "storage" / "decisions.db")
    drafts = []
    for ticket_id, value in con.execute(
        "SELECT ticket_id, prediction_value FROM decisions WHERE stage='answer_drafting' AND action_taken='draft_ready'"
    ):
        drafts.append((ticket_id, json.loads(value)))
    if len(drafts) < 50:
        print(f"Expected at least 50 drafts, found {len(drafts)}", file=sys.stderr)
        return 1
    random.Random(2026).shuffle(drafts)

    OUT.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Draft review packet (50 drafts)",
        "",
        "Judge each draft on its own, from the ticket and the retrieved passages shown. Do not discuss",
        "scores with the other assessor until both sheets are finished.",
        "",
        "## Rubric",
        "",
        "- **hallucination** (`Y` or `N`): `Y` if the draft contains at least one claim that the retrieved",
        "  passages do not support. This includes a fact about the customer's account or situation that",
        "  the ticket does not state, and a feature or step presented as available to a customer whose plan",
        "  (shown below) the passage excludes. Greetings, offers to help and hedged next steps are not claims.",
        "- **citations_total**: the number of `[DOC-...]` citations in the draft (count each occurrence).",
        "- **citations_unsupported**: how many of those citations are attached to a sentence that the cited",
        "  passage does not support. A citation to the right document that does not back its sentence counts.",
        "- **notes**: anything a second reader should know (optional).",
        "",
        "Record scores in your own sheet (`assessor_A.csv` or `assessor_B.csv`), one row per ticket.",
        "",
    ]
    for number, (ticket_id, d) in enumerate(drafts, start=1):
        ctx = d["ticket_context"]
        cited = set(d["citations"])
        lines += [
            f"## {number}. {ticket_id}",
            "",
            f"**Channel:** {ctx.get('channel')} | **Customer plan:** {tiers.get(ticket_id, 'unknown')}",
            "",
            f"**Subject:** {ctx.get('subject')}",
            "",
            "**Ticket body:**",
            "",
            *["> " + line for line in str(ctx.get("body", "")).splitlines()],
            "",
            "**Draft reply:**",
            "",
            *["> " + line for line in d["draft"].splitlines()],
            "",
            "**Retrieved passages:**",
            "",
        ]
        for source in d["retrieved_sources"]:
            mark = " (cited)" if source["doc_id"] in cited else ""
            lines += [f"- **{source['doc_id']}{mark}**, {source['title']}: {source['passage']}", ""]
        lines.append("---")
        lines.append("")
    (OUT / "review_packet.md").write_text("\n".join(lines), encoding="utf-8")

    ids = [ticket_id for ticket_id, _ in drafts]
    for name in ("assessor_A", "assessor_B"):
        with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(COLUMNS)
            for ticket_id in ids:
                writer.writerow([ticket_id, "", "", "", ""])
    print(f"Wrote {len(ids)} drafts to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
