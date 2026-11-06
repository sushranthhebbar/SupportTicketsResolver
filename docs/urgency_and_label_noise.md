# Urgency labels, repeated texts, and how the system treats urgency

Development data only (500 tickets); the validation set was not used for any of these findings except where stated.

## What `auto_respond` means
It is a route label meaning "a grounded draft is produced". Nothing is sent to customers. A Tier 1 agent reviews, edits, approves or rejects every draft (PRD FR-04), and the PRD allows automatic sending only after a controlled evaluation and supervised pilot. The Project Brief's decision tree ("Send the answer automatically") describes the course's generic design, not this prototype.

## Repeated texts
- 97 distinct texts are shared by 254 of the 500 development tickets (groups of 2 to 5).
- 67 of those 97 texts carry different urgency labels (186 tickets). Intent labels never conflict; routes rarely do.
- The repeats are **not** customers re-posting: in 95 of 97 groups every ticket has a different `customer_id`; the median gap between repeats is 19.5 days (only 2 of 157 gaps within a day); 55 groups stay on one channel; `repeat_contact` is true for 20.5% of repeated-text tickets vs 22.8% of others. The pattern looks like reused text templates across different customers. Validation has 5 repeated texts (3 conflicting, 7 tickets).
- Decision: do not deduplicate or relabel the datasets (that would drop distinct customers' tickets and change the metrics). Run-time duplicate detection (same `customer_id`, near-identical text, short window; link, never suppress) is a documented recommendation, not implemented.

## Why different urgency for the same text can be legitimate
Urgency plausibly depends on the customer's situation, which is not in the text. The supplied context does not explain it: customer tier differs in 52 of 67 conflicting groups yet does not predict urgency (high share: enterprise 36%, business 22%, standard 31%), language fluency never differs, and channel and region show no pattern. Whether the labels come from customer circumstances, annotators or a generator is unknown. Describe them as "labels that vary for identical text", not simply "noise".

## What 47.5% urgency accuracy means
| | PR-03-v2 (n=341) | Always-medium (n=500) |
|---|---|---|
| Exact accuracy | 47.5% | 45.2% |
| Noise ceiling (best fixed answer per distinct text) | 88.9% | 84.0% |
| Conflict-free tickets | 49.8% (n=251) | 48.1% |
| Conflicting-text tickets | 41.1% (n=90) | - |
| Within one level | 95.6% | 100% |

Random guessing gives about 33%. The model is barely above always-medium, so as a per-ticket label it is close to a coin flip. Repeated-text conflicts cap exact accuracy near 85-89%, so they explain only a small part of the gap; the labels are mostly not recoverable from the text. "Within one level" is uninformative with three levels and must not be quoted alone. Intent, by contrast, is about 85.6% over 22 classes (chance about 5%).

## Decision: urgency is purely advisory (router-v4)
- Urgency is returned as `advisory_urgency` (label, confidence, evidence, validity, ambiguity) for agent prioritisation. It never changes the route: high urgency does not imply complexity, and ambiguous urgency no longer forces review.
- Auto-response is gated only on calibrated **intent** confidence >= 0.80; must-not-auto-respond intents (security, compliance, feature request, unclear) always escalate.
- The review queue is ordered high > medium > low > unknown and shows the suggested urgency, labelled advisory.
- The evaluation report adds `technical.urgency_noise_analysis` (exact, within-one, mean level error, ceiling, conflict-free vs conflicting accuracy). Labels are never rewritten.

## Open risks
- Offline replay (calibration-v2, not active): holdout exact route accuracy 72.8% with 0 must-not auto-answers; fit set 75.8% with 8 must-not tickets auto-answered because their intent was misclassified.
- 82 of 281 auto-routed development tickets were expected to escalate (labels follow `answerable_from_docs` and history); retrieval and guardrails must catch these, and this has not been tested live.
- The calibration artifact stays inactive until those risks are reviewed.
