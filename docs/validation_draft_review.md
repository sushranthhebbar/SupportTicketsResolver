# Validation draft review (PR-03-v4 final run)

Reviewer: the coding assistant, reading each draft against the cited documentation text (`data/documentation.json`). This is **not** the human review the project plan requires for a hallucination rate; it is a structured read that finds what automatic checks miss. A person should confirm the flagged items and spot-check the rest.

Scope: the 50 `draft_ready` drafts in `evaluation/results/validation_final_pr03v4.jsonl` (63 tickets routed to review; 13 of those were `needs_human`, 17 escalated with no draft). Ticket labels were used only to describe the tickets, not to judge the drafts.

## Result
| Verdict | Drafts | Tickets |
|---|---|---|
| Sound: every claim traces to the cited text and fits the ticket | 39 | |
| Minor: supported text, but an assumption or small embellishment | 7 | VAL-0019, 0023, 0028, 0033, 0063, 0071, 0075 |
| Needs a person: a customer could be misled or harmed | 4 | VAL-0045, 0049, 0066, 0078 |

Plus two plan-applicability mismatches (VAL-0051, VAL-0076), which overlap the sound/minor groups. No draft invented a document, a number or a procedure that is absent from the cited text. Counts are of drafts, not claims; one claim-level slip is enough to put a draft in the second or third row.

## What went wrong, by pattern
1. **Subject line treated as fact when the body differs** (the largest pattern; 6 drafts). The synthetic tickets often carry a subject that does not match the body.
   - VAL-0078 (subject "Database restore taking hours", body is a connection-pool error): the draft reports a slow restore the customer never mentioned and gives restore-time guidance.
   - VAL-0049 (subject "Need to rotate an exposed key", body is a read-only-scope error): the draft says "revoke the exposed key immediately", before diagnosing scope, with no evidence of exposure. Following step 1 would break a key that still reads fine.
   - VAL-0023 (assumes a migration), VAL-0033 (assumes duplicate deliveries), VAL-0075 (says 401 where the body says "permission error"), VAL-0028 (assumes deployments roll back).
2. **Doc fact applied to a case it does not fit.**
   - VAL-0045: an export "still queued" since the weekend is told it does not need cancelling because large exports "commonly take several minutes". Days is far outside that; an agent needs to check the job.
   - VAL-0066: the customer wants written confirmation of where data is physically stored. The draft says "you can share the following", but it only restates generic policy and names no region. Same failure shape as DEV-0432/0123 in the earlier probe.
3. **Plan applicability ignored.** VAL-0051 (Standard) is told about log forwarding, and VAL-0076 (Standard) about region migration; both docs apply to Business and Enterprise plans. The drafter and the guardrails do not compare a document's `applies_to` with the customer's tier.
4. **Small embellishments** beyond the text: VAL-0019 "or vice versa" (scope), VAL-0063 (muddled project-vs-organisation scope explanation, adds "conflicting"), VAL-0028 "known issue", VAL-0071 assumes a spend cap caused the throttling.

## Guardrail findings
- Citation validation passed on all 50 drafts; none cited a document that was not retrieved. This confirms the earlier probe finding: citations verify retrieval, not whether a claim fits the ticket.
- VAL-0016 uses a combined citation, `[DOC-PERF-001, DOC-PERF-002]`; only PERF-002 is recorded in `citations`. The multi-ID bracket form is not parsed. The claim is supported, but the recorded citation list is incomplete.
- 9 of the 13 `needs_human` outcomes are "must cite at least one source inline" refusals, i.e. the model produced uncited text. That is the safe direction, but 6 were answerable tickets (VAL-0008, 0010, 0012, 0031, 0047, 0062) that a retry might have drafted.

## Implications
- Agent review remains the real safeguard, as in the development probe. The four "needs a person" drafts are exactly the kind a quick read catches.
- Candidate fixes (not applied; each would change the frozen system and needs a new evaluation, so none is made after seeing validation results): tell the drafter to answer from the body and treat a conflicting subject as unconfirmed; add an `applies_to` vs tier check; parse multi-ID citations.
- Do not report a hallucination rate from this read. Report it only after human review of at least this sample.
