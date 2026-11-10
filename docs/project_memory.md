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
- User ran the provider smoke command, but its output showed it was still using the legacy OpenRouter URL/model (`openrouter.ai`, an `openrouter/free`-routed `nvidia/...:free` response) rather than Groq. The returned message content was `None`; the script previously treated this as success. Updated the smoke check to fail on empty/non-text content and report configured versus provider-reported model. User needs a Groq API key in `.env` before rerunning the smoke check. Groq evaluation remains pending.
- User requested that `.env` be switched to Groq before having a Groq API key. Updated local ignored `.env` with the Groq URL and Qwen model plus the documented API-key placeholder; preserved the old OpenRouter secret and made the placeholder take precedence. Added a credential guard so the placeholder is refused before any provider request. Groq free tier still requires generating an API key in GroqCloud; no real key was created or written by Codex.
- User subsequently created/entered a Groq credential locally. Verified only that a non-placeholder key is configured (never printed it). The one-request smoke check succeeded against `https://api.groq.com/openai/v1/chat/completions` using `qwen/qwen3.8-27b` and received valid JSON. The first attempt surfaced a missing "JSON" instruction in the smoke prompt; fixed it before the successful retry. Full 80-ticket evaluation has not yet been run.
- The placeholder guard and smoke-prompt fix were added after the user's prior full-suite pass confirmation. Do not claim the latest changes are test-verified until the user reruns `.venv311\Scripts\python.exe -m pytest tests/ -v`.
- User ran the Groq validation command: 18/80 tickets completed; 62 failed with HTTP 429 and the artifact verifier correctly failed. Added bounded HTTP-429 retry handling shared by classification and drafting: honors `Retry-After`, otherwise exponential backoff (configurable with `MODEL_429_MAX_RETRIES` and `MODEL_429_FALLBACK_SECONDS`, default five retries and a five-second initial delay). This cannot overcome exhausted quotas or persistent provider-side limits. Added focused retry tests; user must rerun `.venv311\Scripts\python.exe -m pytest tests/ -v` before another evaluation attempt. Preserve the first failed artifacts at `evaluation/results/validation_2026-11-02.jsonl` and `.report.json`; use a distinct `-retry` output for the next run.
- Added console logging for evaluation progress (ticket count, ID, per-ticket duration or error) and HTTP 429 retries (retry number and wait duration); the evaluation CLI enables timestamped INFO logging. Static verification passed with `git diff --check` and Python AST parsing. User should run the full suite inside `.venv311` before the next evaluation attempt.
- User's next evaluation log showed repeated transient 429s and successful retries; no quota headers were logged to distinguish RPM from TPM. Added a three-second minimum gap between model requests in the evaluation CLI (about 20 RPM), while keeping standalone/test calls unpaced by default. 429 warnings now print provider request/token remaining and reset headers when available. This still cannot prevent token quota exhaustion; next run's headers should clarify the cause. CLI supports `--model-request-interval` to tune the gap.
- User's paced run still saw 429s. Logs show request quota remaining around 935–943 with request reset over an hour away, while token reset timers were 37–54 seconds. This points to token throughput (8K TPM) as the likely limiter. Retry logic now waits for the longer of `Retry-After` and `x-ratelimit-reset-tokens` when available; added a focused test for Groq's reset-duration format. User should rerun tests and evaluate with a new output path.

## Validation evaluation results (2026-11-02)

- The user completed the paced 80-ticket evaluation with Groq `qwen/qwen3.8-27b`. Artifacts: `evaluation/results/validation_2026-11-02-paced.jsonl` and `evaluation/results/validation_2026-11-02-paced.report.json`.
- The artifact verifier passed: 80/80 tickets in the expected order, unique IDs, no processing errors, and no evaluation labels/history leaked into processor outputs.
- Quality assessment from the results: intent exact accuracy 71/80 (88.8%); intent macro precision 86.3% and macro recall 87.5%. Urgency exact accuracy 36/80 (45.0%); after excluding seven tickets in three duplicate-text label-conflict groups, 34/73 (46.6%). The conflicts are documented in the report and affect the interpretation, but do not account for most urgency errors.
- Routing exact accuracy was 7/80 (8.8%): the system chose `review` 63 times and `escalate` 17 times; expected labels were `auto_respond` or `escalate`. This indicates a strongly conservative behavior and poor alignment with expected routing on this dataset. There were zero unsafe auto-response violations, but also zero auto-responses, so that safety metric does not demonstrate safe auto-response performance.
- Retrieval hit rate on answerable tickets was 52/53 (98.1%); citation document-ID match rate was 81.8% (a document-level proxy, not sentence-level support). Business outcomes, hallucination rate, confidence calibration, and latency percentiles are unavailable/unmeasured in the report; do not infer them from the historical baseline or model confidence.
- Next evaluation work: investigate urgency confusion and route/action policy alignment before claiming operational readiness; conduct human review of citation support and complete the fairness audit. The existing report should be treated as baseline quality evidence, not as all predictions passing.

## Citation validation follow-up (2026-11-03)

- Updated citation handling so persisted citation IDs are derived only from inline IDs verified against sources retrieved for that ticket. Missing inline citations and IDs absent from retrieval still fail closed; a disagreement in the redundant structured citation array is reconciled and recorded.
- Updated PR-02 to v2 with an explicit two-way match requirement between inline citation IDs and the structured `citations` array.
- Ran two separate 12-ticket answerable development probes, preserving the first run and the PR-02-v2 run as separate artifacts. Both completed 12/12 with no processor errors. Each produced 6 draft-ready, 2 human-review, and 4 not-generated outcomes. Neither sample had a structured/inline citation mismatch; each had one ticket blocked for missing inline citation. This small sample does not establish an improvement in citation metrics. Do not treat it as validation or use it to revise held-out results.
- Artifacts: `evaluation/results/development_citation_probe.jsonl` / `.report.json` (before PR-02-v2) and `evaluation/results/development_citation_probe_v2.jsonl` / `.report.json` (PR-02-v2). The 80-ticket validation set was not rerun.
- Follow-up probe: 16 new answerable development tickets, excluding the first 12, completed with 0 processing errors. Results: 9 draft-ready, 2 human-review, 5 not-generated; zero structured/inline citation mismatches were reconciled; two drafts were blocked for missing inline citations. Citation document-ID match proxy was 62.5% on this small sample. A local source-text spot check found extra cited documents supporting claims in several drafts (for example, export timing and API-key removal guidance absent from the single expected-document label). Thus this proxy can penalize relevant citations when reference IDs are incomplete; it does not measure sentence-level support. Do not shorten citations to improve the score without human support review. Artifact: `evaluation/results/development_citation_probe_v2_16.jsonl` and `.report.json`. Validation remains untouched.
- Urgency review of that same 16-ticket sample: 11/16 predictions matched supplied labels. Four mismatches were expected `medium` / predicted `low` (data residency confirmation, long manual export, billing-period reconciliation, CI setup); one was expected `low` / predicted `medium` (single-user console login failure). The four medium cases have active tasks or difficulties, consistent with the project rubric's “real current issue” band, while the low-labeled login failure also appears to be a real bounded issue. Treat these as rubric/label alignment questions, not clear model mistakes; preserve supplied labels and inspect this definition before changing PR-03. No new model run was made for this urgency analysis.

## PR-03 prompt check (2026-11-04)

- PR-03-v3 prompt experiment: added active-problem vs routine/planned-work clarification and ran classification-only on the same 16 tickets. One provider response returned invalid intent `rollback`, leaving 15 paired tickets. PR-03-v2 scored 10/15 urgency matches and v3 also scored 10/15; v3 fixed one medium case and changed one previously correct low case to medium. The candidate did not pass the no-regression gate, so runtime/docs were restored to PR-03-v2. Artifacts: `evaluation/results/urgency_pr03_v3_16.jsonl` and `.report.json`.

## Evaluation scope clarification (2026-11-04)

- The user confirmed the hidden 120-ticket assessment set will never be provided to this project. Treat this as permanently inaccessible, not pending.
- Use the 500 supplied development tickets for prompt/policy exploration and the supplied 80-ticket validation set for final local comparisons. Do not tune changes against the validation set. Make no hidden-set run claims; describe it as externally assessed but unavailable for local reproduction.


## Confidence calibration implementation (2026-11-05)

- Added `src/calibration.py`, `scripts/collect_calibration_predictions.py`, `scripts/fit_calibration.py`, `tests/test_calibration.py`, and pipeline wiring (`CALIBRATION_ARTIFACT`, explicit opt-in; version-matched; `calibration_version` in routing output). Offline tests pass (46 passed in a scratch Python 3.9 venv, excluding three modules that need chromadb/pytest-asyncio; the full suite still needs a run in `.venv311`).
- **Calibration has not been run on real data.** The implementation was developed in a checkout without `.env`/provider key, so no live predictions exist yet and no calibration artifact has been produced. The fit script was smoke-tested only on synthetic predictions (not committed). Do not claim calibrated metrics until the collection and fit steps are run with the Groq key.
- Expected constraint: urgency accuracy is ~45% against noisy labels, so calibrated urgency confidence may never reach 0.80 and auto-response may stay disabled. If so, report that honestly rather than lowering the threshold; the threshold must be chosen from held-out precision (target >= 85% per class), never the validation set.

## Confidence calibration results (2026-11-05)

- Collected live PR-03-v2 predictions (`qwen/qwen3.8-27b`, Groq) for the whole eligible development pool: 343 attempted, 341 classified (errors: DEV-0114 HTTP 400; DEV-0487 non-boolean `urgency_ambiguous`). Artifact `evaluation/calibration/calibration-v1.json` fitted on 251 tickets, evaluated on 90 held-out tickets (hash split by text). Validation tickets were not used.
- Fix during fitting: isotonic blocks with fewer than 10 observations are pooled into a neighbor (a single-ticket 0.98 urgency block had calibrated to 1.0).
- Held-out intent: accuracy 84.4%, Brier 0.140 raw -> 0.128 calibrated; calibrated values 0.83 (raw 0.65-0.95) and 0.94 (raw 0.98). Precision at the 0.80 threshold is 84.4% (n=90), below the 85% target; per-class precision is not demonstrable (19 predicted classes, only 2 with >= 10 selections).
- Held-out urgency: accuracy 55.6%, Brier 0.317 -> 0.260. Calibrated urgency never exceeds 0.66, so no ticket reaches the 0.80 threshold: **auto-response stays disabled**. The model's raw urgency confidence (0.85-0.95) was overconfident; calibration corrects this.
- The artifact has NOT been activated (`CALIBRATION_ARTIFACT` unset). Activating it would not change routing today. The 0.80 threshold was left unchanged. Next lever for auto-response is urgency quality, not the threshold.

## Scenario re-split and intent-definition prompt (2026-11-06)

- Per `docs/development_error_analysis.md` (development data only): urgency 47.5% (50.8% conflict-free), indistinguishable from always-medium (47.8%); the hash-by-text split leaked (87 of 90 held-out tickets had a paraphrase in `fit`). Added `src/scenarios.py` (text-only paraphrase clustering, 79 scenarios; 0 scenarios straddle the new split). `fit_calibration.py` now uses it; `calibration-v1.json` is superseded by `calibration-v2.json` (not active). v2 held-out (81 tickets, ~24 scenarios): intent accuracy 92.6% (Brier 0.064 raw -> 0.071 calibrated, no improvement), urgency 46.9% (Brier 0.370 -> 0.257, max calibrated urgency 0.72 < 0.80). Auto-response still disabled.
- Added PR-03-v4 (PR-03-v2 + intent definitions/tie-breaks, urgency text unchanged) as an opt-in experiment (`prompt_version="PR-03-v4"`); runtime default remains PR-03-v2. Exposed/misused keys stay `security_incident` for escalation safety. Added `scripts/compare_prompt_runs.py` (paired intent AND urgency comparison, McNemar, scenario-level counts, pre-registered H1 criteria: integration_help recall >= 50%, macro recall >= 0.87, no class loses > 10 points, net gain >= 10 tickets).
- **The PR-03-v4 run has not been executed** (needs live Groq calls; ~340 calls over possibly two days). No v4 results exist. The comparison script was smoke-tested only by comparing the baseline with itself (reproduces 85.6% intent / 47.5% urgency).

## Routing rule: must-not-auto-respond intents (router-v2)

`route_ticket` now escalates `security_incident`, `compliance_request`, `feature_request` and `unclear_request` regardless of urgency or calibration. In the development labels `must_not_auto_respond` is exactly this intent set and every such ticket has `expected_route=escalate`. Replayed offline on the 341 stored PR-03-v2 development predictions: 0 must-not tickets would be auto-answered (previously 30 of 64 would have been once calibration was enabled), exact route accuracy 21.7% (was 8.5%). Evaluation also reports `routing_accuracy_review_counts_as_human` (40.8%) and a route confusion table, because `review` can never match the two-valued `expected_route`. Residual error is 172 `auto_respond` tickets sent to review (auto-response is disabled until calibration reaches 0.80) and 30 sent to escalate by high urgency.

## Routing: urgency advisory (router-v3)

Reference docs (Dataset Guide: urgency is for "prioritisation"; Brief Figure 5 has one classification-confidence gate and no urgency branch; Sprint Plan: urgency definitions unsettled) plus development evidence (urgency ~47.5% vs 47.8% always-medium; calibrated urgency never reaches 0.80) led to: auto-response is gated on calibrated intent confidence only. `auto_respond` means "draft for agent review"; nothing is sent. Must-not intents, high urgency and ambiguous urgency evidence rules are unchanged.

Offline replay with calibration-v2 (not active) on stored PR-03-v2 development predictions: holdout (n=81) exact route 69.1%, 0 must-not tickets auto-answered; fit (n=260) 69.6%, 8 must-not tickets auto-answered (gold compliance/feature/unclear predicted as another intent). Of 224 auto-routed tickets overall, 186 (83%) had the right intent, and 61 had expected_route=escalate (non-must-not; labels follow answerable_from_docs/history), which the retrieval and guardrail stages must catch and this replay cannot test. Enabling the artifact is still a separate, reviewed step.

## Routing: urgency purely advisory (router-v4)

Decision (user): urgency is for agent prioritisation only. High urgency does not imply complexity, so it no longer escalates, and ambiguous/unsupported urgency evidence no longer forces review. The pipeline returns `advisory_urgency` (label, confidence, evidence, evidence_valid, ambiguous). Identical texts with different urgency labels come from different customers (95 of 97 groups), so urgency plausibly depends on customer context absent from the ticket; customer tier does not explain it.

Offline replay with calibration-v2 (not active) on stored development predictions: holdout n=81 exact route 72.8%, 0 must-not auto-answered; fit n=260 75.8%, 8 must-not auto-answered (intent misclassified). 281 of 341 auto-routed, 236 (84%) with correct intent; 82 auto-routed tickets were expected to escalate (labels follow answerable_from_docs/history), which retrieval/guardrails must catch and this replay cannot test. The UI does not yet display `advisory_urgency` or sort by it.

## Urgency reporting and review queue (advisory)

- Review queue/drafts now carry `advisory_urgency` (from the logged classification decision); the pending queue is ordered high > medium > low > unknown, and `static/review.html` shows the label, ambiguity flag and evidence, labelled advisory. `tests/test_review_urgency.py` covers it (the HTTP review tests need httpx/pytest-asyncio, not in the local venv).
- `technical.urgency_noise_analysis` in the evaluation report gives exact accuracy, within-one-level accuracy, mean absolute level error, the noise ceiling, and accuracy on conflict-free vs conflicting-text tickets. Labels are unchanged.
- Development PR-03-v2 (n=341): exact 47.5%, conflict-free 49.8% (n=251), conflicting-text 41.1% (n=90), ceiling 88.9%, within-one 95.6%. Always-medium on all 500: exact 45.2%, ceiling 84.0%, within-one 100%. Conclusion: repeated-text conflicts only cap exact accuracy near 85-89%, so they do NOT explain 47.5%; most of the gap is that the labels are not predictable from the text. Within-one is uninformative with three levels (always-medium scores 100%), so report it only next to exact accuracy and the baseline.

## Pointer

Findings from the urgency/label-noise discussion (auto_respond meaning, repeated-text analysis, tier does not explain urgency, interpretation of 47.5%, advisory decision) are consolidated in `docs/urgency_and_label_noise.md`. Correction to earlier wording: repeated-text conflicts are not "the" noise explaining poor urgency accuracy; they cap exact accuracy near 85-89% only.


## Accuracy uncertainty and fairness (development)
Cluster-bootstrap intervals and a group breakdown are in `docs/accuracy_uncertainty_and_fairness.md` (script `scripts/analyze_accuracy_uncertainty.py`). Intent 85.6% has a 77-93% interval once scenario clustering is respected; urgency 47.5% (41-55%). Flagged group gaps (chat intent, docs_comment urgency, Europe intent) are leads only; no fluency or tier gap. Also: the escalation-draft probe (`scripts/probe_escalation_drafts.py`, 44 tickets) found 29 drafts on should-escalate tickets, 6 needing a person; DEV-0141 passed citation checks while misapplying docs.

## Escalation-draft probe, environment, and PR-03-v4 run (2026-11-06/07)
- **Probe** (`scripts/probe_escalation_drafts.py`, results in `evaluation/calibration/escalation_draft_probe.jsonl`): the 82 development tickets that router-v4 + calibration-v2 would auto-respond but whose label expects escalation; 44 probed live. 29 got `draft_ready`, 15 went to review (9 declined by the evidence-sufficiency check). 7 of 8 gold must-not tickets were caught; the one that got a draft is DEV-0141. Full read of the 29 drafts against the docs: 23 sound; 6 need a person (DEV-0141 conflates DOC-DATA-002 backup retention with DOC-SEC-003 audit-log export and passed every citation check; DEV-0432/0123 do not supply the written data-location confirmation asked for; DEV-0338 gives no concrete step for a two-day restore; DEV-0393 and DEV-0149 partly off). All 29 were historically escalated, so "looks correct" is judged against the docs only. Conclusion: citation checks verify retrieval, not claim correctness; agent review is the real safeguard; keep CALIBRATION_ARTIFACT off.
- **Retrieval** (357 dev tickets with expected docs): top-1 88.8%, any expected doc in top 5 95.8%, all in top 5 83.2%.
- **Intent detail** (PR-03-v2, n=341): macro F1 0.82; integration_help recall 0/13, api_key_issue 31%, compliance_request 53% (7 of 17 predicted data_export); mean intent confidence 0.958 when right vs 0.934 when wrong, so confidence barely discriminates.
- **Environment:** full `requirements.txt` installed in `.venv` (Python 3.9.6). `posthog` pinned to 2.4.2 (chromadb 0.4.22 breaks with posthog>=6). `tests/test_agent_review_api.py` and `tests/test_dashboard.py` still cannot be collected because `src/app.py` needs Python >= 3.10 (README says 3.11). Run `pytest tests` (bare `pytest` clashes with `scripts/test_model_provider.py`). 55 tests pass; `tests/test_escalation.py` was updated for advisory urgency.
- **Group gaps:** chat and Europe intent gaps trace to a few scenarios (8 clusters hold 37 of 49 errors); no evidence of channel/region bias (see `docs/accuracy_uncertainty_and_fairness.md`).
- **PR-03-v4 run** (`scripts/collect_calibration_predictions.py --prompt-version PR-03-v4 --only-ids-from ... --output evaluation/calibration/development_predictions_pr03v4.jsonl --max-tickets 100 --request-interval 12 --retry-errors`, compare with `scripts/compare_prompt_runs.py --candidate ...`). Interim, 162 of 341 paired: intent 85.2% -> 95.1%, macro recall 0.846 -> 0.939, net discordant +16 (17 fixed, 1 broken); compliance_request 33% -> 100%, integration_help 0% -> 100%, database_issue 75% -> 100%; api_key_issue unchanged at 33%; urgency unchanged (43.2% -> 44.4%). H1 currently NOT MET only because authentication_failure fell 6/7 -> 5/7 (-14 points, one ticket); final verdict needs all 341. Caveats: v4 definitions were written after reading these development errors (optimistic); gains rest on ~12 scenarios; only validation can confirm. Runtime default stays PR-03-v2; calibration-v2 is fitted to PR-03-v2 only, so adopting v4 requires refitting it.
- **Quota note:** the Groq free tier's daily token limit is shared across the probe, classification runs and any other live calls; a long 429 wait (hundreds of seconds, doubling) means stop and resume the next day. 503s are provider-side and are retried with `--retry-errors`.
- **Branch state:** `confidence-calibration` pushed after commit `a9445c1`; later doc/data changes need another push.
- **Still open:** finish the PR-03-v4 collection (179 tickets, ~2 days) and finalize H1; human citation-support review; latency and hallucination measurement; clean-checkout/Python 3.11 test check; fairness on validation; report, video, workbooks, effort log and archive.

## PR-03-v4 final development verdict (340 of 341 paired; DEV-0261 still errored)
- Intent accuracy 85.6% -> 93.2% (fixed 30, broken 4, net +26). Paired gain +7.6 points, 95% CI +1.6 to +14.7 (resampled by scenario cluster, 76 clusters; 9 scenarios improved, 4 worsened, 63 unchanged). Macro recall 0.843 -> 0.919. Urgency unchanged (47.6% -> 47.4%).
- Safety-relevant: gold must-not tickets predicted as a must-not intent 56/64 -> 64/64 (all compliance_request -> data_export errors fixed); over-escalation of other tickets unchanged at 4.
- Per class: compliance_request 53% -> 100%, integration_help 0% -> 92%, database_issue 81% -> 100%, onboarding 82% -> 100%, api_usage_question 87% -> 100%; authentication_failure 71% -> 50% (10/14 -> 7/14; three "cannot log in, password correct" tickets now predicted account_access, labels look genuinely ambiguous); api_key_issue 31% -> 23% (still weakest: 6 of 13 predicted authentication_failure, 4 security_incident).
- **H1 (pre-registered) is NOT MET** on the criterion "no class loses > 10 points" (authentication_failure -21). Other three criteria pass (integration_help 92%, macro recall 0.919, net +26). Verdict is recorded as written; do not reinterpret it after the fact.
- Remaining v4 errors: 23, all in 8 scenarios.
- Caveats: the v4 definitions were written after reading these development errors (optimistic); gain rests on ~9 scenarios; only validation can confirm.
- **Decision pending (user):** whether to adopt v4 as the runtime default. If adopted: refit calibration on the already-collected v4 predictions (`scripts/fit_calibration.py --predictions evaluation/calibration/development_predictions_pr03v4.jsonl`; calibration-v2 is v2-only), then check once on the validation set at the end and report the result either way. Runtime default is still PR-03-v2.
- Collection file: `evaluation/calibration/development_predictions_pr03v4.jsonl` (346 rows, 340 ok). Re-run with `--retry-errors --max-tickets 5` to clear DEV-0261 if wanted.

## calibration-v3 (fitted on PR-03-v4 predictions; inactive)
- `evaluation/calibration/calibration-v3.json` (fit 259 / holdout 81, scenario-level split, same as v2). Not activated; runtime default prompt is still PR-03-v2 and `CALIBRATION_ARTIFACT` is unset.
- The intent calibrator is flat: two blocks (0.85-0.95 -> 0.908, n=153; 0.98 -> 0.915, n=106). The v4 model outputs only three confidence values (0.85, 0.95, 0.98), and wrong answers occur at 0.95 (14) and 0.98 (9) alike, so the 0.80 gate rejects nothing. Holdout intent accuracy is 100% (81), so the holdout cannot test calibration; Brier raw 0.001 vs calibrated 0.008 (calibration slightly worse). Urgency calibration improves Brier (0.36 -> 0.25) but urgency is advisory and still only about 47% accurate.
- Offline replay of router-v4 (in-sample for the fit split): v2 + calibration-v2 auto-routes 281/341 (82%), of which 82 expected to escalate, 8 must-not auto-answered, 45 wrong intent. v4 + calibration-v3 auto-routes 272/340 (80%), 74 expected to escalate, **0 must-not auto-answered**, 19 wrong intent. Expected-escalate tickets that are auto-routed come from answerability and history labels, not intent errors, so classification does not remove them.
- Consequence: enabling an artifact turns on `auto_respond` for ~80% of tickets with a confidence gate that filters nothing; the effective safeguards are the must-not rule, the draft guardrails and mandatory agent review. Recommendation: keep it off unless the PRD wants drafts labelled auto_respond.

## Runtime default changed to PR-03-v4 (2026-11-09)
- `CLASSIFIER_PROMPT_VERSION` in `src/classification.py` is now `"PR-03-v4"`; `src/pipeline.py` falls back to the same constant when a classifier omits `prompt_version`. PR-03-v2 stays selectable via `prompt_version="PR-03-v2"`.
- **This was a decision, not a pre-registered pass:** H1 was NOT MET (authentication_failure recall -21 points). Rationale: intent +7.6 points (CI +1.6 to +14.7), must-not intents caught 56/64 -> 64/64, wrong-intent among auto-routed 45 -> 19; the lost class is an ambiguous label pair that routes to a human either way. Caveats stand (definitions written after reading development errors; gain rests on ~9 scenarios). Validation must be run once at the end and reported either way.
- Consequences: `calibration-v2` no longer applies to default-prompt predictions (stays a safe `review`); `calibration-v3` applies but is flat and is NOT recommended for activation; `CALIBRATION_ARTIFACT` is still unset. The collector now defaults to v4, so pass `--output` explicitly and never append v4 rows to `development_predictions.jsonl` (v2 baseline). README and `prompts/build/PR-03_ticket_classifier.md` updated; `tests/test_calibration.py` asserts both versions and the new default; 55 tests pass.

## Final validation run, PR-03-v4 (2026-11-10, run once, frozen config)
- `evaluation/results/validation_final_pr03v4.jsonl` + `.report.json`, system version `0.2-pr03v4`, calibration off (`CALIBRATION_ARTIFACT` unset). Run in two slices with `--resume --max-new-tickets 40`; verifier passed (80 ordered unique tickets, 0 errors, no labels/history in processor results).
- Intent accuracy 73/80 = 91.3% (previous v2 validation run, `validation_2026-11-02-paced`: 71/80 = 88.7%; the +2.6 points are 2 tickets, within noise). Macro precision 0.94, macro recall 0.92.
- Errors (7): api_key_issue -> security_incident x3 (safe direction, escalates), api_key_issue -> authentication_failure, account_access -> configuration_help, quota_or_overage -> billing_query, authentication_failure -> account_access. api_key_issue recall 2/6, quota_or_overage 1/2, authentication_failure 2/3: same weak classes as development.
- Must-not violations 0; guardrail blocks 0. Routing: 17 escalate, 63 review, 0 auto_respond (calibration off). Routing accuracy 17.5% strict (45 auto_respond labels landed in review), 40% counting review as human; 18 escalate-labelled tickets went to review (agent review is the safeguard).
- Retrieval hit rate 98.1% (52/53); citation document match 78.7% (proxy only).
- Urgency exact 43.8% (noise ceiling 96.3%), within one level 85.0%; advisory only.
- Latency not recorded in the report (null); hallucination rate, sentence-level citation support and confidence calibration still need human review or a calibrated output.
- Reported as measured; no tuning after seeing these results. The validation set is now spent for PR-03-v4.
- Still open: Python 3.11 test check (user), human citation/hallucination review, latency measurement, fairness on validation, report, video, workbooks, effort log and archive, push.
