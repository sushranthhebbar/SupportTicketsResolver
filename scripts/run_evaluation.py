"""Run the evaluation harness with a project ticket processor."""

from __future__ import annotations

import argparse
import importlib
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation import run_evaluation  # noqa: E402
from src.tickets import NormalizedTicket  # noqa: E402


def _load_processor(specification: str) -> Callable[[NormalizedTicket], Any]:
    if ":" not in specification:
        raise ValueError("Processor must use the form 'module:function'")
    module_name, function_name = specification.split(":", 1)
    module = importlib.import_module(module_name)
    processor = getattr(module, function_name, None)
    if not callable(processor):
        raise ValueError(f"Processor {specification!r} is not callable")
    return processor


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    parser = argparse.ArgumentParser(
        description="Process a ticket dataset and write per-ticket results and metrics."
    )
    parser.add_argument("--input", required=True, help="Input ticket JSON file")
    parser.add_argument("--output", required=True, help="Per-ticket JSONL output path")
    parser.add_argument("--report", help="Metrics JSON path (defaults beside --output)")
    parser.add_argument(
        "--processor",
        required=True,
        help="Ticket processor as importable module:function",
    )
    parser.add_argument("--system-version", default="unspecified")
    parser.add_argument(
        "--model-request-interval",
        type=float,
        default=3.0,
        help="Minimum seconds between model requests during evaluation (default: 3)",
    )
    args = parser.parse_args()

    try:
        if args.model_request_interval < 0:
            parser.error("--model-request-interval must be zero or greater")
        os.environ["MODEL_MIN_REQUEST_INTERVAL_SECONDS"] = str(args.model_request_interval)
        processor = _load_processor(args.processor)
        report = run_evaluation(
            args.input,
            args.output,
            processor,
            report_path=args.report,
            system_version=args.system_version,
        )
    except Exception as exc:
        parser.exit(2, f"Evaluation could not run: {type(exc).__name__}: {exc}\n")

    print(
        f"Processed {report['run_info']['tickets_processed']} of "
        f"{report['run_info']['tickets_in_input']} tickets; "
        f"{report['run_info']['processing_errors']} errors."
    )
    print(f"Results: {report['run_info']['results_path']}")
    print(f"Metrics: {report['run_info']['report_path']}")
    return 0 if report["run_info"]["processing_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
