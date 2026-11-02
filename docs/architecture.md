# Architecture

## Current components

- `src/tickets.py` loads ticket datasets and normalizes email, chat, documentation-comment, and forum records into a shared `NormalizedTicket` representation. Evaluation labels and historical outcomes are kept separately from runtime ticket fields.
- `src/model_provider.py` resolves provider-neutral API key and URL settings, retaining legacy OpenRouter environment variables as fallbacks. `src/classification.py` sends normalized ticket fields to the configured OpenAI-compatible chat-completions endpoint. The model infers and returns intent, urgency, confidence, an urgency evidence excerpt, and its own ambiguity assessment; the input ticket contains no ambiguity flag.
- `src/routing.py` applies the routing rules and confidence threshold. Ambiguous or unsupported urgency evidence always goes to human review. Clear security incidents and high-urgency tickets escalate. Other tickets require calibrated intent and urgency confidence of at least 0.80 to auto-respond; otherwise they go to review.
- `src/escalation.py` prepares an FR-06 summary for agent review, keeping ticket text, supplied conversation history, troubleshooting attempts, retrieved documentation, and system assessments in separate fields. Missing context is called out as unresolved uncertainty rather than invented.
- `src/app.py` exposes the authenticated FR-04 agent review API and serves `static/review.html`. Agents can list/read grounded drafts, edit them, approve them, or reject them. Edits and approvals must pass citation and safety validation again. Approval records the AI disclosure and source IDs; the app does not send customer messages.
- `src/review_store.py` persists review state separately from append-only decisions, exposes per-ticket history, and logs agent edits, approvals, rejections, and escalation decisions for audit. Recording an escalation does not invoke an external handoff.
- `src/outcome_store.py` records observed first-contact resolution, escalation, repeat contact, resolution time, satisfaction, segment fields, and agent feedback for assisted tickets. Its summary reports descriptive metrics by customer tier and language fluency and makes no causal claim.
- `src/answering.py` drafts a reply from retrieved passages through the configured model provider; it never sends replies to customers.
- `src/guardrails.py` rejects malformed responses, insufficient evidence, ungrounded source IDs, credential-like output, and prompt-injection-like drafts.
- `src/pipeline.py` connects classification, routing, retrieval, grounded drafting, escalation summaries, and SQLite decision logging. It writes classification and routing rows, plus an answer-drafting or escalation-summary row when applicable.
- `src/evaluation.py` runs an injected ticket processor over an input dataset, writes per-ticket JSONL results, and produces a metrics JSON report. `scripts/run_evaluation.py` exposes it as a command-line runner.
- `src/retrieve.py` splits documentation articles into passages, builds or loads a persistent Chroma index, and returns source identifiers with retrieved passages.
- `src/logging_store.py` writes auditable decisions to SQLite.
- `src/monitoring.py` exposes Prometheus counters and latency metrics.
- `src/dashboard.py` aggregates persisted ticket decisions and observed outcomes for the authenticated local dashboard served by `src/app.py` at `/dashboard`. It reports outcome coverage, clearly disclaims causal attribution, and identifies latency as unavailable until the pipeline persists it.
- `scripts/verify_setup_steps_4_6.py` verifies those three setup components locally.

### Normalized ticket fields

`NormalizedTicket.to_dict()` returns the same structure for every channel:

```json
{
  "ticket_id": "DEV-0001",
  "channel": "chat",
  "subject": "",
  "body": "Ticket text",
  "received_at": "2026-05-23T22:43:00Z",
  "customer_context": {
    "customer_id": "CUST-1131",
    "customer_name": "Example Customer",
    "customer_tier": "standard",
    "customer_region": "latin_america",
    "language_fluency": "non_fluent"
  }
}
```

Dataset `labels` and `history` are kept separately on `TicketRecord` for offline evaluation; they are not part of the normalized ticket passed to runtime processing.

## Data flow

The retrieval corpus is `data/documentation.json`. The source datasets for development and evaluation live under `evaluation/data/`. Supplied labels are preserved as provided, including any conflicting urgency annotations. Runtime artifacts, including the vector index and SQLite database, are stored under `storage/` and are not committed.

## Classification, urgency, routing, and calibration

The classifier labels use the intent categories present in the supplied development
dataset. Urgency means: **how soon action must happen to prevent material harm or
meet a consequential deadline**. **High** is immediate action to contain active
credential compromise, data loss/corruption, critical production unavailability or
severe customer impact, or an imminent consequential deadline. **Medium** is a real
current problem whose scope is limited, has a workaround, or has no evidence of
immediate/irreversible harm. **Low** means no current material harm and no
consequential near-term deadline, such as routine questions, planned work, feature
requests, and minor issues with a workable path forward. “Urgent” wording alone,
customer tier, intent, route, and historical outcomes do not determine urgency. If
impact or timing is unclear, choose medium with lower confidence and route to review.

An audit of diverse development examples found that exact duplicate subject/body
texts carried conflicting urgency labels in 67 of 97 repeated-text groups. The same
compliance request, for example, was labeled both low and medium. These annotations
remain unchanged: ticket text alone cannot reveal which hidden label is intended.
The classifier must judge urgency from evidence in the ticket; when the evidence is
ambiguous or its quoted support is not present in the ticket, routing sends the case
to human review. Evaluation should preserve and report label conflicts rather than
rewriting them to make model accuracy appear higher.

The model returns raw self-estimated confidence values in [0, 1]. These are logged as
raw estimates and are not interpreted as probabilities. Before confidence can enable
automatic response, calibrate intent and urgency scores separately using a dedicated
calibration split drawn from development data (not the final validation/evaluation
set). Generate predictions for that split, mark each field correct/incorrect against
its label, fit an isotonic regression mapping from raw score to observed correctness,
and check reliability bins, Brier score, and per-class precision on separate held-out
data. Version and retain the calibration artifact with the model and prompt version.
Do not fit or adjust thresholds against the final evaluation set. Until calibrated
scores are explicitly provided, non-urgent, non-security tickets route to human
review. The default auto-response threshold is 0.80 for both calibrated intent and
urgency confidence; review or adjust it only using held-out precision results against
the project target of at least 85% precision per class.

Every ticket produces classification and routing SQLite records. Tickets that do not
escalate also produce an answer-drafting record, including the draft status, sources,
citations, and guardrail results. Thus answer-record count depends on escalation and
draft attempts; distinct logged ticket IDs should reconcile with processed tickets.

The classifier also returns its own urgency ambiguity assessment and an exact
evidence excerpt. The ambiguity value is generated from the ticket text/context; it
is not expected as an input field. If the model reports ambiguity or the excerpt is
not found in the ticket text, routing sends the ticket to human review even when a
calibration score would otherwise clear the threshold. At evaluation time, the harness reports repeated-text urgency-label
conflicts without changing reference labels. A model cannot know which conflicting
hidden label is intended from ticket text alone; the reported metric conflict is a
dataset limitation, not a signal for relabeling predictions.

Reply drafting uses retrieved documentation passages only. Every factual claim must
carry an inline `[DOC-ID]` citation, and structured citation IDs must match passages
retrieved for that ticket. No-hit retrieval, model-declared insufficient evidence,
malformed output, unsupported citations, credential-like content, timeouts, and rate
limits produce a blank draft plus a human next step. A successful draft still needs
agent review and is never sent automatically. Retrieval and provider failures become
per-ticket safe results so evaluation can continue.

Run a 20-ticket live sample with `python .\\scripts\\run_classification_sample.py`.
It uses the first 20 validation tickets for decision inspection, writes
`evaluation/results/classification_sample_20.jsonl`, and records decisions in
`storage/decisions.db`. The validation labels are not passed to the classifier.

## Planned components

The evaluation harness accepts input and output paths rather than hardcoding a dataset filename. The local agent review API is bound to loopback by the documented launch command; access requires the configured bearer token.

### Evaluation processor interface

The runner loads a `NormalizedTicket` and calls a processor function that accepts that object and returns a mapping of predictions and runtime measurements. The processor receives no ground-truth labels or historical outcomes. The harness retains those separately for scoring. It continues after individual processor errors and records them in the results file.

Example command for the pipeline processor:

```powershell
python .\scripts\run_evaluation.py `
  --input evaluation\data\validation_tickets.json `
  --output evaluation\results\validation_run.jsonl `
  --processor src.pipeline:process_ticket `
  --system-version 0.1
```

The runner writes a companion `.report.json` file by default. Historical ticket outcomes are reported as baselines; system first-contact resolution and satisfaction are left unreported until observed outcomes exist. Document-ID matching is reported as a retrieval/citation proxy, not as sentence-level citation accuracy. Hallucination rate requires human review.
