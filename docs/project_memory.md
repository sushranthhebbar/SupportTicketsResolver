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

## Current pending work (2026-11-01)

- **Verification:** User confirmed all 29 tests pass inside `.venv311`. Verify the README command and CI workflow during the planned Friday evaluation task.
- **Friday sprint gate:** Run the full unattended evaluation and review metrics/failures. The hidden 120-ticket evaluation set is not distributed; the supplied validation set contains 80 tickets, so the hidden-set run is blocked until that data is available.
- **Urgency quality (parked by user):** Revisit later. The 30-ticket sample matched 12/30 supplied urgency labels, but labels can conflict and `openrouter/free` dispatched seven underlying models. This is diagnostic only, not a reliable quality score. Preserve labels; report conflicts and route model-detected ambiguity to human review.
- **Confidence calibration / FR-09:** No calibration artifact exists. The target of at least 85% per-class precision and recall has not been demonstrated on reliable held-out labels. Until calibrated confidence is configured, non-urgent cases remain in human review.
- **Remaining product tasks:** FR-06, FR-04, FR-07/FR-08 implementations are complete and user-verified by passing tests. The initial monitoring dashboard is implemented; its focused tests await the user's manual run. Complete the fairness audit and report/video/submission package.
- **Setup:** Clean-checkout dependency installation remains unverified. The existing project environment passed user-run tests. Chroma previously emitted non-fatal telemetry compatibility warnings.

## Friday evaluation attempt (2026-11-01)

- Verified the README's offline test command and `.github/workflows/ci.yml`: CI uses Python 3.11, installs `requirements.txt`, and runs `python -m pytest tests/ -v` without credentials. Updated the README's local test command to invoke `.venv311` directly.
- Ran the full pipeline evaluation on the supplied 80-ticket validation set using `openrouter/free`; output is in `evaluation/results/validation_2026-11-01.jsonl` with report `evaluation/results/validation_2026-11-01.report.json`.
- Reproduction command from the project root (uses the project virtual environment): `.venv311\Scripts\python.exe .\scripts\run_evaluation.py --input evaluation\data\validation_tickets.json --output evaluation\results\validation_2026-11-01.jsonl --processor src.pipeline:process_ticket --system-version 0.1`.
- Artifact verification command: `.venv311\Scripts\python.exe .\scripts\verify_evaluation_artifacts.py --input evaluation\data\validation_tickets.json --results evaluation\results\validation_2026-11-01.jsonl --report evaluation\results\validation_2026-11-01.report.json`.
- Provider throttling prevented completion: 6/80 tickets succeeded, 73 calls returned HTTP 429, and one response lacked the expected `choices` field. The hidden 120-ticket evaluation set remains unavailable. This is an incomplete operational run and must not be treated as a quality result.
- Updated metric calculation to exclude processor failures from classification, routing, retrieval, citation, and safety denominators; reports now expose successful scoring coverage and excluded failures. Added `scripts/verify_evaluation_artifacts.py`, which checks ID coverage/order, duplicates, label/history isolation, and agreement between JSONL and report counts. Verification ran and correctly failed the incomplete run (6/80; 74 processor errors).
- Manual test run still needed after these code changes: `.venv311\Scripts\python.exe -m pytest tests/ -v`. User will run it and report results.
- Follow-up: repeat the unattended evaluation after provider rate limits clear or with a controlled model/quota; then rerun the artifact verifier. Do not rely on the 6-ticket metrics.
- User subsequently ran the test suite inside `.venv311` and confirmed all 29 tests pass.

## Product implementation, step 1: FR-06 escalation summaries (2026-11-01)

- Confirmed the Stage 2 PRD criterion: summaries include the issue, relevant ticket history, troubleshooting attempted, relevant documentation, and unresolved uncertainty; distinguish ticket facts from system inferences; and flag missing troubleshooting instead of inventing it.
- Added `src/escalation.py` to assemble a structured summary from the normalized ticket, optional conversation history and agent-supplied troubleshooting, retrieved documentation, and routing/classification assessment. Missing context is explicitly marked. Summary is tagged for agent review.
- Integrated summaries on escalation routes in `src/pipeline.py`; retrieval sources and the full summary are persisted in the SQLite decision log under `FR-06` and returned to callers. Summary generation is deterministic and does not make another model call.
- Added two FR-06 tests in `tests/test_escalation.py` and updated README/architecture documentation. Tests have not been run; the user should run `.venv311\Scripts\python.exe -m pytest tests/ -v` and report the result before we move to the next implementation step.
- The agent UI needed to actually review/edit/approve the summary remains part of the subsequent FastAPI/FR-04 step.
- User subsequently confirmed the test suite passed after the FR-06 additions.

## Product implementation, step 2: FR-04 agent review (2026-11-01)

- Confirmed PRD acceptance: agents can review, edit, reject, or approve a draft before sending; approved customer-facing responses must disclose AI assistance and include sources. This local prototype does not send customer messages.
- Added authenticated FastAPI endpoints in `src/app.py` and a browser review page at `/review` to list/read pending drafts and edit, approve, or reject a draft. The documented local launch binds to loopback; review endpoints require `AGENT_API_TOKEN`.
- Added `src/review_store.py` with persistent `agent_reviews` state, append-only `agent_review` decision records, final-state protection against changing approved/rejected drafts, and renewed citation/safety validation after edits and before approval. Approval returns a reviewed draft with the disclosure statement and retrieved source IDs.
- Persisted source titles and passages with draft decisions so agents can check the cited evidence in the review page.
- Added three API workflow tests and documented configuration/usage. User's first test run showed all other tests passing but the three API tests errored during setup because installed Starlette `TestClient` passed the removed `app=` argument to the installed httpx client. Replaced those tests with async `httpx.AsyncClient` and `ASGITransport`; user rerun is pending. Command: `.venv311\Scripts\python.exe -m pytest tests/ -v`.
- Access/retention policy and the final wording of the AI disclosure remain client decisions from NFR-04/FR-04; the prototype uses a shared bearer token and a proposed default disclosure.
- Added a random local `AGENT_API_TOKEN` to the ignored `.env` without printing it. Started the app on loopback port 8000; `/review` returned HTTP 200 and the user confirmed the page is visible. The server session must remain running while the user uses the page.
- User reran the full suite after switching the API tests to `ASGITransport` and confirmed all tests pass.

## Product implementation, step 3: FR-07/FR-08 outcomes and feedback (2026-11-01)

- Confirmed the PRD criteria: authorized reviewers need the sources shown, generated draft, and agent decisions; assisted-ticket records must capture available outcomes and feedback and support reporting by customer tier and language fluency without claiming AI caused an outcome.
- Added an authenticated per-ticket decision-history endpoint exposing timestamped stage, model, prediction, source IDs, actions, reasons, guardrail results, and requirement traceability. The browser review page now displays the ticket's history, including the original generated draft.
- Added `src/outcome_store.py` with an assisted-ticket-only outcome and feedback table, append-only outcome event logging, partial updates, and descriptive summaries for FCR, escalation, repeat contact, resolution time, CSAT, and feedback categories grouped by customer tier and language fluency.
- Added authenticated outcome read/write endpoints and an outcomes summary endpoint. The review page includes fields for observed outcomes and agent feedback. Outcome summaries explicitly state that they do not establish causality.
- Added an agent escalation action in the review flow and included it in the append-only ticket history; it records intent but does not invoke an external handoff.
- Added tests for decision-history visibility, outcome capture, grouped reporting, escalation logging, and validation. On 2026-11-01 the user confirmed the tests pass; they ran inside `.venv311` with `.venv311\Scripts\python.exe -m pytest tests/ -v`.

## Product implementation, step 4: monitoring dashboard (2026-11-01)

- FR-07/FR-08 implementation is verified by the user's passing test run.
- Added `src/dashboard.py` and authenticated `/api/dashboard/summary`, plus `/dashboard` with daily ticket volume, routing, intent/urgency/channel mix, guardrail failures, observed outcome coverage, and customer-tier/language-fluency outcome tables.
- Outcome reporting is descriptive and makes no AI causality claim. The dashboard reports latency as unavailable because the current pipeline does not persist per-ticket latency; it does not substitute zero or infer a value.
- Added channel to newly persisted classification records so channel mix can be reported. Older records without channel context are naturally excluded from that breakdown.
- Added `tests/test_dashboard.py` for the aggregate summary, coverage, guardrail counts, page availability, and authentication. Static verification passed: `git diff --check` and AST parsing for the changed Python modules/tests.
- User's first manual full-suite run reported one failure in `test_outcomes_require_assistance_and_valid_ranges`: a fresh SQLite database had no `decisions` table, and outcome capture raised `sqlite3.OperationalError` before it could return the expected `OutcomeNotFound`. Fixed outcome capture to initialize the decision schema before checking assistance; also made dashboard summary initialize the schema so an empty database can render. User subsequently confirmed all tests pass after the fix, using the documented `.venv311` environment.
- The API was not running during dashboard implementation. To launch/reload it from the project root: `.venv311\Scripts\python.exe -m uvicorn src.app:app --host 127.0.0.1 --port 8000`; then open `http://127.0.0.1:8000/dashboard` and enter the local `AGENT_API_TOKEN` from `.env` to load data.
- Next product step after dashboard verification: fairness audit. Governance criteria call for comparing ticket count, resolution rate, quality, variation from the best segment, and explanation across enterprise/business tier, fluent/non-fluent English, and short/long-complex tickets. Remaining delivery work includes the report/video/submission package.

## Evaluation provider change (2026-11-02)

- User prefers Groq over OpenRouter for the validation run and identified the Groq **free-tier** limits for `qwen/qwen3.8-27b`: 30 RPM, 1,000 RPD, 8,000 TPM, and 200,000 TPD. Groq's current model documentation confirms Qwen 3.8 27B supports JSON Object Mode, which matches the runtime request format. The request/day budget should be ample for the 80-ticket run; token throughput remains the likely constraint.
- Added provider-neutral `MODEL_API_KEY` / `MODEL_API_URL` resolution with fallback support for `GROQ_API_KEY` and the legacy OpenRouter variables. Updated `.env.example` for Groq/Qwen and added `scripts/test_model_provider.py` as a one-request connection/JSON-mode smoke check.
- Added provider configuration unit tests. User confirmed the full test suite passes after these changes, using `.venv311`. The actual validation rerun has not happened; user must place a Groq API key in `.env`, then run the connection check before the evaluation.
- RPM and daily request caps are not the only possible limits: the reported 8K TPM may govern throughput. The evaluation is sequential, but the current client does not explicitly pace by token usage or retry 429 classification requests. Do not promise a throttle-free run based on request-count caps alone.

