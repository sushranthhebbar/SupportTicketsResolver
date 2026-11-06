# Accuracy uncertainty and fairness breakdown (development set)

Produced by `scripts/analyze_accuracy_uncertainty.py` from the stored PR-03-v2 development
predictions (341 tickets); no model calls. Output: `evaluation/results/development_accuracy_uncertainty.json`.
Validation tickets were not used.

## Method
- Paraphrases of one scenario are near-duplicates, so tickets are resampled by scenario
  cluster (341 tickets fall in 76 clusters), 2000 resamples, 95% percentile intervals.
  Per-ticket intervals would be too narrow: they would give about +/-3.7 points on intent
  accuracy where the clustered interval is about +/-8.
- Routing metrics replay router-v4 with `calibration-v2` on these predictions. 260 of the
  341 tickets are in that calibration's fit split, so these two rows are optimistic and are
  shown for comparison between groups, not as held-out performance.

## Headline numbers with intervals
| Metric | Value | 95% CI |
|---|---|---|
| Intent accuracy | 85.6% | 77.2 - 92.8 |
| Urgency exact | 47.5% | 40.7 - 54.6 |
| Urgency within one level | 95.6% | 92.8 - 97.9 |
| Must-not tickets predicted as a must-not intent (n=64) | 87.5% | 65.6 - 100 |
| Share auto-routed (in-sample) | 82.4% | 72.6 - 90.7 |
| Auto-routed although the label expects escalation (in-sample) | 24.0% | 18.5 - 30.0 |

Reading: the intent and urgency point estimates are unchanged but their intervals are
roughly twice as wide as a naive calculation suggests. Urgency's interval still sits far
below the label-conflict ceiling (about 85-89%), so the conclusion that urgency is weak
holds. The must-not interval is very wide because only 64 tickets qualify.

## Fairness by customer attribute
Each row compares a group with all other tickets; `*` means the cluster-bootstrap interval
for the difference excludes zero.

- **Language fluency:** no disadvantage. Intent 85% fluent vs 86% non-fluent; urgency 47% vs 49%.
- **Customer tier:** no flagged difference. Enterprise is slightly better on every metric,
  business slightly worse on must-not recall (76%), but intervals include zero.
- **Channel:**
  - chat has lower intent accuracy (78%, -11 points)*.
  - docs_comment has lower urgency accuracy (33%, -17 points)* and a higher share auto-routed
    despite expecting escalation (37%, +15 points)*.
  - email has a lower share of unsafe auto-routing (19%, -9 points)*.
- **Region:** Europe has lower intent accuracy (79%, -10 points)*; other regions are not flagged.

## How much to trust the flags
- About 52 comparisons were made at the 95% level, so two or three flags are expected by
  chance. Five were flagged, which is somewhat more than chance but not strong evidence.
  Treat them as leads, not findings.
- The scenario clusters mix channels (74 of 79), so the channel gaps are not explained by
  different scenario content in different channels; they point at how text is written in
  that channel (chat and docs comments are shorter and less structured). That reading is a
  hypothesis; it has not been tested.
- Groups with few tickets (latin_america 38, forum 39) have wide intervals and cannot be
  said to be fair or unfair.
- Language fluency, the attribute most likely to raise a fairness concern, shows no gap.

## What this does not cover
- Validation and hidden-test fairness: repeat this once on the final frozen run.
- Outcome fairness (resolution, satisfaction by group): needs observed outcomes, not available.
- Whether urgency errors differ by group in direction (over- vs under-estimating).

## Follow-up: the chat and Europe intent gaps
Both gaps trace back to a few scenarios, not to channel or region.

- 49 intent errors fall in only 15 of 76 scenario clusters; the 8 worst clusters hold 37 of them.
  The worst are the "auditor asked for access records" compliance request (7 of 8 wrong,
  predicted `data_export`), two CI-pipeline `integration_help` scenarios (11 of 11 wrong),
  two `api_key_issue` scenarios (9 of 10 wrong) and a connection-pool `database_issue` scenario.
- Five of the seven compliance misclassifications happened to come from Europe, which is
  most of the Europe gap; the same scenario text appears in several channels and regions.
- Removing those 8 scenarios: chat 0.96 vs 0.96 (gap gone) and Europe 0.94 vs 0.97 (-3 points,
  down from -10). Removing the worst 3 leaves chat -7 and Europe -4.
- Not explained by text length (chat median 25 words vs 28 elsewhere), fluency or tier.
- The one residual lead is Europe x chat (64%, n=33) against 91% for neither. With few
  scenarios behind it, this is a lead and not a finding.

Conclusion: no evidence of a channel or regional bias in the classifier. The gaps reflect
how unevenly scenarios are spread across groups. It also means the 85.6% headline depends
heavily on which scenarios happen to be in a sample (effective sample about 76), which is
why the validation figure, drawn from different scenarios, may differ by several points.
The remedy is the weak classes themselves (PR-03-v4 targets them), not a fairness fix.
