"""Prometheus counters and latency metrics for ticket processing."""

from __future__ import annotations

import os

from prometheus_client import Counter, Histogram, start_http_server


TICKETS_PROCESSED = Counter(
    "tickets_processed_total",
    "Tickets processed by channel and outcome",
    ("channel", "outcome"),
)
RESPONSE_SECONDS = Histogram(
    "response_seconds",
    "End-to-end ticket processing time in seconds",
)
GUARDRAIL_BLOCKS = Counter(
    "guardrail_blocks_total",
    "Responses blocked by guardrail",
    ("guardrail",),
)


def start_metrics_server(port: int | None = None) -> None:
    """Expose the default Prometheus registry on localhost:port."""
    metrics_port = port or int(os.getenv("PROMETHEUS_PORT", "8001"))
    start_http_server(metrics_port, addr="127.0.0.1")


def record_ticket(channel: str, outcome: str) -> None:
    TICKETS_PROCESSED.labels(channel=channel, outcome=outcome).inc()


def record_guardrail_block(guardrail: str) -> None:
    GUARDRAIL_BLOCKS.labels(guardrail=guardrail).inc()
