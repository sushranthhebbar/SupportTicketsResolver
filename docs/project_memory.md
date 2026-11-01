# Project Memory

_Last updated: 2026-11-01_

## FR-09 classification requirement

The Build Specification requires every ticket to be classified for intent and urgency with numeric confidence values (A3). The user has added this capability to Stage 2 as FR-09.

Requirement added to Stage 2:

> **FR-09:** The system shall assign each ticket an intent and urgency label, with a numeric confidence score for each classification.

Acceptance criteria recorded for FR-09:

- Every processed ticket has intent and urgency labels and a confidence value between 0 and 1 for each.
- Labels use the project-defined categories.
- Report classification precision and recall per class on held-out labeled data; target at least 85% precision per class, per the Evaluation Framework.

Traceability: Discovery §1 (Marcus needs a reliable ticket-mix breakdown); Discovery §2 (ticket data includes intent and urgency labels); Build Specification A3; Evaluation Framework (classification precision target).

**Status:** The user has added FR-09 to Stage 2. Update the revision log as appropriate; treat the requirement as active.

**Open design questions:** How low-confidence classifications should affect routing; how confidence calibration will be checked.

**Dependency:** Classifier prompt PR-03 is now traceable to FR-09.

## Prompt library progress

- PR-01: Requirement-to-specification drafter, design-time prompt, drafted for the Prompt Library.
- PR-02: Grounded Reply Drafter, build prompt for FR-03 and FR-05, drafted for the Prompt Library.
- PR-03: Ticket Classifier, build prompt for FR-09, drafted for the Prompt Library.
- Open before implementation: define low/medium/high urgency guidance and specify how raw model confidence is calibrated before routing.
- Specifications for FR-01 through FR-08 have been drafted in the conversation; FR-09 specification was drafted in the conversation and the user added the requirement to Stage 2.

- PR-04: Escalation Summary Builder, build prompt for FR-06, drafted for the Prompt Library.


## Prompt quality review and traceability

Stage 3 Sections 3–4 have been drafted in the conversation for manual entry. PR-02, PR-03, and PR-04 were reviewed against the prompt-quality checklist. Proposed test IDs have been mapped to FR-01 through FR-09; these are plans, not implemented tests.

Open items before relying on the prompts: define low/medium/high urgency guidance; calibrate classifier confidence outside the prompt and verify calibration; create representative prompt examples; resolve requirement-level thresholds and workflow details noted in the traceability table.
User confirmed Sections 3–4 are complete in the Word workbook. The test-case IDs remain proposed plans; no tests have been added or run from this work.

## Week 2 schedule

User confirmed the Week 2 day-by-day plan (Stage 4, Section 3) is complete in the workbook. Planned Week 2 backlog work totals 22 hours against a maximum availability of 24 hours, leaving 2 hours of contingency. The full unattended evaluation run is scheduled for Friday. Other commitments and unavailable days were not specified.

## Monday implementation progress

- Added `src/tickets.py` with `NormalizedTicket`, `TicketRecord`, `normalize_ticket`, and `load_ticket_records`.
- The normalized runtime ticket omits evaluation-only `labels` and outcome `history`; those remain separate on `TicketRecord` for offline evaluation.
- Development (500 records) and validation (80 records) were loaded in a one-off smoke check. Both cover all four supported channels, and one normalized sample per channel was printed.
- Updated the README repository map and architecture notes, including the exact normalized record fields.
- Existing setup verifier: retrieval index, SQLite, and Prometheus checks passed on the elevated rerun. Chroma emitted non-fatal telemetry compatibility warnings. The clean-copy dependency install was stopped at the user request. The existing project environment passed the full test suite (14 tests) and the setup verifier. Clean-checkout installation remains unverified.



## User-run verification confirmation

On 2026-11-01, the user reran the documented commands in the project environment:

- `python -m pytest tests/ -v`: all 14 tests passed, including the new ticket normalization tests.
- `scripts/verify_setup_steps_4_6.py`: retrieval, SQLite, and Prometheus checks all passed.

Chroma emitted telemetry compatibility warnings (`capture() takes 1 positional argument but 3 were given`), but the verifier continued and completed successfully. Clean-checkout dependency installation remains unverified; the temporary install was stopped at the user's request.

## Tuesday implementation progress

- Reviewed the retrieval layer: the setup verifier previously indexed 59 passages from 29 articles and returned the expected source `DOC-AUTH-001` for its known query.
- Added `src/evaluation.py` and `scripts/run_evaluation.py`. The harness accepts arbitrary input/output paths and a processor function (`module:function`), gives the processor only `NormalizedTicket`, writes per-ticket JSONL plus a metrics JSON report, and records per-ticket errors without stopping the run.
- The report distinguishes historical ticket baselines from observed system outcomes, reports per-class classification, routing, retrieval, latency, and safety metrics where processor data is available, and marks human-review or unconnected metrics as unavailable rather than inventing them.
- Updated architecture and README documentation with the harness interface. The sample CLI command requires a pipeline processor that has not been implemented yet.
- The user ran the evaluation harness tests and reported all passing. The 120-ticket hidden evaluation set is not distributed; the provided validation file has 80 tickets.
- Added `tests/test_evaluation.py` with two focused harness tests: report/results generation plus no label leakage, and per-ticket error recording with continuation. The user manually ran these tests and confirmed they passed.

User manually ran `tests/test_evaluation.py` and confirmed all tests passed. The user subsequently confirmed the full suite contained 16 tests before Wednesday's additions.

## Wednesday implementation progress

- Added `src/classification.py` with the project intent categories, low/medium/high urgency guidance, structured-output validation, and OpenRouter request integration. Only normalized ticket fields are sent; dataset labels remain withheld.
- Added `src/routing.py` and `src/pipeline.py`. Security incidents and high-urgency tickets escalate. Other tickets require both calibrated confidence values to meet the 0.80 threshold for auto-response; without a calibration artifact they go to human review. The pipeline writes classification and routing decisions to SQLite (two records per ticket).
- Documented a calibration approach using a dedicated development-data calibration split, isotonic regression, reliability bins, Brier score, and held-out per-class precision. Do not tune against the final evaluation set.
- Added `scripts/run_classification_sample.py` and ran it against the first 20 validation tickets using the configured `openrouter/free` model. Results: 20 rows; 40 decision records covering all 20 ticket IDs; 2 escalated and 18 sent to review. On this small inspection sample, intent matched 17/20 labels and urgency matched 7/20. This is diagnostic only, not the full evaluation; urgency behavior needs review before relying on it.
- Added four classification/routing/pipeline tests in `tests/test_classification_routing.py`. The user ran the suite inside `.venv311` and confirmed all tests pass. The suite now has 20 tests. Command: `.\\.venv311\\Scripts\\python.exe -m pytest tests/ -v`.
- User accepted the operational urgency rubric defined from a diverse development-set spectrum. It uses time-to-harm/consequential deadline: high requires immediate action against material harm; medium is a real but bounded/workable current problem; low has no current material harm or consequential near-term deadline. Urgency wording alone, customer tier, intent, route, and historical outcomes are not proxies; ambiguous cases default to medium with low confidence and review.
- Development-data audit found that among 97 exact repeated subject/body groups, 67 carried conflicting urgency labels (e.g. the same compliance request was low and medium). User rejected relabeling these as a bad approach because hidden evaluation labels may also conflict. The generated reconciled copy, script, and report were discarded; supplied labels remain unchanged. The classifier should flag unclear or conflicting urgency evidence and route those tickets to human review. The 7/20 validation-sample match remains diagnostic only because validation labels have not been audited.
- Updated PR-03 to v2 to require a short urgency evidence excerpt or explicit ambiguity flag. Unsupported evidence or an ambiguous urgency judgment routes to human review even if a calibrated score is high. Evaluation reports repeated-text urgency-label conflicts without rewriting labels. Added tests for these behaviors. User confirmed all 21 tests pass inside `.venv311`; command: `.\\.venv311\\Scripts\\python.exe -m pytest tests/ -v`.
- User clarified that the ticket does not supply an ambiguity flag: the classifier must infer and return it based on ticket evidence, and routing consumes that model output. Code/docs/tests now explicitly distinguish the input ticket from the classifier's assessment.
- User requested a diverse behavioral evaluation on original development data. Added `scripts/run_urgency_spectrum_sample.py`: 18 varied examples plus 6 exact-text pairs with conflicting reference urgency labels. It passes only normalized tickets to the classifier, writes reference labels separately for offline comparison, and summarizes ambiguity/evidence/route outcomes. The live sample has now been run; findings follow.
- Ran the 30-ticket PR-03-v2 development sample. All 30 completed with no API errors; 4 were flagged urgency-ambiguous, 1 evidence quote was unsupported, and routes were 4 escalate / 26 review (no calibrated confidence artifact, so none auto-responded). Raw urgency matched 12/30 supplied labels, descriptive only because labels conflict and have not been fully audited. Within the 6 exact-text conflict pairs, 2 pairs received different urgency predictions; 1 prediction in those pairs was marked ambiguous. The `openrouter/free` alias dispatched 7 distinct underlying models, so the sample is not a controlled reproducibility/quality evaluation. Results: `evaluation/results/urgency_spectrum_development.jsonl` and `.report.json`. No pytest suite was run.

## Thursday implementation progress

- Added `src/answering.py` and PR-02-v1 for documentation-grounded, agent-reviewed reply drafts. The model receives only the ticket and retrieved passages, treats both as untrusted data, and returns a structured evidence decision, draft, source IDs, reason, and next step.
- Added `src/guardrails.py`: no-hit and insufficient-evidence paths return a blank draft and clarification/escalation recommendation; citations must match retrieved source IDs and inline citations; credential-like or prompt-injection-like response text is blocked; malformed output, timeout, provider errors, and rate limits fail safely.
- Integrated retrieval, drafting, safe routing overrides, and answer decision logging in `src/pipeline.py`. Drafts are never sent to customers. Added eight answer/guardrail/pipeline tests. User manually ran the suite inside `.venv311` and confirmed all 29 tests pass. Command: `.\\.venv311\\Scripts\\python.exe -m pytest tests/ -v`.

