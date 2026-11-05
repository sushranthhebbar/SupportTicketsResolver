# Project handoff: Support Tickets Resolver

**Audience:** Someone joining the project with no prior context  
**Project status snapshot:** 2 November 2026  
**Purpose:** Explain the problem, the repository, what works, what the evidence says, and what remains open.

> This handoff summarizes the working tree as inspected on 2 November 2026. The repository has uncommitted changes and local evaluation artifacts; see [Working-tree status](#working-tree-status) before assuming everything described has been committed or re-verified. The supplied course reference pack remains authoritative for assignment requirements.

## 1. Executive summary

This is a Python prototype for assisting CloudServe Solutions support agents. It classifies and routes support tickets, retrieves relevant knowledge-base passages, drafts source-cited replies when there is enough evidence, and prepares structured summaries for escalations. A local authenticated API and browser page let an agent review, edit, approve, reject, or escalate drafts and record observed outcomes. It is intentionally a **human-reviewed support assistant**: it does not send messages to customers.

The main operational concern is turning the current prototype into a reproducible, evidence-backed submission. The supplied 80-ticket validation run on 2 November processed only 18 tickets and failed 62 with rate limiting. The verifier correctly rejects that run as incomplete. It is not a full-run result and its small-sample metrics should not be presented as demonstrated system quality. The newest retry/backoff and progress-logging changes are in the working tree, but the project notes say the full test suite still needs to be rerun after those changes.

Other material open work: produce a complete validation run under a stable provider/quota; do a controlled urgency-quality and fairness review; implement or document confidence calibration before enabling automatic replies; verify setup from a clean checkout; finish the governance and submission artifacts (including the report, video, completed workbooks/effort log, and source archive).

## 2. The problem and why this design exists

CloudServe sells cloud infrastructure and developer-operations tools. Its support team is seeing growing volume, slow replies, low first-contact resolution, customer dissatisfaction, and workload pressure. The original ask is a chatbot, but the project brief frames the deeper opportunity as helping agents find and use existing support knowledge, while keeping people responsible for customer-facing decisions.

The supplied discovery transcription in [Discovery workbook notes](discovery_workbook.md) reports 500 development tickets. In that sample:

| Finding | Supplied sample evidence | Why it matters |
| --- | ---: | --- |
| Tickets labeled answerable from documentation | 357 / 500 (71.4%) | Retrieval and grounded drafting may reduce repeated research, if quality and controls hold. |
| First-contact resolution in historical records | 219 / 500 (43.8%) | Near the brief's 42% baseline; below the project target. |
| Repeat contacts | 108 / 500 (21.6%) | A faster response alone is not enough if issues recur. |
| Non-fluent English tickets | 120 / 500 (24.0%) | Supports explicit segment-level quality checks. |
| Urgency labels in repeated-text groups | Conflicts in 67 of 97 groups (development audit) | Exact ticket wording sometimes cannot determine the hidden urgency label. Preserve labels and report ambiguity; do not “fix” labels to improve scores. |

These are historical dataset findings, not outcomes caused by this prototype. See [Project Brief](reference/01_Read_First/01_Project_Brief.docx), [Dataset Guide](reference/05_Datasets/Dataset_Guide.docx), and [Evaluation Framework](reference/03_Reference/Evaluation_Framework.docx) for the original context and measurement rules.

## 3. What the system does

At a high level, a ticket is normalized, classified, routed, and then either escalated with context or processed through retrieval and grounded drafting. All routes produce auditable decisions. Reviewers can inspect and record the result through the local web workflow.

1. **Normalize:** `src/tickets.py` converts email, chat, documentation-comment, and forum records into a common `NormalizedTicket`. Evaluation labels and historical outcomes are kept separately and are not passed to runtime processing.
2. **Classify:** `src/classification.py` calls an OpenAI-compatible chat-completions endpoint and returns intent, urgency, raw confidence estimates, urgency evidence, and an ambiguity assessment. The model is instructed to use ticket evidence; confidence is not assumed to be calibrated.
3. **Route:** `src/routing.py` sends security incidents and high urgency to escalation. Ambiguous urgency or unsupported evidence goes to review. Other tickets require both calibrated intent and urgency confidence to meet the configured threshold (default 0.80) to auto-respond. No calibration artifact is currently configured, so ordinary tickets remain in human review.
4. **Retrieve and draft:** `src/retrieve.py` searches the 29-article corpus in `data/documentation.json`. `src/answering.py` drafts only from retrieved passages. `src/guardrails.py` checks evidence, source IDs/citations, unsafe content, and malformed or failed provider responses. Failure paths return a blank draft and a human next step.
5. **Summarize escalations:** `src/escalation.py` assembles ticket facts, supplied history, troubleshooting, retrieved documentation, system assessment, and unresolved uncertainty. Missing details are called out rather than invented.
6. **Persist and monitor:** SQLite decision/review/outcome stores record classifications, routing, draft details, source IDs, review actions, and observed outcomes. Prometheus metrics and the dashboard expose operational summaries.
7. **Human review:** `src/app.py` exposes authenticated endpoints and serves `static/review.html` and `static/dashboard.html`. The reviewer can inspect, edit, approve, reject, or record escalation; approval rechecks guardrails and records AI disclosure and citations. This prototype does not send the reply or invoke an external escalation handoff.
8. **Evaluate:** `src/evaluation.py` and `scripts/run_evaluation.py` run a processor against a supplied dataset, write per-ticket JSONL, and produce a report. `scripts/verify_evaluation_artifacts.py` checks coverage, ordering, duplicates, data isolation, and report reconciliation.

More detailed component behavior and data flow are in [Architecture](architecture.md). Prompt behavior/version notes are in [PR-02](../prompts/build/PR-02_grounded_reply_drafter.md) and [PR-03](../prompts/build/PR-03_ticket_classifier.md).

## 4. Repository map

| Path | Contents |
| --- | --- |
| `src/` | Application modules: normalization, classification, routing, retrieval, drafting, guardrails, escalation, evaluation, review API/stores, outcomes, dashboard, logging, and metrics. |
| `tests/` | Offline unit and API workflow tests. The latest change notes request a fresh full run after current rate-limit changes. |
| `scripts/` | Evaluation and verification runners, setup checks, live sample scripts, and provider smoke checks. |
| `data/documentation.json` | The 29-article knowledge corpus used by retrieval. |
| `evaluation/data/` | 500 development tickets, 80 validation tickets, and supplied reference responses. The separate hidden 120-ticket assessment set will never be provided to this project. |
| `evaluation/results/` | Dated sample/evaluation JSONL and reports; inspect each report's completion count before citing metrics. |
| `prompts/` | Runtime prompt register and versioned build prompts. |
| `docs/` | Architecture, discovery transcription, project memory, reference index, and this handoff. |
| `docs/reference/` | Preserved course-provided Word specifications, workbooks, frameworks, guides, and source datasets documentation. |
| `static/` | Browser UI for review and operations dashboard. |
| `storage/` | Generated local Chroma index and SQLite state; runtime data, excluded from Git. |
| `.github/workflows/ci.yml` | GitHub Actions workflow: Python 3.11, pinned requirements, offline pytest suite. |

## 5. Current implementation status

“Implemented” means code exists and project memory records user-confirmed passing tests at an earlier checkpoint. It does not mean the current working tree has been rerun after the newest edits.

| Area | Status as of snapshot | Notes / evidence |
| --- | --- | --- |
| Ticket normalization and evaluation/runtime label isolation | Implemented | Described in architecture and exercised in tests per project memory. |
| Retrieval over supplied documentation | Implemented | Persistent Chroma setup; earlier setup check indexed 59 passages from 29 articles. |
| Classification, urgency evidence, ambiguity, and routing | Implemented; quality unresolved | Raw confidence only. Urgency annotations conflict in duplicate text. No calibration artifact. |
| Grounded reply drafting and guardrails | Implemented | Agent-reviewed drafts only; failure/no evidence paths are safe blank drafts. |
| Escalation summaries | Implemented | Structured summary with missing context called out; no external handoff. |
| Review API and browser workflow | Implemented | Shared bearer token, local loopback launch, reviewer identity supplied by client. Access/retention decisions remain open for deployment. |
| Outcome/feedback capture and dashboard | Implemented | Summaries are descriptive, not causal. Latency is unavailable in persisted dashboard data. Focused tests exist. |
| Evaluation harness and artifact verifier | Implemented | Handles per-ticket errors and computes metrics over successful records, while surfacing excluded failures. |
| Provider neutrality and smoke check | Implemented | Supports `MODEL_API_*`, Groq fallback, and legacy OpenRouter settings. `.env` is local/private; never copy credentials into docs or logs. |
| HTTP 429 retry and progress logging | Added in current working tree | Retries honor `Retry-After`, otherwise bounded backoff; default five retries, initial fallback five seconds. Does not solve exhausted quota. Latest suite run is pending. |
| Full unattended validation | Incomplete | 18/80 successful in 2 Nov run; 62 failed on HTTP 429. Verifier fails as intended. |
| Clean checkout installation | Unverified | Existing `.venv311` has been used; clean-copy setup was not completed. |
| Fairness audit | Open | Segment reporting capability exists in outcomes; required audit analysis/report remains to be completed. |
| Course deliverables | Open / status not evidenced here | Completed stage workbooks, PRD revision log, effort log, final report, demo video, and correctly packaged archive need confirmation/completion. |

## 6. Current evaluation evidence and limits

The latest checked-in-on-disk result is `evaluation/results/validation_2026-11-02.report.json`, corresponding to `validation_2026-11-02.jsonl`.

- Input: 80 validation tickets.
- Processed successfully: 18.
- Processing errors: 62, with HTTP 429 rate limits noted in project memory.
- Artifact verifier: failed the run because coverage was incomplete. This is the correct outcome.
- On the 18 scorable tickets, report values include intent macro precision 0.909, urgency macro precision 0.620, urgency macro recall 0.544, routing accuracy 0.056, and retrieval hit rate 1.0 on 9 eligible tickets. These figures have very small denominators, exclude 62 failed tickets, and are not a valid full-set quality claim.
- The validation file itself has three repeated-text urgency conflict groups involving seven tickets, as reported by the evaluation artifact. Interpret urgency metrics with this label-quality issue in view.
- The report's historical baseline describes the original tickets; system FCR and satisfaction are null until real observed assisted-ticket outcomes exist. Citation document-ID match is only a proxy, not human-verified claim support. Hallucination rate and confidence calibration are unavailable.

The project note says a prior Groq one-request JSON-mode smoke check succeeded with the configured Qwen model, but that did not establish sufficient sustained quota for 80 tickets. Retries may reduce transient throttling; they do not guarantee completion. A controlled model and adequate token/request budget are still needed.

## 7. Open items, in recommended order

### P0 — Restore a verified build baseline

1. Run `.venv311\Scripts\python.exe -m pytest tests/ -v` after the current provider placeholder, retry, and progress-logging changes. Record the result in `docs/project_memory.md`.
2. Run `git diff --check` and review the working-tree diff, especially the pending changes listed below.
3. Verify the README setup/test commands and CI path from a clean checkout or fresh environment; document any platform-specific requirements.

### P0 — Complete an unattended validation run

1. Confirm the provider, model, key source, quota, and usable TPM allowance without printing secrets.
2. Run the 80-ticket validation set with a new output basename so failed earlier artifacts are preserved. Current README command uses `validation_2026-11-02-retry`.
3. Run `scripts/verify_evaluation_artifacts.py` against the new JSONL and report. Do not call it complete unless all 80 inputs appear once, in order, and no processor errors remain.
4. Inspect both successes and failures and summarize coverage, technical metrics, business-metric limitations, and governance metrics in the final report. State that the hidden 120-ticket set is permanently unavailable to the project; do not treat its absence as a pending local task.

### P1 — Resolve measurement and model-quality gaps

1. Preserve the supplied intent/urgency labels. Report duplicate-text label conflicts rather than rewriting them.
2. Build a controlled urgency evaluation using a pinned model/version and representative cases; review ambiguity and evidence excerpts, with human review for conflicted or unclear cases.
3. If automatic responses are ever to be enabled, create a separate development calibration split, calibrate intent and urgency separately, validate reliability and per-class precision on held-out data, version the artifact, and then evaluate the configured threshold. Do not tune on final validation/hidden evaluation results.
4. Complete the governance framework's segment fairness analysis: enterprise/business/standard, fluent/non-fluent, and short versus long/complex tickets, with counts, outcome/quality measure, variation, and explanation. Be explicit about small samples and proxy measures.
5. Human-review a response sample for factual grounding, citation support, and safety; current automated document-ID matching cannot establish sentence-level support or hallucination rate.

### P1 — Finish operational governance and submission materials

1. Confirm the intended data-access, reviewer-identity, retention, incident-response, and AI disclosure policy before any real deployment. The current shared token is a local prototype control, not multi-agent identity management.
2. Complete/update the PRD revision log based on discoveries during implementation and ensure requirements map to code/tests.
3. Complete the risk register, fairness audit, final evaluation report, and effort log. Record which figures are historical baselines, validation results, human-reviewed proxies, or unavailable.
4. Prepare the required demonstration video and archive using the exact folder/file rules in [Submission Guide](reference/04_Submission/Submission_Guide.docx). The guide lists a 13 September deadline; it is older than this snapshot, so confirm the active deadline with the course owner.

## 8. How to run locally

Use Python 3.11. From the project root, create/activate an environment and install pinned packages as described in [README](../README.md). Copy `.env.example` to `.env`, set a valid provider API key privately, and keep `.env` untracked. Never paste the key into issue reports or handoff materials.

Run offline tests:

```powershell
.venv311\Scripts\python.exe -m pytest tests/ -v
```

Run the local authenticated review app (the token in `.env` must be a private random value):

```powershell
.venv311\Scripts\python.exe -m uvicorn src.app:app --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/review` or `/dashboard`. The README also documents setup verification, provider smoke check, live sample runs, full evaluation, and artifact verification. Live runs incur provider calls and are subject to current provider quotas.

## 9. Working-tree status

At inspection time, `git status --short` showed modifications to `README.md`, `docs/project_memory.md`, the evaluation/provider scripts, `src/answering.py`, `src/classification.py`, `src/evaluation.py`, `src/model_provider.py`, and related tests. Four 1–2 November validation artifact files are untracked. These changes are existing project work and were left untouched while creating this handoff. `.env` is present locally and ignored; its contents and secrets are intentionally not reproduced here.

The current working-tree change introduces a retry helper shared by classification and drafting, rejects known placeholder credentials, improves provider smoke validation, logs evaluation progress, and updates the recommended retry artifact names. The notes state static diff/AST checks passed, while the complete offline test suite remains pending after these latest edits.

## 10. Reference documents to read first

1. [Project Brief](reference/01_Read_First/01_Project_Brief.docx) — client situation, goals, constraints, and the intended problem framing.
2. [Build Specification](reference/01_Read_First/02_Build_Specification.docx) — binding acceptance criteria and unattended-run gate.
3. [Dataset Guide](reference/05_Datasets/Dataset_Guide.docx) — dataset splits, labels, hidden evaluation set, and allowed evaluation use.
4. [Evaluation Framework](reference/03_Reference/Evaluation_Framework.docx) — business/technical/governance measures and interpretation requirements.
5. [Governance Framework](reference/03_Reference/Governance_Framework.docx) — risk register, decision logging, fairness audit, and incident obligations.
6. [Sprint Plan](reference/02_Stage_Workbooks/Stage_4_Sprint_Plan.docx) and [PRD Revision Log](reference/02_Stage_Workbooks/Stage_5_PRD_Revision_Log.docx) — planned sequencing and required evidence of requirements changes.
7. [Submission Guide](reference/04_Submission/Submission_Guide.docx) — required final artifacts and package structure; verify its dated deadline.
8. [Architecture](architecture.md), [Project Memory](project_memory.md), and [Discovery workbook transcription](discovery_workbook.md) — current implementation detail, development history, and discovery evidence.

The reference pack index is [docs/reference/README.md](reference/README.md). It includes the original Word files, not just the list above.
