# Governance coverage check (11 November 2026)

Compares the code with sections 1 and 4 of the Governance Framework and with
acceptance criteria A7 and A8. It reads the code and the decision log from the
final validation run (`storage/decisions.db`). It changes no code.

## 1. Decision logging

**Fields.** The `decisions` table has every field in the framework's minimum
record (`src/logging_store.py`). Five fields are only partly used:

| Field | Status |
|---|---|
| `alternatives` | Never filled (0 rows). The classifier returns one label, so there are no alternatives to log. |
| `prompt_version` | Filled on every row (0 empty). The routing row carries the classifier's version, because the router has no prompt. |
| `requirement_ids` | Filled, but mixes FR and backlog IDs (for example `B-08`, `B-10`). |
| `input_summary` | Only "Ticket X received on channel". The ticket text is stored in the answer-drafting row instead. |
| `guardrail_results` | Filled on answer-drafting rows only. Classification and routing rows have none. |

**Stages.** The framework lists classification, routing, generation and
validation. The code uses `classification`, `routing`, `answer_drafting`,
`escalation_summary` and `agent_review`. Guardrail results sit inside the
`answer_drafting` row rather than a separate validation row. This is a naming
difference, not a missing decision.

**Coverage check (reconciliation).** On the final validation run:

| Stage | Rows | Distinct tickets |
|---|---|---|
| classification | 80 | 80 |
| routing | 80 | 80 |
| answer_drafting | 63 | 63 |
| escalation_summary | 17 | 17 |

80 tickets were processed (VAL-0001 to VAL-0080) and 80 have a classification
and a routing row. Each ticket has either a draft row (63) or an escalation
summary (17), never both and never neither (63 + 17 = 80). Routing rows: 17
escalate, 63 review. **The log reconciles for this run.**

**Gap.** `process_ticket` writes its rows only after the classifier returns. If
the classifier raises, no decision is recorded. The evaluation harness stores
the error in its own results file, so the run is still countable, but the
decision log would be one short. The final run had 0 errors, so it did not
show here. Fix, if wanted: log a `block` or `error` decision in the exception
path.

**Privacy of the log.** The answer-drafting row stores the full ticket subject
and body and the retrieved passages (so the review page can show them). Anyone
with the database can read customer text. This belongs in the retention answer
(PRD open question 2).

## 2. Guardrails (framework section 4)

| Framework guardrail | In the code | Coverage |
|---|---|---|
| Private data: names, addresses, keys, account numbers | `SECRET_VALUE_PATTERNS` catches key-, bearer-token- and `password=` style strings in the draft. Nothing checks names, addresses, emails or account numbers. | **Partial.** Credentials only. |
| Grounding: every claim traceable to a passage | Evidence-sufficiency flag, at least one inline `[DOC-…]`, and every cited ID must have been retrieved. | **Partial.** Checks the citation, not the claim. The draft review found 4 misleading drafts that passed. |
| Instruction integrity: ticket cannot alter instructions | The prompt tells the model to treat tickets as untrusted (`src/answering.py:94`). `PROMPT_INJECTION_RE` scans the *draft*, not the ticket. | **Partial.** No check on the ticket input, and no record of the input when it fires. |
| Tone and scope: no commitments on refunds or timelines | Nothing. | **Missing.** |
| Confidence floor: a missing score is not a high one | `route_ticket` sends a missing or out-of-range confidence to `review`. Covered by `tests/test_classification_routing.py`. | **Met.** |

When a guardrail fires, the framework says block and escalate. The code blocks
the draft (`action: block`) and routes the ticket to `review`, so a person
reads it; it does not set the route to `escalate`. I count that as meeting the
intent (nothing reaches a customer), but the wording differs.

Guardrails run on every drafted response inside `process_ticket`, not only in
tests, so they meet the "runs on every response" test.

## 3. A7 and A8

- **A7 (a guardrail blocks and logs).** The code path exists and logs
  (`unsafe_content`, `citation_validation`). The validation run produced 0
  blocks, so there is no recorded real example. A demo ticket is still needed
  for the video, and a test that asserts the log row.
- **A8 (decision log reconciles).** Met on the final run, as shown above.

## 4. Kill switch

No dedicated switch exists. What does stop automatic answering today:

- The prototype has no path that sends to a customer, so nothing is answered
  automatically.
- With `CALIBRATION_ARTIFACT` unset, no ordinary ticket reaches `auto_respond`;
  everything goes to review. Unsetting it and restarting the service takes
  effect on the next process start, not instantly, and needs a person with
  access to the environment.

For the declaration I will state this as it is: the switch is a configuration
setting, not an instant control, and a runtime flag read on every ticket would
be the first thing to add before any real deployment.

## 5. What to do

Small code changes, in the order I would take them:

1. Log a decision when the classifier fails (closes the reconciliation gap).
2. Add a tone-and-scope check for commitments (refunds, timelines, credits) to
   `validate_grounded_answer`, with a test.
3. Add a ticket-input injection check that records the input when it fires.
4. Widen the private-data check to emails and account-number patterns.
5. Add a test that a guardrail block writes a log row (A7).

Items 2 to 5 are all small, but each changes behaviour on a frozen validation
set that is already spent, so any rerun would not be a clean comparison. If the
code is left alone, the report should list them as known gaps.
