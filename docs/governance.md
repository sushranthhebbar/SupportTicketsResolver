# Governance and risk (draft for report section 8)

Sources: `docs/governance_coverage_check.md`, `docs/validation_draft_review.md`,
`docs/validation_latency_and_fairness.md`, `evaluation/results/validation_segment_fairness.json`.
Likelihood and impact are my own judgement, not measured. This is a prototype that
never sends to a customer; "owner" names the person accountable for the prototype, and
the production owner is proposed, not agreed.

## 1. Decision logging

Every ticket writes a classification row and a routing row, plus a draft row
(answer_drafting) or an escalation summary, and agent actions write an agent_review row.
All fields of the framework's minimum record exist. On the final validation run the log
reconciles exactly: 80 tickets, 80 classification rows, 80 routing rows, 63 draft rows,
17 escalation rows. A classifier failure now writes an `error` row, so a failed ticket is
still counted. Known weaknesses: `alternatives` is never filled; `input_summary` is
minimal; the draft row stores full ticket text, so access to the database needs a
retention rule. Detail: `docs/governance_coverage_check.md`.

## 2. Risk register

| ID | Risk | Likelihood | Impact | Mitigation in the design | Owner |
|---|---|---|---|---|---|
| R-01 | The system answers confidently and incorrectly | Medium: 4 of 50 drafts I read would mislead a reviewer who skims | High | No send path exists; every draft goes to an agent. Drafts cite sources inline and citations are checked against retrieval. Must-not intents always escalate (64/64 development, 14/14 validation). Not mitigated: the automatic checks missed all 4 misleading drafts. Hallucination rate is unmeasured until two assessors review. | Sushranth Hebbar |
| R-02 | Private data appears in an outbound response | Low in the prototype (nothing is sent); medium if deployed | High | Draft is blocked if it contains key-, token- or password-like strings. The ticket is scanned for the same strings. Not covered: names, emails, addresses, account numbers, another customer's data. The drafter is given the ticket and retrieved articles only, not other customers' records. | Sushranth Hebbar |
| R-03 | A customer's input is treated as an instruction | Medium (untested adversarially) | Medium | The prompt marks ticket text as untrusted. The draft is scanned for instruction-like text and blocked. The ticket text is also scanned and blocked before drafting. Only fixed phrases are matched, so paraphrased injections would pass, and no injection test set was run. | Sushranth Hebbar |
| R-04 | Some customer groups receive worse answers | Medium | Medium | Segment audit on validation (section 3): no gap distinguishable from noise on intent accuracy; groups of 8 to 61 tickets cannot show gaps under about 20 points. Draft quality by group was not assessed. | Sushranth Hebbar |
| R-05 | The documentation the system relies on goes stale | High over time | Medium | Each citation names the article, so an agent can open the source. Two drafts used articles restricted to plans the customer lacks. Plan-scope check is specified (PRD v2.0 FR-02), not built. No freshness check exists. | Technical writer (proposed) |
| R-06 | The model provider becomes unavailable | High on the free tier (HTTP 429 seen on 1 and 2 Nov) | Low in the prototype | Retries honour the provider's reset time; a failed draft becomes a safe `needs_human` result and the ticket goes to review; failed classification is logged and the run can resume. No second provider and no disconnect test (A11). | Sushranth Hebbar |
| R-07 | Latency degrades under load | High | Medium | Measured under free-tier pacing: median 6.3 s, p95 55.8 s, against a 3 s target. No load test and no unpaced run. | Sushranth Hebbar |
| R-08 | Costs rise unexpectedly with volume | Unknown | Medium | A drafted ticket makes two model calls, an escalation one; no cost per ticket was measured or capped, and the NFR-07 target is still TBD. | Support Operations (proposed) |

## 3. Fairness audit (validation, 80 tickets, PR-03-v4, calibration off)

Resolution rate is not available (the prototype resolves nothing and there is no pilot).
Quality score is intent accuracy. Retrieval hit is shown because retrieval is the step the
framework expects to suffer on non-fluent English. Draft-ready is the share of tickets for
which a cited draft was produced. Intervals are Wilson 95% and treat tickets as
independent, so they are narrower than the scenario-cluster intervals in
`validation_accuracy_uncertainty.json`. Variation is in points from the best segment.

| Segment | Tickets | Intent accuracy (95% CI) | Variation | Retrieval hit | Draft-ready |
|---|---|---|---|---|---|
| Enterprise | 8 | 88% (53-98) | -7 | 100% (6/6) | 88% |
| Business | 30 | 90% (74-97) | -5 | 100% (22/22) | 73% |
| Standard | 42 | 93% (81-98) | -2 | 96% (24/25) | 50% |
| Fluent English | 61 | 90% (80-95) | -5 | 98% (43/44) | 62% |
| Non-fluent English | 19 | 95% (75-99) | best | 100% (9/9) | 63% |
| Short (body up to 24 words) | 43 | 93% (81-98) | -2 | 96% (27/28) | 65% |
| Long (body over 24 words) | 37 | 89% (75-96) | -6 | 100% (25/25) | 59% |

What it shows:

- **No intent or retrieval gap is distinguishable from noise.** Every interval overlaps
  the best segment. Non-fluent English did not do worse; it scored best on intent and
  retrieved the expected article in 9 of 9. The framework's expected finding did not
  appear on this set. With 19 tickets I cannot rule out a gap of about 20 points.
- **Draft-ready varies by tier (88% / 73% / 50%) but this is case mix, not worse
  answers.** The standard tier holds 11 of the 14 gold must-not tickets in the set among
  its 42 (business 2 of 30, enterprise 1 of 8), and those always escalate: 13 of
  standard's 42 tickets escalated against 3 of 30 business. Among non-escalated
  tickets, needs-human rates were 8 of 29 standard, 5 of 27 business, 0 of 7 enterprise,
  which is too few to read as a gap.
- Enterprise has only 8 tickets, so its row is inconclusive (below the ~25 rule in the PRD).
- Not assessed: whether drafts differ in correctness or tone by group, and the earlier
  channel and region comparisons are in `docs/validation_latency_and_fairness.md`.

## 4. Guardrails

Summarised from the coverage check: confidence floor met; private data, grounding and
instruction integrity partial (the ticket text and the draft are both scanned for credentials
and injection phrases); tone and scope (no commitments on refunds or timelines)
missing. A fired guardrail blocks the draft and sends the ticket to review, and the block
and its reason are logged. The validation run produced no blocks. Four engineered tickets run live (`scripts/demo_guardrail_ticket.py`) were all blocked by the input check, with no draft and a logged `block` row. Seven earlier tickets built to make the model leak a credential did not block, because the model refused.

## 5. Incident procedure

Written for the prototype or a supervised pilot, where the harm is a wrong or unsafe draft
reaching an agent or, if someone adds a send path, a customer.

| Step | What to do | Who | How long |
|---|---|---|---|
| 1. Detect | Signs: an agent reports a wrong or unsafe draft; the dashboard shows blocked drafts (`guardrail_failures`) or a rise in `needs_human`; a decision-log count that does not match tickets processed. Note the ticket ID. | Any agent reports; the owner checks the dashboard daily during a pilot | Same day |
| 2. Contain | Stop automatic drafting: unset `CALIBRATION_ARTIFACT` if it is set (every ticket then goes to review) and stop the service (the `uvicorn src.app:app` process). Tell agents to work from the knowledge base only. Do not delete any rows. | Owner | Minutes, plus restart |
| 3. Assess | Query `storage/decisions.db` for the ticket_id: read the classification, answer_drafting and routing rows, with `prompt_version`, sources used and guardrail results. Decide: model error, retrieval error, stale article, guardrail gap, or someone changed the instructions. Count other tickets with the same article or intent. | Owner | Within a day |
| 4. Notify | Tell the Head of Support and affected agents; if a customer received an incorrect statement, the agent corrects it through the normal channel. If private data left the system, notify whoever is responsible for data protection (not named; open question). | Owner to Head of Support | Within a day |
| 5. Remediate | Fix the cause (prompt, article, guardrail, or threshold), add a test that reproduces the ticket, run the test suite, then restore. Do not change the frozen validation configuration without recording a new run. | Owner | Days |
| 6. Review | Write what happened and what changed in `docs/project_memory.md`; update the risk register; check whether the PRD needs a revision. | Owner with Head of Support | Within a week |

### The kill switch

| Question | Answer |
|---|---|
| What is the mechanism? | There is no dedicated switch. The system has no code path that sends a message, so nothing is answered automatically. Automatic routing is off while `CALIBRATION_ARTIFACT` is unset, so every ordinary ticket goes to review. Stopping the service stops drafting. |
| Who is authorised to use it? | Whoever can edit the environment file and restart the service: currently the project author. No access control is defined for a pilot. |
| How long until it takes effect? | At the next process start (about a minute), not immediately. It is not read per ticket. |
| What happens to tickets in flight? | A ticket mid-request finishes or fails; a failed one is logged as an error. Drafts already saved stay in the review queue and still need an agent to approve them. |
| How is it tested? | Not as a switch. The final validation run was made with `CALIBRATION_ARTIFACT` unset, which showed 0 auto-responds, but I have not tested restart-to-stop. This is a governance finding: add a runtime flag read on every ticket before any real deployment. |

## 6. Declaration

| Statement | Position |
|---|---|
| This system must never | Send a message to a customer without an agent approving it, or answer a security incident, compliance request, feature request or unclear request without a specialist. |
| The mechanism that enforces that is | The code has no send path; approval is a separate agent action that re-runs the citation and safety checks; the routing rule escalates the four must-not intents whatever the confidence (14 of 14 caught on validation; 64 of 64 on development). |
| The most likely way it could still cause harm is | A fluent, cited draft that gets a claim wrong or applies an article to a plan it does not cover, which a busy agent approves. In my read of 50 drafts, 4 would mislead a reviewer who skims and the automatic checks caught none. |
| We would not deploy this without first | A human review of at least 50 drafts by two assessors with agreement reported, a supervised pilot with real agents, the plan-scope check and commitments check, a runtime kill switch that has been tested, and agreed rules for data access and retention. |
