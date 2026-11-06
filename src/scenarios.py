"""Paraphrase "scenario" grouping for leakage-free development splits.

The development tickets are about 79 paraphrase scenarios (typos, changed durations,
re-worded openings). Splitting by exact text lets paraphrases of the same scenario
land on both sides of a split. Scenarios are built from ticket text only: tickets are
linked when their content-word Jaccard similarity is at least the threshold, and
connected tickets form one scenario (union-find). No labels are used.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Iterable, Sequence

from src.calibration import FIT_FRACTION, text_key
from src.tickets import PROJECT_ROOT, TicketRecord

SIMILARITY_THRESHOLD = 0.5
_STOP_WORDS = frozenset(
    "the a an and or to of in on is are was were we our i my it this that for with as at "
    "be by not no have has had can you please do does did from so if but will would could "
    "me us your their its they them there then than into out up about".split()
)
TUNING_ID_SOURCES = (
    "evaluation/results/development_citation_probe_input.json",
    "evaluation/results/development_citation_probe_v2_16_input.json",
)
TUNING_JSONL_SOURCES = (
    "evaluation/results/urgency_spectrum_development.jsonl",
    "evaluation/results/urgency_pr03_v3_16.jsonl",
)


def _content_words(subject: str, body: str) -> frozenset[str]:
    return frozenset(
        word
        for word in re.findall(r"[a-z0-9]+", f"{subject} {body}".lower())
        if word not in _STOP_WORDS and len(word) > 2
    )


def scenario_clusters(
    records: Sequence[TicketRecord], *, threshold: float = SIMILARITY_THRESHOLD
) -> list[list[str]]:
    """Return ticket-ID groups, one per paraphrase scenario (text-only)."""
    ids = [record.ticket.ticket_id for record in records]
    words = {
        record.ticket.ticket_id: _content_words(record.ticket.subject, record.ticket.body)
        for record in records
    }
    parent = {ticket_id: ticket_id for ticket_id in ids}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    for index, first in enumerate(ids):
        for second in ids[index + 1:]:
            union = words[first] | words[second]
            if union and len(words[first] & words[second]) / len(union) >= threshold:
                parent[find(first)] = find(second)
    groups: dict[str, list[str]] = {}
    for ticket_id in ids:
        groups.setdefault(find(ticket_id), []).append(ticket_id)
    return list(groups.values())


def scenario_split(
    records: Sequence[TicketRecord],
    *,
    fit_fraction: float = FIT_FRACTION,
    threshold: float = SIMILARITY_THRESHOLD,
) -> dict[str, str]:
    """Map ticket_id -> ``fit``/``holdout``; every scenario lands wholly on one side."""
    by_id = {record.ticket.ticket_id: record for record in records}
    split: dict[str, str] = {}
    for group in scenario_clusters(records, threshold=threshold):
        anchor = min(text_key(by_id[i].ticket.subject, by_id[i].ticket.body) for i in group)
        bucket = int(hashlib.sha256(("scenario:" + anchor).encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
        side = "fit" if bucket < fit_fraction else "holdout"
        for ticket_id in group:
            split[ticket_id] = side
    return split


def tuning_ticket_ids(root: Path = PROJECT_ROOT) -> set[str]:
    """Development tickets already used for prompt tuning or inspection."""
    ids: set[str] = set()
    for relative in TUNING_ID_SOURCES:
        path = root / relative
        if path.exists():
            for item in json.loads(path.read_text(encoding="utf-8")):
                ids.add(item if isinstance(item, str) else item.get("ticket_id"))
    for relative in TUNING_JSONL_SOURCES:
        path = root / relative
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    ids.add(json.loads(line)["ticket_id"])
    return {ticket_id for ticket_id in ids if ticket_id}


def tuning_scenario_ids(records: Sequence[TicketRecord], root: Path = PROJECT_ROOT) -> set[str]:
    """All tickets in any scenario that contains a tuning ticket."""
    tuning = tuning_ticket_ids(root)
    excluded: set[str] = set()
    for group in scenario_clusters(records):
        if tuning.intersection(group):
            excluded.update(group)
    return excluded
