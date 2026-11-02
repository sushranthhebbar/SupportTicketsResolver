"""Independently verify evaluation outputs against their input dataset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tickets import load_ticket_records  # noqa: E402


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"JSONL row {line_number} is not an object")
            rows.append(value)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    records = load_ticket_records(args.input)
    rows = _read_jsonl(args.results)
    report = json.loads(args.report.read_text(encoding="utf-8"))
    expected_ids = [record.ticket.ticket_id for record in records]
    actual_ids = [row.get("ticket_id") for row in rows]
    if actual_ids != expected_ids:
        parser.error("Result ticket IDs or order do not match the input dataset")
    if len(actual_ids) != len(set(actual_ids)):
        parser.error("Result contains duplicate ticket IDs")

    failures = []
    row_error_count = 0
    successful_count = 0
    error_types: dict[str, int] = {}
    for row in rows:
        result = row.get("result")
        if result is not None and not isinstance(result, dict):
            failures.append(f"{row['ticket_id']}: result is not an object")
        if isinstance(result, dict) and ("labels" in result or "history" in result):
            failures.append(f"{row['ticket_id']}: evaluation-only data leaked to processor result")
        if row.get("error") is not None:
            row_error_count += 1
            error_type = str(row["error"].get("type", "Unknown"))
            error_types[error_type] = error_types.get(error_type, 0) + 1
        elif result is not None:
            successful_count += 1

    info = report.get("run_info", {})
    if info.get("tickets_in_input") != len(records):
        failures.append("Report input count does not match dataset")
    if info.get("tickets_processed") != successful_count:
        failures.append("Report processed count does not match successful JSONL rows")
    if info.get("processing_errors") != row_error_count:
        failures.append("Report error count does not match errored JSONL rows")
    if successful_count != len(records):
        failures.append(f"Run is incomplete: {successful_count}/{len(records)} tickets processed successfully")
    if row_error_count:
        failures.append(f"{row_error_count} processor errors by type: {error_types}")

    if failures:
        print("Evaluation artifact verification FAILED:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(
        f"Evaluation artifact verification passed: {len(records)} ordered, unique tickets; "
        "all processed without errors; no labels/history in processor results."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
