"""Isotonic confidence calibration for classifier intent and urgency scores.

The model's confidence values are raw self-estimates. This module maps each raw
score to the observed probability that the corresponding label was correct, fitted
on a development calibration split (never the validation/evaluation set). The
calibration artifact is versioned with the model and prompt it was fitted for and
is applied only to predictions from that same model and prompt.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.tickets import PROJECT_ROOT


CALIBRATION_ENV_VAR = "CALIBRATION_ARTIFACT"
FIELDS = ("intent", "urgency")
FIT_FRACTION = 0.70
MIN_CLASS_SAMPLE = 10


def text_key(subject: str, body: str) -> str:
    """Normalized subject/body text; identical texts must share a split."""
    return " ".join(f"{subject} {body}".casefold().split())


def split_for_text(key: str, *, fit_fraction: float = FIT_FRACTION) -> str:
    """Deterministically assign a text group to ``fit`` or ``holdout``."""
    bucket = int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    return "fit" if bucket < fit_fraction else "holdout"


def collection_order(key: str) -> str:
    """Stable pseudo-random ordering so any prefix of a run is a fair sample."""
    return hashlib.sha256(("order:" + key).encode("utf-8")).hexdigest()


def fit_isotonic(
    scores: Sequence[float], correct: Sequence[bool], *, min_block_n: int = 1
) -> list[dict[str, float]]:
    """Pool-adjacent-violators fit; returns non-decreasing blocks.

    Each block is ``{"x_min", "x_max", "value", "n"}`` where ``value`` is the
    observed correctness rate for scores within the block. Blocks supported by
    fewer than ``min_block_n`` observations are pooled into a neighbor so a handful
    of tickets cannot produce an extreme calibrated value.
    """
    if len(scores) != len(correct):
        raise ValueError("scores and correct must have the same length")
    if not scores:
        raise ValueError("At least one observation is required to fit a calibrator")
    grouped: dict[float, list[float]] = {}
    for score, ok in zip(scores, correct):
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
            raise ValueError("scores must be numbers between 0 and 1")
        entry = grouped.setdefault(float(score), [0.0, 0.0])
        entry[0] += 1.0 if ok else 0.0
        entry[1] += 1.0
    blocks: list[dict[str, float]] = []

    def pool_violations() -> None:
        while len(blocks) > 1 and (
            blocks[-2]["hits"] / blocks[-2]["n"] > blocks[-1]["hits"] / blocks[-1]["n"]
        ):
            last = blocks.pop()
            prev = blocks[-1]
            prev["x_max"] = last["x_max"]
            prev["hits"] += last["hits"]
            prev["n"] += last["n"]

    for score in sorted(grouped):
        hits, count = grouped[score]
        blocks.append({"x_min": score, "x_max": score, "hits": hits, "n": count})
        pool_violations()
    while len(blocks) > 1 and any(b["n"] < min_block_n for b in blocks):
        index = next(i for i, b in enumerate(blocks) if b["n"] < min_block_n)
        into = index - 1 if index > 0 else 1
        low, high = sorted((index, into))
        blocks[low] = {
            "x_min": blocks[low]["x_min"], "x_max": blocks[high]["x_max"],
            "hits": blocks[low]["hits"] + blocks[high]["hits"],
            "n": blocks[low]["n"] + blocks[high]["n"],
        }
        del blocks[high]
        rebuilt, blocks[:] = list(blocks), []
        for block in rebuilt:
            blocks.append(block)
            pool_violations()
    return [
        {"x_min": b["x_min"], "x_max": b["x_max"], "value": b["hits"] / b["n"], "n": int(b["n"])}
        for b in blocks
    ]


def predict_isotonic(blocks: Sequence[Mapping[str, float]], score: float) -> float:
    """Conservative step lookup: a score takes the value of the highest block at or
    below it; scores below the fitted range take the lowest block's value."""
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
        raise ValueError("score must be a number between 0 and 1")
    value = blocks[0]["value"]
    for block in blocks:
        if score >= block["x_min"]:
            value = block["value"]
        else:
            break
    return float(value)


def brier_score(probabilities: Sequence[float], correct: Sequence[bool]) -> float | None:
    if not probabilities:
        return None
    return sum((p - (1.0 if ok else 0.0)) ** 2 for p, ok in zip(probabilities, correct)) / len(probabilities)


def reliability_bins(
    probabilities: Sequence[float], correct: Sequence[bool], *, bins: int = 5
) -> list[dict[str, Any]]:
    """Equal-width reliability table: mean predicted vs observed correctness."""
    rows: list[dict[str, Any]] = []
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        members = [
            (p, ok)
            for p, ok in zip(probabilities, correct)
            if low <= p < high or (index == bins - 1 and p == 1.0)
        ]
        rows.append(
            {
                "range": [low, high],
                "n": len(members),
                "mean_predicted": sum(p for p, _ in members) / len(members) if members else None,
                "observed_accuracy": sum(1 for _, ok in members if ok) / len(members) if members else None,
            }
        )
    return rows


def precision_at_threshold(
    predicted_labels: Sequence[str],
    probabilities: Sequence[float],
    correct: Sequence[bool],
    threshold: float,
) -> dict[str, Any]:
    """Overall and per-predicted-class precision among predictions >= threshold."""
    selected = [(label, ok) for label, p, ok in zip(predicted_labels, probabilities, correct) if p >= threshold]
    per_class: dict[str, dict[str, Any]] = {}
    for label in sorted({label for label, _ in selected}):
        members = [ok for item, ok in selected if item == label]
        per_class[label] = {
            "n": len(members),
            "precision": sum(members) / len(members),
            "sufficient_sample": len(members) >= MIN_CLASS_SAMPLE,
        }
    return {
        "threshold": threshold,
        "n_selected": len(selected),
        "precision": sum(ok for _, ok in selected) / len(selected) if selected else None,
        "per_class": per_class,
    }


def build_artifact(
    fit_rows: Sequence[Mapping[str, Any]],
    holdout_rows: Sequence[Mapping[str, Any]],
    *,
    model_name: str,
    prompt_version: str,
    threshold: float = 0.80,
    version: str = "calibration-v1",
    notes: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Fit per-field calibrators on ``fit_rows`` and score them on ``holdout_rows``.

    Rows need ``{field}_pred``, ``{field}_conf`` and ``{field}_correct`` for each
    field, plus ``ticket_id``.
    """
    calibrators: dict[str, Any] = {}
    metrics: dict[str, Any] = {}
    for field in FIELDS:
        blocks = fit_isotonic(
            [row[f"{field}_conf"] for row in fit_rows],
            [row[f"{field}_correct"] for row in fit_rows],
            min_block_n=MIN_CLASS_SAMPLE,
        )
        calibrators[field] = {"blocks": blocks}
        field_metrics: dict[str, Any] = {}
        for name, rows in (("fit", fit_rows), ("holdout", holdout_rows)):
            raw = [row[f"{field}_conf"] for row in rows]
            calibrated = [predict_isotonic(blocks, value) for value in raw]
            correct = [bool(row[f"{field}_correct"]) for row in rows]
            labels = [row[f"{field}_pred"] for row in rows]
            field_metrics[name] = {
                "n": len(rows),
                "accuracy": sum(correct) / len(correct) if correct else None,
                "brier_raw": brier_score(raw, correct),
                "brier_calibrated": brier_score(calibrated, correct),
                "reliability_raw": reliability_bins(raw, correct),
                "reliability_calibrated": reliability_bins(calibrated, correct),
                "precision_at_threshold": precision_at_threshold(labels, calibrated, correct, threshold),
            }
        metrics[field] = field_metrics
    holdout_ids = sorted(row["ticket_id"] for row in holdout_rows)
    fit_ids = sorted(row["ticket_id"] for row in fit_rows)
    return {
        "version": version,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "method": "isotonic_regression_pav_conservative_step",
        "model_name": model_name,
        "prompt_version": prompt_version,
        "threshold": threshold,
        "fit_ticket_ids": fit_ids,
        "holdout_ticket_ids": holdout_ids,
        "split_rule": f"paraphrase-scenario clusters (text-only Jaccard >= 0.5); sha256(anchor text) bucket < {FIT_FRACTION} -> fit, else holdout",
        "calibrators": calibrators,
        "metrics": metrics,
        "notes": dict(notes or {}),
    }


class CalibrationArtifact:
    """Loaded calibration artifact that maps raw classifier scores."""

    def __init__(self, data: Mapping[str, Any]) -> None:
        self.data = dict(data)
        for field in FIELDS:
            if not self.data.get("calibrators", {}).get(field, {}).get("blocks"):
                raise ValueError(f"Calibration artifact has no {field} calibrator")

    @property
    def version(self) -> str:
        return str(self.data["version"])

    def applies_to(self, classification: Mapping[str, Any]) -> bool:
        """Only use scores from the model and prompt the artifact was fitted for."""
        return (
            classification.get("prompt_version") == self.data.get("prompt_version")
            and classification.get("model_name") == self.data.get("model_name")
        )

    def calibrate(self, classification: Mapping[str, Any]) -> dict[str, float] | None:
        if not self.applies_to(classification):
            return None
        return {
            field: predict_isotonic(
                self.data["calibrators"][field]["blocks"], classification[f"{field}_confidence"]
            )
            for field in FIELDS
        }


def save_artifact(artifact: Mapping[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_artifact(path: str | Path) -> CalibrationArtifact:
    return CalibrationArtifact(json.loads(Path(path).read_text(encoding="utf-8")))


def configured_artifact() -> CalibrationArtifact | None:
    """Return the artifact named by ``CALIBRATION_ARTIFACT``, or None if unset.

    Activation is explicit so that a freshly generated artifact never enables
    automatic responses until someone has reviewed its held-out results.
    """
    configured = os.getenv(CALIBRATION_ENV_VAR, "").strip()
    if not configured:
        return None
    path = Path(configured)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return load_artifact(path)
