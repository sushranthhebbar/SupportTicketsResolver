# Validation latency and fairness (PR-03-v4 final run)

Source: `evaluation/results/validation_final_pr03v4.jsonl` (80 tickets, calibration off, frozen config). No model calls were made for this analysis.

## Latency
`evaluation/results/validation_final_pr03v4.report.json` now reports latency (it was `null`): **median 6.3 s, p95 55.8 s, 80 of 80 tickets measured**.

Why it was null: the pipeline returns `latency_seconds: None`, and `build_metrics` (`src/evaluation.py`) used `result.get("latency_seconds", row_value)`, which returns the `None` when the key exists. It now falls back to the harness-measured value, and a test covers it. The saved results file is byte-identical; only the report's latency block and its `run_at_utc` changed.

| Group | n | median | p95 | over 30 s |
|---|---|---|---|---|
| escalate (classify only, no draft) | 17 | 2.9 s | 54.9 s | 4 |
| review, draft ready (classify + retrieve + draft) | 50 | 6.3 s | 53.9 s | 14 |
| review, needs human | 13 | 6.1 s | 57.1 s | 3 |
| all | 80 | 6.3 s | 55.8 s | 21 |

- The distribution is two clusters: about 6 s typical (excluding the 21 slow tickets: median 6.0 s, p95 7.3 s) and 21 tickets (26%) at 42-62 s. The slow ones occur in every group, including escalations that make a single model call. That points to a wait before the call (consistent with 429 retry delays) rather than model time, but I did not log the cause per ticket, so this is an inference.
- **These are not production latencies.** The run used a free-tier model with request pacing (`MODEL_MIN_REQUEST_INTERVAL_SECONDS`, about 2.5 s waited before each of the two calls per drafted ticket) and 429 retries, all inside the measured time. Report them as "end-to-end under free-tier pacing". A clean figure needs an unpaced run on a paid or higher-limit key, which was not done and would be a new live run.

## Fairness on validation
`scripts/analyze_accuracy_uncertainty.py --allow-validation --results ... --calibration-off` -> `evaluation/results/validation_accuracy_uncertainty.json` (80 tickets, 50 scenario clusters, cluster bootstrap, 2000 reps). Each group is compared with all other tickets.

- Overall: intent 91.2% (95% CI 83.3-97.5), urgency exact 43.8% (33.3-54.9), within one 85.0% (75.5-93.9).
- Must-not caught 14/14. The bootstrap interval is degenerate ([1, 1]); the honest bound is the rule of three: with 14 of 14 caught, the miss rate could still be up to about 21% (95%).
- Auto-respond rate and unsafe auto-respond are 0 by construction (calibration off), so they say nothing about fairness.
- Of 13 group comparisons on intent and 13 on urgency, **one interval excludes zero**: Latin America intent accuracy 100% (+10 points, n=7). It is a favourable gap on seven tickets, and with 26+ comparisons about one chance flag is expected. Treat it as noise.
- Group intent accuracy: chat 91% (-0 points), forum 82% (-11), docs_comment 88% (-5), email 97% (+9); Asia-Pacific 86% (-8), Europe 96% (+7), North America 89% (-4); non-fluent 95% (+5), fluent 90% (-5). None is distinguishable from zero.
- The development chat and Europe intent gaps did not reproduce: chat is level with the rest and Europe is above it. This supports the earlier finding that those gaps came from scenario concentration, not from the channel or region.
- Urgency exact accuracy varies by group (27% forum to 63% non-fluent), also within noise, on a metric limited by label conflicts and advisory only.

Limits: groups of 7-25 tickets cannot detect gaps smaller than about 20 points, so "no evidence of a gap" is weaker than "no gap". Fairness of the drafts themselves (tone, correctness by group) was not assessed.
