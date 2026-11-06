# Development-set error analysis of the PR-03-v2 classifier

Scope: intent, urgency, routing, retrieval/citation and label quality, measured on the **development** data only
(`evaluation/data/development_tickets.json`, `evaluation/calibration/*`, `evaluation/results/development_*`, `urgency_spectrum_development*`,
`urgency_pr03_v3_16*`). Validation tickets and `validation_*` / `classification_sample_20*` results were not opened. No model calls were made.
All numbers below are produced by `scripts/analyze_development_errors.py` (stdlib only; run `.venv/bin/python scripts/analyze_development_errors.py`,
optionally with section names, and `labels --show` to print the 64 sampled errors). Intervals are 95% Wilson; `*` marks any cell with n < 10 (unreliable).

Evidence labels used throughout: **[measured]** = computed directly from the files; **[inferred]** = my reading of the measurements; **[judged]** = single-reader judgment (section 6).

## Summary (most decision-relevant findings)

1. **Earlier headline numbers verify, with caveats.** [measured] Urgency accuracy is 47.5% (162/341; CI 42-53%) and 50.8% (120/236; CI 45-57%) on conflict-free tickets. Intent accuracy is 85.6% (292/341), macro precision/recall 0.837/0.844. No urgency class comes near the project's 85% per-class precision/recall target (macro P/R 0.489/0.456).
2. **The per-intent-majority baseline (58.4%) is an in-sample figure and is optimistic.** [measured] Fitted on the `fit` split and scored on the 90 holdout tickets it gets 52.2% (model 55.6%, paired sign test p = 0.72); leave-one-text-out it gets 49.0% on the same 341 tickets (model 47.5%). Always-"medium" scores 47.8% in-sample, i.e. the model is statistically indistinguishable from the trivial baselines overall. The model's holdout 55.6% is a lucky slice (fit split 44.6%, z = 1.8) and should not be quoted as the expected accuracy.
3. **Where urgency accuracy comes from.** [measured] On security_incident + rollback_request (33 tickets) the model is right 90.9% (the labels there are almost deterministic: 92%/82% high). On the other 308 tickets it is right 42.9%, below always-"medium" (51.9%) and below leave-one-text-out per-intent majority (44.5%). Gold-high recall is 100% (30/30) on those two intents and 16.9% (11/65) everywhere else; so "high is under-called" is true but concentrated, and predicted-high precision is 64%. The biggest single error cell is actually gold-medium predicted low (59), not a high miss.
4. **Urgency labels carry little scenario-level signal, so there is a hard ceiling.** [measured] The 500 dev tickets are ~79 paraphrase scenarios. Two tickets of the same scenario agree on urgency 45.0% of the time versus 35.5% for two random tickets; 69 of 75 multi-ticket scenarios contain more than one urgency label. An oracle that knows the scenario reaches 62.8% in-sample and about 52% leave-one-out; the model is paraphrase-stable (same answer for every variant in 57/69 scenarios) while gold is not. In a stratified sample of 64 urgency errors I judged only ~11% clearly "gold right, model wrong", ~53% rubric-ambiguous, ~36% where the gold label contradicts the rubric [judged]. Prompt work cannot recover the last two groups.
5. **Confidence and ambiguity signals.** [measured] Raw urgency confidence is uninformative (AUROC 0.50; accuracy at 0.85-0.90 is 37-44%, at 0.95 is 65%, at 0.40 is 75%). The ambiguity flag is also uninformative (28 flags, 8.2%; accuracy 53.6% flagged vs 47.0% unflagged; fires on 2.9% of tickets in label-conflict groups vs 10.6% elsewhere). Intent confidence is only mildly informative (AUROC 0.65; 0.98 -> 94.6%, 0.95 -> 84.8%, <0.95 -> 33%, n=12). Calibrated urgency never exceeds 0.656, so auto-respond cannot trigger regardless of prompt wording.
6. **Intent errors are few scenarios, not noise.** [measured] All 49 intent errors fall in 15 of 76 scenarios; 8 scenarios are wrong on every variant. integration_help has 0/13 recall (absorbed by webhook_issue, configuration_help, performance_degradation). The confusions look like taxonomy overlap rather than random mistakes (compliance_request vs data_export, api_key_issue vs authentication_failure / security_incident, database_issue vs performance_degradation) [inferred]. data_export vs data_residency is not a problem here (1 error). The prompt lists intent names with no definitions.
7. **Routing: the harness and the labels, not the classifier, dominate.** [measured] `expected_route` is only `auto_respond|escalate`, so the router's `review` can never match: current policy scores 8.5% exact-match routing (always-auto-respond: 59.2%), with 0 must_not violations and 100% handoff recall. In the labels `expected_route` is almost independent of urgency (escalate: low 32%, medium 35%, high 48%) and is determined by must_not_auto_respond (a function of 4 intents), answerable_from_docs, and, for 15 database/performance tickets, history.escalated; (must_not OR not-answerable) alone gives 95.7% held-out accuracy. A latent policy gap: the router only hard-escalates security_incident, so if raw/calibrated scores ever enabled auto-respond, 30/64 must_not tickets (13/17 compliance_request, 17/17 feature_request) would be auto-responded in simulation.
8. **Probe files are tiny and all-answerable.** [measured] 28 tickets (12 + 16): retrieval hit 28/28, top-1 correct 26/28, citation doc-ID match 15/23 (a proxy). Unanswerable behaviour is untested because no probe ticket has answerable_from_docs=false. The v3 prompt experiment (15 paired tickets) gave 10/15 vs 10/15.
9. **Recommendation (hedged).** The evidence does not support a wholesale rewrite of PR-03 aimed at urgency accuracy: most urgency "errors" are not recoverable from ticket text. It does support (a) a scenario-grouped re-split before any further prompt, few-shot or threshold work (87/90 holdout tickets have a paraphrase sibling in `fit`), (b) a small, zero-shot, testable intent-definition revision, (c) a router rule and an evaluation metric that treat the four must_not intents and `review` explicitly, and (d) a decision by the project owner on what urgency is for, given label noise. See section 7.

## Method notes and limits

- Classified set: 341 tickets (251 `fit`, 90 `holdout` by text hash), 258 distinct texts, 105 in exact-text urgency-conflict groups, 236 conflict-free. Two tickets failed (DEV-0114 HTTP 400, DEV-0487 non-boolean flag) and are excluded; they are 0.6% of attempts. Labels were never altered.
- The model is not fitted on this data, so model accuracy over all 341 is an unbiased estimate; the `fit`/`holdout` split only matters for the baselines and for the calibrators. Baselines are reported in-sample, on the 90-ticket holdout, and leave-one-text-out to make optimism visible.
- Effective sample size is smaller than 341: texts repeat (13 repeated-text groups received non-identical outputs at temperature 0, i.e. provider non-determinism), and paraphrase scenarios cluster (about 76 scenarios). Wilson intervals treat tickets as independent and are therefore too narrow, especially for intent.
- "Scenario clusters" are my construction (content-word Jaccard >= 0.5 within gold intent, union-find). Results are the same at 0.6 and without the intent constraint (79-92 clusters, ceilings 62.8-63.4%).
- The 343 attempted tickets exclude earlier prompt-tuning tickets and tickets sharing their text (per docs); the classified subset has a gold-urgency mix close to all 500 (low 24.3% vs 25.6%, medium 47.8% vs 45.2%, high 27.9% vs 29.2%).

### 0. Data


| quantity | value |
|---|---|
| dev tickets / unique texts | 500 / 343 |
| repeated-text groups / with conflicting urgency | 97 / 67 |
| tickets in conflicting groups (all dev) | 186 |
| repeated-text groups with conflicting expected_route | 30 |
| repeated-text groups with conflicting answerable_from_docs | 36 |
| repeated-text groups with conflicting expected_route that also differ in answerable_from_docs / history.escalated | 28 / 23 |
| repeated-text groups with conflicting intent | 0 |
| prediction rows (attempted / classified / error) | 343 / 341 / 2 |
| classified: fit / holdout | 251 / 90 |
| classified: unique texts | 258 |
| classified in a conflicting-urgency text group | 105 |
| classified conflict-free | 236 |

Repeated texts within the classified set: 59 groups; 13 of them received non-identical outputs for identical text (temperature 0 but provider non-determinism).

| gold urgency | all 500 dev | classified 341 | holdout 90 |
|---|---|---|---|
| low | 25.6% | 24.3% | 25.6% |
| medium | 45.2% | 47.8% | 45.6% |
| high | 29.2% | 27.9% | 28.9% |

Text-only ceiling: a deterministic function of the text can match at most 88.9% (303/341; 85%-92%) of the 341 gold urgency labels (best single label per distinct text; ignores that 13 text groups got inconsistent outputs).

## 1. Intent

- all classified: accuracy 85.6% (292/341; 82%-89%); macro precision 0.837, macro recall 0.844, macro F1 0.819 (n=341)
- fit: accuracy 86.1% (216/251; 81%-90%); macro precision 0.844, macro recall 0.852, macro F1 0.829 (n=251)
- holdout: accuracy 84.4% (76/90; 76%-91%); macro precision 0.774, macro recall 0.820, macro F1 0.775 (n=90)

Per-class (all 341 classified; sorted by F1; holdout column = correct/support on holdout; * = support < 10):

| intent | support | n predicted | precision | recall | F1 | holdout hit | n<10 |
|---|---|---|---|---|---|---|---|
| integration_help | 13 | 0 | 0.00 | 0.00 | 0.00 | 0/3 |  |
| api_key_issue | 13 | 4 | 1.00 | 0.31 | 0.47 | 0/1 |  |
| configuration_help | 8 | 17 | 0.47 | 1.00 | 0.64 | 2/2 | * |
| authentication_failure | 14 | 15 | 0.67 | 0.71 | 0.69 | 2/2 |  |
| compliance_request | 17 | 9 | 1.00 | 0.53 | 0.69 | 3/7 |  |
| account_access | 9 | 11 | 0.64 | 0.78 | 0.70 | 0/0 | * |
| webhook_issue | 18 | 24 | 0.71 | 0.94 | 0.81 | 4/4 |  |
| data_export | 21 | 30 | 0.70 | 1.00 | 0.82 | 3/3 |  |
| performance_degradation | 15 | 21 | 0.71 | 1.00 | 0.83 | 7/7 |  |
| quota_or_overage | 14 | 11 | 1.00 | 0.79 | 0.88 | 5/6 |  |
| security_incident | 16 | 20 | 0.80 | 1.00 | 0.89 | 4/4 |  |
| database_issue | 21 | 17 | 1.00 | 0.81 | 0.89 | 7/10 |  |
| api_usage_question | 15 | 14 | 0.93 | 0.87 | 0.90 | 1/2 |  |
| onboarding | 17 | 14 | 1.00 | 0.82 | 0.90 | 3/4 |  |
| billing_query | 16 | 19 | 0.84 | 1.00 | 0.91 | 3/3 |  |
| data_residency | 22 | 23 | 0.96 | 1.00 | 0.98 | 10/10 |  |
| deployment_failure | 18 | 18 | 1.00 | 1.00 | 1.00 | 4/4 |  |
| feature_request | 17 | 17 | 1.00 | 1.00 | 1.00 | 4/4 |  |
| rate_limit | 8 | 8 | 1.00 | 1.00 | 1.00 | 2/2 | * |
| rollback_request | 17 | 17 | 1.00 | 1.00 | 1.00 | 3/3 |  |
| sso_configuration | 18 | 18 | 1.00 | 1.00 | 1.00 | 4/4 |  |
| unclear_request | 14 | 14 | 1.00 | 1.00 | 1.00 | 5/5 |  |

Top confusion pairs (gold -> predicted), all classified:

| gold | predicted | n |
|---|---|---|
| compliance_request | data_export | 7 |
| integration_help | webhook_issue | 7 |
| api_key_issue | authentication_failure | 5 |
| database_issue | performance_degradation | 4 |
| authentication_failure | account_access | 4 |
| api_key_issue | security_incident | 4 |
| integration_help | configuration_help | 3 |
| onboarding | configuration_help | 3 |
| quota_or_overage | billing_query | 3 |
| account_access | configuration_help | 2 |
| integration_help | performance_degradation | 2 |
| api_usage_question | data_export | 2 |
| compliance_request | data_residency | 1 |
| integration_help | api_usage_question | 1 |
| webhook_issue | configuration_help | 1 |

Errors: 49; top-3 pairs cover 19.

Intent confidence vs accuracy (raw self-reported):

| raw intent_confidence | n | accuracy |
|---|---|---|
| 0.65 | 1 | 0.0% (0/1; 0%-79%) * |
| 0.85 | 8 | 25.0% (2/8; 7%-59%) * |
| 0.92 | 3 | 66.7% (2/3; 21%-94%) * |
| 0.95 | 237 | 84.8% (201/237; 80%-89%) |
| 0.98 | 92 | 94.6% (87/92; 88%-98%) |

AUROC of raw intent confidence for correctness: 0.650 (holdout only: 0.643, n=90).

Confidence < 0.95: 33.3% (4/12; 14%-61%); confidence >= 0.95: 87.5% (288/329; 84%-91%).

Intent errors by weak class (misses of the three lowest-recall gold classes; false positives of the main 'sink' predictions):

- gold integration_help: 13 errors -> {'webhook_issue': 7, 'configuration_help': 3, 'performance_degradation': 2, 'api_usage_question': 1}
- gold api_key_issue: 9 errors -> {'authentication_failure': 5, 'security_incident': 4}
- gold compliance_request: 8 errors -> {'data_export': 7, 'data_residency': 1}
- predicted configuration_help: 9 false positives from {'integration_help': 3, 'account_access': 2, 'onboarding': 3, 'webhook_issue': 1}
- predicted data_export: 9 false positives from {'compliance_request': 7, 'api_usage_question': 2}
- predicted webhook_issue: 7 false positives from {'integration_help': 7}
- predicted performance_degradation: 6 false positives from {'database_issue': 4, 'integration_help': 2}
- predicted security_incident: 4 false positives from {'api_key_issue': 4}

Intent labels never conflict across identical texts in dev (see section 0), so intent is not affected by the duplicate-label problem.

Distinct-text intent accuracy (first copy of each text): 84.5% (218/258; 80%-88%).

**Reading [inferred].**
- Intent is the healthier half of PR-03: 85.6% accuracy, with nine classes at F1 >= 0.9 and perfect scores on deployment_failure, feature_request, rate_limit, rollback_request, sso_configuration, unclear_request. Per-class holdout cells are mostly n < 10 and should not be trusted.
- Weak classes by recall: integration_help (0/13), api_key_issue (4/13), compliance_request (9/17). Weak by precision (sink classes): configuration_help (0.47 precision, 17 predicted for 8 true), data_export (0.70), webhook_issue (0.71), performance_degradation (0.71). Macro precision/recall of 0.84/0.84 is below the 85% target; both precision and recall reach 0.85 for only 8 of 22 classes (api_usage_question, data_residency, deployment_failure, feature_request, rate_limit, rollback_request, sso_configuration, unclear_request) and cannot be established for the n < 10 classes.
- The prompt names the 22 labels but defines none. The error pairs read as definitional overlap: the same "log forwarding stopped" scenario (integration_help) goes to webhook_issue in 7/7 variants; "auditor asked for access records ... can I export these" (compliance_request) goes to data_export 7/8; "pushed a key to a public repo" (api_key_issue) goes to security_incident 4/4 - arguably the model is closer to the urgency rubric's own wording ("credential compromise") than the gold label; "connection pool exhausting" (database_issue) goes to performance_degradation 4/5. These are not random model slips; they are systematic per scenario, which also means the 49 errors are about 15 independent decisions. The suspected data_export vs data_residency overlap is not visible: only 1 compliance_request ticket went to data_residency and no export/residency confusions appear.
- Confidence: raw intent confidence is concentrated on 0.95 (237) and 0.98 (92); AUROC 0.65 so it carries some signal (calibration-v1 collapses it into two values 0.83 / 0.94). Cells below 0.95 have n = 12 and are unreliable.
- Intent labels never conflict between identical texts, so intent is not affected by the duplicate-label problem.

## 2. Urgency

- All classified: 47.5% (162/341; 42%-53%)
- Conflict-free: 50.8% (120/236; 45%-57%)
- Conflicting-text tickets only: 40.0% (42/105; 31%-50%)
- Fit split: 44.6% (112/251; 39%-51%); holdout split: 55.6% (50/90; 45%-65%); holdout conflict-free: 58.7% (37/63; 46%-70%)

Confusion, all classified (rows = gold, columns = predicted; n=341)

| gold \ pred | low | medium | high | total | recall |
|---|---|---|---|---|---|
| low | 33 | 43 | 7 | 83 | 39.8% |
| medium | 59 | 88 | 16 | 163 | 54.0% |
| high | 8 | 46 | 41 | 95 | 43.2% |
| precision | 33.0% | 49.7% | 64.1% | 341 | 47.5% |

Confusion, conflict-free (rows = gold, columns = predicted; n=236)

| gold \ pred | low | medium | high | total | recall |
|---|---|---|---|---|---|
| low | 21 | 32 | 4 | 57 | 36.8% |
| medium | 42 | 66 | 9 | 117 | 56.4% |
| high | 3 | 26 | 33 | 62 | 53.2% |
| precision | 31.8% | 53.2% | 71.7% | 236 | 50.8% |

Confusion, conflicting-text tickets only (rows = gold, columns = predicted; n=105)

| gold \ pred | low | medium | high | total | recall |
|---|---|---|---|---|---|
| low | 12 | 11 | 3 | 26 | 46.2% |
| medium | 17 | 22 | 7 | 46 | 47.8% |
| high | 5 | 20 | 8 | 33 | 24.2% |
| precision | 35.3% | 41.5% | 44.4% | 105 | 40.0% |

- urgency macro precision / recall / F1, all (n=341): 0.489 / 0.456 / 0.465; classes meeting the project 85% per-class precision and recall target: 0/3
- urgency macro precision / recall / F1, conflict-free (n=236): 0.523 / 0.488 / 0.500; classes meeting the project 85% per-class precision and recall target: 0/3
- urgency macro precision / recall / F1, holdout (n=90): 0.594 / 0.511 / 0.521; classes meeting the project 85% per-class precision and recall target: 0/3

Ordinal error (levels off; low=0, medium=1, high=2):

| set | n | exact | off by 1 | off by 2 | direction | mean signed error |
|---|---|---|---|---|---|---|
| all | 341 | 47.5% | 48.1% | 4.4% | under-call 33.1% / over-call 19.4% | -0.14 |
| conflict-free | 236 | 50.8% | 46.2% | 3.0% | under-call 30.1% / over-call 19.1% | -0.11 |

Predicted vs gold distribution (all classified):

| level | gold | predicted |
|---|---|---|
| low | 24.3% | 29.3% |
| medium | 47.8% | 51.9% |
| high | 27.9% | 18.8% |

### Baselines vs model (majority classes broken alphabetically; 'oracle intent' uses the GOLD intent as a feature, which a real system does not have; 'predicted intent' uses PR-03-v2's intent)

| protocol | n scored | PR-03-v2 model | constant majority [label] | per-intent majority (oracle intent) | per-intent majority (predicted intent) |
|---|---|---|---|---|---|
| IN-SAMPLE (fit and score on all 341) | 341 | 47.5% (162/341; 42%-53%) | 47.8% (163/341; 43%-53%) [medium] | 58.4% (199/341; 53%-63%) | 56.6% (193/341; 51%-62%) |
| IN-SAMPLE, conflict-free scored | 236 | 50.8% (120/236; 45%-57%) | 49.6% (117/236; 43%-56%) [medium] | 61.4% (145/236; 55%-67%) | 59.3% (140/236; 53%-65%) |
| HELD-OUT: fit on 251 fit-split preds, score 90 holdout | 90 | 55.6% (50/90; 45%-65%) | 45.6% (41/90; 36%-56%) [medium] | 52.2% (47/90; 42%-62%) | 51.1% (46/90; 41%-61%) |
| HELD-OUT: fit on all 361 dev tickets in fit split, score 90 holdout | 90 | 55.6% (50/90; 45%-65%) | 45.6% (41/90; 36%-56%) [medium] | 52.2% (47/90; 42%-62%) | 51.1% (46/90; 41%-61%) |
| HELD-OUT (fit-500), holdout conflict-free only | 63 | 58.7% (37/63; 46%-70%) | 44.4% (28/63; 33%-57%) [medium] | 58.7% (37/63; 46%-70%) | 57.1% (36/63; 45%-69%) |

Paired on holdout (n=90): model right & per-intent baseline wrong = 17; baseline right & model wrong = 14; exact sign-test p = 0.72.

Leave-one-text-out per-intent majority (oracle intent), n=341: 49.0% (167/341; 44%-54%) -- a less noisy optimism check than the single 90-ticket holdout.

Per-intent majority (oracle intent, fit on fit-500) predicted-level distribution on holdout: {'medium': 52, 'high': 28, 'low': 10}

By gold intent:

| gold intent | n | urgency accuracy | pred high share | gold high share |
|---|---|---|---|---|
| account_access | 9 | 22.2% (2/9; 6%-55%) * | 0.0% | 33.3% |
| api_key_issue | 13 | 38.5% (5/13; 18%-64%) | 69.2% | 23.1% |
| api_usage_question | 15 | 40.0% (6/15; 20%-64%) | 0.0% | 0.0% |
| authentication_failure | 14 | 35.7% (5/14; 16%-61%) | 14.3% | 28.6% |
| billing_query | 16 | 37.5% (6/16; 18%-61%) | 0.0% | 6.2% |
| compliance_request | 17 | 17.6% (3/17; 6%-41%) | 0.0% | 17.6% |
| configuration_help | 8 | 75.0% (6/8; 41%-93%) * | 0.0% | 12.5% |
| data_export | 21 | 33.3% (7/21; 17%-55%) | 0.0% | 19.0% |
| data_residency | 22 | 54.5% (12/22; 35%-73%) | 0.0% | 13.6% |
| database_issue | 21 | 47.6% (10/21; 28%-68%) | 9.5% | 38.1% |
| deployment_failure | 18 | 44.4% (8/18; 25%-66%) | 66.7% | 61.1% |
| feature_request | 17 | 47.1% (8/17; 26%-69%) | 0.0% | 0.0% |
| integration_help | 13 | 30.8% (4/13; 13%-58%) | 0.0% | 0.0% |
| onboarding | 17 | 47.1% (8/17; 26%-69%) | 0.0% | 5.9% |
| performance_degradation | 15 | 40.0% (6/15; 20%-64%) | 0.0% | 40.0% |
| quota_or_overage | 14 | 35.7% (5/14; 16%-61%) | 42.9% | 14.3% |
| rate_limit | 8 | 75.0% (6/8; 41%-93%) * | 0.0% | 0.0% |
| rollback_request | 17 | 88.2% (15/17; 66%-97%) | 100.0% | 88.2% |
| security_incident | 16 | 93.8% (15/16; 72%-99%) | 100.0% | 93.8% |
| sso_configuration | 18 | 44.4% (8/18; 25%-66%) | 0.0% | 33.3% |
| unclear_request | 14 | 71.4% (10/14; 45%-88%) | 0.0% | 14.3% |
| webhook_issue | 18 | 38.9% (7/18; 20%-61%) | 0.0% | 38.9% |

By channel:

| channel | n | urgency accuracy | pred high share | gold high share |
|---|---|---|---|---|
| chat | 114 | 46.5% (53/114; 38%-56%) | 22.8% | 28.9% |
| docs_comment | 54 | 33.3% (18/54; 22%-47%) | 14.8% | 27.8% |
| email | 134 | 51.5% (69/134; 43%-60%) | 14.9% | 26.9% |
| forum | 39 | 56.4% (22/39; 41%-71%) | 25.6% | 28.2% |

By customer_tier:

| customer_tier | n | urgency accuracy | pred high share | gold high share |
|---|---|---|---|---|
| business | 110 | 46.4% (51/110; 37%-56%) | 16.4% | 20.9% |
| enterprise | 57 | 56.1% (32/57; 43%-68%) | 26.3% | 36.8% |
| standard | 174 | 45.4% (79/174; 38%-53%) | 17.8% | 29.3% |

By language_fluency:

| language_fluency | n | urgency accuracy | pred high share | gold high share |
|---|---|---|---|---|
| fluent | 255 | 47.1% (120/255; 41%-53%) | 18.4% | 29.4% |
| non_fluent | 86 | 48.8% (42/86; 39%-59%) | 19.8% | 23.3% |

By text length (words; tertile cuts 25/30):

| text length (words; tertile cuts 25/30) | n | urgency accuracy | pred high share | gold high share |
|---|---|---|---|---|
| long | 108 | 49.1% (53/108; 40%-58%) | 31.5% | 38.9% |
| medium | 108 | 43.5% (47/108; 35%-53%) | 15.7% | 19.4% |
| short | 125 | 49.6% (62/125; 41%-58%) | 10.4% | 25.6% |

Conflict-free repeat of the channel/tier/fluency/length cuts (accuracy only):

- channel: chat 50.0% (42/84; 40%-60%); docs_comment 40.6% (13/32; 26%-58%); email 53.3% (48/90; 43%-63%); forum 56.7% (17/30; 39%-73%)
- tier: business 48.3% (42/87; 38%-59%); enterprise 61.0% (25/41; 46%-74%); standard 49.1% (53/108; 40%-58%)
- fluency: fluent 51.0% (79/155; 43%-59%); non_fluent 50.6% (41/81; 40%-61%)

### Ambiguity flag and evidence validity

| group | n | share | urgency acc (all) | urgency acc (conflict-free) | share in conflict groups |
|---|---|---|---|---|---|
| urgency_ambiguous = true | 28 | 8.2% | 53.6% (15/28; 36%-70%) | 56.0% (14/25; 37%-73%) | 10.7% |
| urgency_ambiguous = false | 313 | 91.8% | 47.0% (147/313; 42%-52%) | 50.2% (106/211; 44%-57%) | 32.6% |
| evidence valid | 335 | 98.2% | 46.9% (157/335; 42%-52%) | 50.0% (115/230; 44%-56%) | 31.3% |
| evidence invalid | 6 | 1.8% | 83.3% (5/6; 44%-97%) * | 83.3% (5/6; 44%-97%) * | 0.0% |

Ambiguity rate on conflicting-label texts 2.9% vs conflict-free 10.6%. AUROC of the ambiguity flag (not-ambiguous) for urgency correctness: 0.490.

| group | n | ambiguous rate |
|---|---|---|
| predicted low | 100 | 0.0% |
| predicted medium | 177 | 15.8% |
| predicted high | 64 | 0.0% |

### Urgency confidence vs accuracy

| raw urgency_confidence | n | accuracy (all) | accuracy (conflict-free) |
|---|---|---|---|
| 0.4 | 12 | 75.0% (9/12; 47%-91%) | 75.0% (9/12; 47%-91%) |
| 0.6 | 70 | 47.1% (33/70; 36%-59%) | 54.8% (23/42; 40%-69%) |
| 0.65 | 16 | 50.0% (8/16; 28%-72%) | 41.7% (5/12; 19%-68%) |
| 0.7 | 5 | 40.0% (2/5; 12%-77%) * | 33.3% (1/3; 6%-79%) * |
| 0.75 | 12 | 58.3% (7/12; 32%-81%) | 66.7% (6/9; 35%-88%) * |
| 0.8 | 30 | 36.7% (11/30; 22%-54%) | 35.0% (7/20; 18%-57%) |
| 0.85 | 99 | 44.4% (44/99; 35%-54%) | 46.7% (28/60; 35%-59%) |
| 0.9 | 56 | 37.5% (21/56; 26%-51%) | 36.6% (15/41; 24%-52%) |
| 0.95 | 40 | 65.0% (26/40; 50%-78%) | 69.4% (25/36; 53%-82%) |
| 0.98 | 1 | 100.0% (1/1; 21%-100%) * | 100.0% (1/1; 21%-100%) * |

- AUROC raw urgency confidence -> correct, all (n=341): 0.501
- AUROC raw urgency confidence -> correct, conflict-free (n=236): 0.500
- AUROC raw urgency confidence -> correct, holdout (n=90): 0.511

| band | n | accuracy |
|---|---|---|
| <0.70 | 98 | 51.0% (50/98; 41%-61%) |
| 0.70-0.85 | 47 | 42.6% (20/47; 30%-57%) |
| >=0.90 | 97 | 49.5% (48/97; 40%-59%) |

Calibrated urgency scores take values [0.416, 0.656]; max 0.656 (< 0.80 so urgency can never clear the auto-respond bar).

### High urgency

Gold high n=95: predicted high 43.2% (41/95; 34%-53%), medium 46, low 8. Predicted high n=64, precision 64.1% (41/64; 52%-75%).

Conflict-free gold high n=62: recall 53.2% (33/62; 41%-65%).

| gold intent (gold-high tickets) | n | predicted-high recall |
|---|---|---|
| account_access | 3 | 0.0% (0/3; 0%-56%) * |
| api_key_issue | 3 | 66.7% (2/3; 21%-94%) * |
| authentication_failure | 4 | 0.0% (0/4; 0%-49%) * |
| billing_query | 1 | 0.0% (0/1; 0%-79%) * |
| compliance_request | 3 | 0.0% (0/3; 0%-56%) * |
| configuration_help | 1 | 0.0% (0/1; 0%-79%) * |
| data_export | 4 | 0.0% (0/4; 0%-49%) * |
| data_residency | 3 | 0.0% (0/3; 0%-56%) * |
| database_issue | 8 | 12.5% (1/8; 2%-47%) * |
| deployment_failure | 11 | 63.6% (7/11; 35%-85%) |
| onboarding | 1 | 0.0% (0/1; 0%-79%) * |
| performance_degradation | 6 | 0.0% (0/6; 0%-39%) * |
| quota_or_overage | 2 | 50.0% (1/2; 9%-91%) * |
| rollback_request | 15 | 100.0% (15/15; 80%-100%) |
| security_incident | 15 | 100.0% (15/15; 80%-100%) |
| sso_configuration | 6 | 0.0% (0/6; 0%-39%) * |
| unclear_request | 2 | 0.0% (0/2; 0%-66%) * |
| webhook_issue | 7 | 0.0% (0/7; 0%-35%) * |

Where the model says high but gold is not high (false highs), by gold intent:

| gold intent | n |
|---|---|
| api_key_issue | 7 |
| quota_or_overage | 5 |
| deployment_failure | 5 |
| authentication_failure | 2 |
| rollback_request | 2 |
| security_incident | 1 |
| database_issue | 1 |

### Where the accuracy comes from

| subset | n | PR-03-v2 | always medium | leave-one-text-out per-intent majority (oracle intent) |
|---|---|---|---|---|
| security_incident + rollback_request | 33 | 90.9% (30/33; 76%-97%) | 9.1% (3/33; 3%-24%) | 90.9% (30/33; 76%-97%) |
| all other 20 intents | 308 | 42.9% (132/308; 37%-48%) | 51.9% (160/308; 46%-57%) | 44.5% (137/308; 39%-50%) |

Gold-high recall within security_incident/rollback_request: 100.0% (30/30; 89%-100%); within all other intents: 16.9% (11/65; 10%-28%).

**Reading.**
- [measured] The prediction mix is shifted down: low 29% (gold 24%), high 19% (gold 28%). Off-by-one errors are 48.1%, off-by-two only 4.4%, so errors are mostly adjacent-level; net signed error is -0.14 levels.
- [measured] The three confusion cells that matter: medium->low 59, high->medium 46, low->medium 43. High is predicted precisely (64% precision, 72% conflict-free) but with 43% recall.
- [measured] Segments: gold intent drives accuracy (security_incident 94%, rollback_request 88%, compliance_request 18%); channel, tier, fluency and length differences are mostly within noise. docs_comment looks weak (33%, n = 54, CI 22-47%; 41% conflict-free, n = 32) and enterprise strong (56%/61%); neither survives a multiple-comparison sniff test and both remain hypotheses.
- [measured] Evidence validity: 6 of 341 (1.8%) are invalid, 5 of them correct, so the "unsupported evidence -> review" rule fires on mostly correct predictions (tiny n). Ambiguity: all 28 flagged predictions are `medium`; the flag adds no accuracy information (AUROC 0.49).
- [measured] Confidence is non-monotonic: n = 12 at 0.40 are 75% right, the largest bucket (0.85, n = 99) is 44% right.
- The baselines section is the key one: model 47.5% vs always-medium 47.8% vs leave-one-text-out per-intent 49.0% (all 341). Holdout figures use n = 90 (CI +/-10 points) and a paraphrase-leaky split, so they cannot rank the model against the baselines.

## 2b. Near-duplicate scenarios (paraphrase clusters) and the label ceiling

| quantity | value |
|---|---|
| scenario clusters among 500 dev tickets (Jaccard >= 0.5 on content words, same intent) | 79 |
| cluster size min / median / max | 1 / 6 / 16 |
| clusters of size >1 containing more than one urgency label | 69/75 |
| pairwise urgency agreement of tickets in the same cluster | 45.0% (798/1775 pairs) |
| agreement expected for two random tickets (sum p_i^2) | 35.5% |
| in-sample ceiling: predict each cluster's majority urgency (500 tickets) | 62.8% (314/500; 58%-67%) |
| leave-one-out cluster-majority urgency, all 500 labels | 51.8% (259/500; 47%-56%) |
| leave-one-out cluster-majority, the 341 classified tickets | 53.4% (182/341; 48%-59%) |
| leave-one-out cluster-majority, the 236 conflict-free classified tickets | 59.3% (140/236; 53%-65%) |
| PR-03-v2 on the same 341 / 236 | 47.5% (162/341; 42%-53%) / 50.8% (120/236; 45%-57%) |

Reading: clusters are paraphrase/noise variants of one scenario (typos, 'sorry for my english', changed durations). Two tickets in the same cluster agree on urgency barely more often than two random tickets, so the supplied urgency labels carry little scenario-level signal. A classifier that treats paraphrases alike cannot exceed roughly the in-sample ceiling and realistically sits near the leave-one-out figure.

Twelve largest scenarios (labels shown as low/medium/high counts):

| size | intent | low/med/high | text start |
|---|---|---|---|
| 16 | rollback_request | 0/4/12 | how do I revert to earlier revision? release we put out this morning i |
| 14 | performance_degradation | 4/4/6 | Latency has been climbing gradually over the past two hours. Nothing i |
| 14 | data_residency | 6/6/2 | Question about backup regions One of our customers has asked for writt |
| 12 | compliance_request | 3/7/2 | Evidence for a compliance review Our auditor has asked for access reco |
| 12 | data_export | 2/8/2 | Export missing recent records The download link from our export has ex |
| 12 | rollback_request | 0/1/11 | Bad release in production We shipped a release yesterday morning that  |
| 11 | deployment_failure | 2/3/6 | Health check keeps timing out Every deployment fails at the health che |
| 11 | quota_or_overage | 4/4/3 | Usage allowance already consumed our spend cap stop production workloa |
| 11 | sso_configuration | 2/6/3 | SAML login returns an error page Single sign-on works for our engineer |
| 11 | api_usage_question | 6/5/0 | Pagination returns duplicates Our cursor seems to stop working partway |
| 10 | database_issue | 1/3/6 | Connection pool exhausted We are getting errors saying no connection i |
| 10 | security_incident | 0/0/10 | One of our engineers believes their credentials may have been exposed  |

Model consistency across paraphrases: in 57/69 multi-ticket scenarios (among classified tickets) the model gives the same urgency to every variant.

Intent errors are scenario-level: the 341 classified tickets span 76 scenarios; all 49 intent errors fall in 15 of them, and 8 scenarios (25 tickets) are wrong on every variant. Effective sample size for intent is therefore nearer 76 than 341.

| tickets | intent errors | gold intent | predicted (counts) | text start |
|---|---|---|---|---|
| 8 | 7 | compliance_request | {'data_export': 7, 'compliance_request': 1} | Retention period question Our auditor has asked for access records cov |
| 7 | 7 | integration_help | {'webhook_issue': 7} | Connecting our CI pipeline log forwarding to our external system stop  |
| 6 | 5 | api_key_issue | {'authentication_failure': 5, 'api_key_issue': 1} | one of our production keys start returning 401 at around two days ago  |
| 5 | 4 | database_issue | {'performance_degradation': 4, 'database_issue': 1} | No connections available error Our connection pool appears to be exhau |
| 4 | 4 | integration_help | {'configuration_help': 3, 'api_usage_question': 1} | Monitoring integration setup We are connecting our CI pipeline and are |
| 4 | 4 | api_key_issue | {'security_incident': 4} | Key stopped working overnight One of our engineers pushed a key to a p |
| 4 | 3 | onboarding | {'configuration_help': 3, 'onboarding': 1} | we planning to migrate existing application across. It currently write |
| 4 | 3 | authentication_failure | {'authentication_failure': 1, 'account_access': 3} | Invalid credentials error Since yesterday morning I cannot get into th |
| 3 | 3 | quota_or_overage | {'billing_query': 3} | Unexpected overage charges Overage charges appeared on our invoice tha |
| 2 | 2 | account_access | {'configuration_help': 2} | We are tightening permissions after a review and I want to understand  |

Split leakage: 87/90 holdout tickets belong to a scenario cluster that also has classified tickets in the fit split (45 of 47 holdout scenarios). The hash split separates identical texts only, not paraphrases, so anything fitted on `fit` (few-shot examples, per-intent/per-scenario priors, thresholds) is evaluated on paraphrases of its own training material.

The model itself is never fitted, yet its urgency accuracy is 44.6% on the fit split and 55.6% on the holdout (z = 1.78): the 90-ticket holdout is a noisy, somewhat easier slice, so 55.6% should not be read as the expected accuracy.

Does any other field explain urgency *within* a scenario? Leave-one-out majority using same-cluster tickets that also share the field value (fallback: whole cluster):

| conditioning | LOO accuracy (500) |
|---|---|
| cluster only | 51.8% (259/500; 47%-56%) |
| + history.escalated | 49.0% (245/500; 45%-53%) |
| + customer_tier | 44.6% (223/500; 40%-49%) |
| + channel | 44.2% (221/500; 40%-49%) |
| + language_fluency | 48.0% (240/500; 44%-52%) |
| + subject line | 46.2% (231/500; 42%-51%) |
| + csat_rating | 43.6% (218/500; 39%-48%) |
| + repeat_contact | 51.6% (258/500; 47%-56%) |

No field improves on the cluster alone (splitting small pools mostly adds noise), so within-scenario label variation is not explained by anything observed here. This is observation only, not proof the labels are random.

**Reading [inferred].** The supplied urgency labels are only weakly a function of ticket text, even after grouping paraphrases; none of the other fields (history, tier, channel, subject) explains the variation within a scenario. Combined with the 67/97 exact-duplicate conflicts, a realistic text-only ceiling for dev urgency is roughly 52-63%, and the model sits at 47.5-53% depending on subset. This is a statement about these labels, not about the (unseen) validation labels.

## 3. Joint intent / urgency view

all classified (n=341)

|  | urgency right | urgency wrong | total |
|---|---|---|---|
| intent right | 149 | 143 | 292 |
| intent wrong | 13 | 36 | 49 |
| total | 162 | 179 | 341 |

Both right 43.7% (149/341; 39%-49%); urgency acc given intent right 51.0% (149/292; 45%-57%), given intent wrong 26.5% (13/49; 16%-40%). Odds ratio (intent right x urgency right) = 2.89.

conflict-free (n=236)

|  | urgency right | urgency wrong | total |
|---|---|---|---|
| intent right | 110 | 89 | 199 |
| intent wrong | 10 | 27 | 37 |
| total | 120 | 116 | 236 |

Both right 46.6% (110/236; 40%-53%); urgency acc given intent right 55.3% (110/199; 48%-62%), given intent wrong 27.0% (10/37; 15%-43%). Odds ratio (intent right x urgency right) = 3.34.

Of 49 intent errors, 13 still have correct urgency. Urgency errors per intent-correct ticket: 143/292.

Mean signed urgency error by whether intent was right: right -0.12, wrong -0.24.

**Reading.** Intent and urgency errors co-occur more than chance (odds ratio 2.9; urgency right 51% when intent right vs 27% when intent wrong), but only 49 tickets have a wrong intent, so this explains little: 143 of the 179 urgency errors have a correct intent. Both right: 43.7% (46.6% conflict-free). The association is plausibly shared difficulty (ambiguous tickets), not a causal coupling; it does not by itself motivate splitting the calls.

## 4. Routing

expected_route values present in dev labels: ['auto_respond', 'escalate']. `src/evaluation.py` scores routing as exact string equality of the route/action with expected_route, so the router's `review` outcome can never match a label: every review-routed ticket counts as a routing miss, whatever its true merit.

All 341 classified (calibration was fitted on 251 of these; B/E are in-sample for the fit part)

| policy simulated | n | auto/review/escalate | routing acc (exact match) | must_not violations (auto on must_not / n must_not) | expected-escalate not auto-responded (handoff recall) | expected-escalate routed 'escalate' (exact) | precision of auto_respond |
|---|---|---|---|---|---|---|---|
| A. current deployment: no calibration artifact | 341 | 0/282/59 | 8.5% (29/341; 6%-12%) | 0/64 | 100.0% (139/139; 97%-100%) | 20.9% (29/139; 15%-28%) | n/a |
| B. calibration-v1 scores (urgency max 0.66) | 341 | 0/282/59 | 8.5% (29/341; 6%-12%) | 0/64 | 100.0% (139/139; 97%-100%) | 20.9% (29/139; 15%-28%) | n/a |
| C. what-if: RAW confidences treated as calibrated @0.80 | 341 | 160/122/59 | 36.4% (124/341; 31%-42%) | 30/64 | 53.2% (74/139; 45%-61%) | 20.9% (29/139; 15%-28%) | 59.4% (95/160; 52%-67%) |
| D. what-if C with ambiguity/evidence gate disabled | 341 | 161/116/64 | 37.8% (129/341; 33%-43%) | 30/64 | 52.5% (73/139; 44%-61%) | 24.5% (34/139; 18%-32%) | 59.0% (95/161; 51%-66%) |
| E. what-if B with ambiguity/evidence gate disabled | 341 | 0/277/64 | 10.0% (34/341; 7%-14%) | 0/64 | 100.0% (139/139; 97%-100%) | 24.5% (34/139; 18%-32%) | n/a |
| reference: always auto_respond | 341 | 341/0/0 | 59.2% (202/341; 54%-64%) | 64/64 | 0.0% (0/139; -0%-3%) | 0.0% (0/139; -0%-3%) | 59.2% (202/341; 54%-64%) |
| reference: always escalate | 341 | 0/0/341 | 40.8% (139/341; 36%-46%) | 0/64 | 100.0% (139/139; 97%-100%) | 100.0% (139/139; 97%-100%) | n/a |

Expected-route mix here: {'auto_respond': 202, 'escalate': 139}; must_not_auto_respond true: 64.

Holdout 90 only (clean for B/E)

| policy simulated | n | auto/review/escalate | routing acc (exact match) | must_not violations (auto on must_not / n must_not) | expected-escalate not auto-responded (handoff recall) | expected-escalate routed 'escalate' (exact) | precision of auto_respond |
|---|---|---|---|---|---|---|---|
| A. current deployment: no calibration artifact | 90 | 0/78/12 | 7.8% (7/90; 4%-15%) | 0/20 | 100.0% (38/38; 91%-100%) | 18.4% (7/38; 9%-33%) | n/a |
| B. calibration-v1 scores (urgency max 0.66) | 90 | 0/78/12 | 7.8% (7/90; 4%-15%) | 0/20 | 100.0% (38/38; 91%-100%) | 18.4% (7/38; 9%-33%) | n/a |
| C. what-if: RAW confidences treated as calibrated @0.80 | 90 | 49/29/12 | 41.1% (37/90; 32%-51%) | 9/20 | 50.0% (19/38; 35%-65%) | 18.4% (7/38; 9%-33%) | 61.2% (30/49; 47%-74%) |
| D. what-if C with ambiguity/evidence gate disabled | 90 | 49/29/12 | 41.1% (37/90; 32%-51%) | 9/20 | 50.0% (19/38; 35%-65%) | 18.4% (7/38; 9%-33%) | 61.2% (30/49; 47%-74%) |
| E. what-if B with ambiguity/evidence gate disabled | 90 | 0/78/12 | 7.8% (7/90; 4%-15%) | 0/20 | 100.0% (38/38; 91%-100%) | 18.4% (7/38; 9%-33%) | n/a |
| reference: always auto_respond | 90 | 90/0/0 | 57.8% (52/90; 47%-67%) | 20/20 | 0.0% (0/38; 0%-9%) | 0.0% (0/38; 0%-9%) | 57.8% (52/90; 47%-67%) |
| reference: always escalate | 90 | 0/0/90 | 42.2% (38/90; 33%-53%) | 0/20 | 100.0% (38/38; 91%-100%) | 100.0% (38/38; 91%-100%) | n/a |

Expected-route mix here: {'auto_respond': 52, 'escalate': 38}; must_not_auto_respond true: 20.

Policy A route reasons (n=341): {'no calibration': 248, 'high urgency': 44, 'security_incident': 15, 'ambiguous/evidence': 34}

Policy A: 59 escalations; expected_route=escalate for 49.2% (29/59; 37%-62%); of the 139 expected-escalate tickets, 29 are escalated, 110 go to review.

must_not_auto_respond tickets (gold) by *predicted* intent and the rule that would catch them:

| gold intent | n | pred intent=security_incident | pred urgency=high | ambiguous/evidence-invalid | caught by A (not auto and not needing calibration) |
|---|---|---|---|---|---|
| compliance_request | 17 | 0 | 0 | 2 | 17 |
| feature_request | 17 | 0 | 0 | 0 | 17 |
| security_incident | 16 | 16 | 16 | 5 | 16 |
| unclear_request | 14 | 0 | 0 | 14 | 14 |

If a calibrated policy ever did auto-respond (mode C), these must_not tickets would be auto-responded, by gold intent:

| gold intent | n must_not | auto-responded under C |
|---|---|---|
| compliance_request | 17 | 13 |
| feature_request | 17 | 17 |
| security_incident | 16 | 0 |
| unclear_request | 14 | 0 |

### What determines expected_route in the dev labels (all 500 tickets; hash split fit/holdout by text)

must_not_auto_respond == (gold intent in security_incident/compliance_request/feature_request/unclear_request): True; every must_not ticket has expected_route=escalate: True.

- urgency (gold): high: 70/146 escalate; low: 41/128 escalate; medium: 78/226 escalate
- answerable_from_docs: False: 143/143 escalate; True: 46/357 escalate
- must_not_auto_respond: False: 102/413 escalate; True: 87/87 escalate
- history.escalated: False: 0/219 escalate; True: 189/281 escalate
- history.first_contact_resolution: False: 189/281 escalate; True: 0/219 escalate
- history.repeat_contact: False: 119/392 escalate; True: 70/108 escalate
- history.csat_rating: 1: 43/89 escalate; 2: 46/107 escalate; 3: 49/114 escalate; 4: 39/109 escalate; 5: 12/81 escalate
- customer_tier: business: 58/164 escalate; enterprise: 32/83 escalate; standard: 99/253 escalate
- channel: chat: 50/155 escalate; docs_comment: 37/78 escalate; email: 79/212 escalate; forum: 23/55 escalate

Single-lookup predictors of expected_route: majority class per feature value fitted on 361 fit-split tickets, scored on 139 holdout tickets (holdout escalate share 37.4%). Features marked (gold) or label fields are NOT available to the classifier at run time.

| feature(s) | holdout accuracy | escalate precision | escalate recall |
|---|---|---|---|
| constant (always auto_respond) | 62.6% (87/139; 54%-70%) | n/a (never predicts escalate) | 0.0% (0/52; 0%-7%) |
| urgency (gold) | 62.6% (87/139; 54%-70%) | n/a (never predicts escalate) | 0.0% (0/52; 0%-7%) |
| intent (gold) | 82.7% (115/139; 76%-88%) | 80.4% (37/46; 67%-89%) | 71.2% (37/52; 58%-82%) |
| intent x urgency (gold) | 86.3% (120/139; 80%-91%) | 88.4% (38/43; 76%-95%) | 73.1% (38/52; 60%-83%) |
| customer_tier + channel | 64.7% (90/139; 57%-72%) | 63.6% (7/11; 35%-85%) | 13.5% (7/52; 7%-25%) |
| history.csat_rating | 59.0% (82/139; 51%-67%) | 40.0% (10/25; 23%-59%) | 19.2% (10/52; 11%-32%) |
| history.repeat_contact | 68.3% (95/139; 60%-75%) | 63.3% (19/30; 46%-78%) | 36.5% (19/52; 25%-50%) |
| answerable_from_docs | 89.9% (125/139; 84%-94%) | 100.0% (38/38; 91%-100%) | 73.1% (38/52; 60%-83%) |
| must_not_auto_respond | 82.7% (115/139; 76%-88%) | 100.0% (28/28; 88%-100%) | 53.8% (28/52; 41%-67%) |
| must_not OR not answerable | 95.7% (133/139; 91%-98%) | 100.0% (46/46; 92%-100%) | 88.5% (46/52; 77%-95%) |
| history.escalated | 79.1% (110/139; 72%-85%) | 64.2% (52/81; 53%-74%) | 100.0% (52/52; 93%-100%) |
| must_not x answerable x history.escalated | 95.7% (133/139; 91%-98%) | 100.0% (46/46; 92%-100%) | 88.5% (46/52; 77%-95%) |
| (must_not OR not answerable) x history.escalated | 95.7% (133/139; 91%-98%) | 100.0% (46/46; 92%-100%) | 88.5% (46/52; 77%-95%) |
| (must_not OR not answerable) x intent | 95.7% (133/139; 91%-98%) | 100.0% (46/46; 92%-100%) | 88.5% (46/52; 77%-95%) |

Escalations not explained by must_not or not-answerable: 15 (intents {'performance_degradation': 7, 'database_issue': 8}; all history.escalated=True: True). Among answerable, non-must_not database_issue/performance_degradation tickets with history.escalated=True: 15/21 escalate.

history.escalated=False => expected_route=auto_respond in 219/219 tickets. Conflicting expected_route across identical texts: 30 of 97 repeated groups.

Runtime-available predictors only (fit on the 251 classified fit tickets, score the 90 classified holdout; same data the classifier produced):

| predictor | holdout accuracy | escalate precision | escalate recall |
|---|---|---|---|
| constant (always auto_respond) | 57.8% (52/90; 47%-67%) | n/a | 0.0% (0/38; 0%-9%) |
| predicted urgency | 60.0% (54/90; 50%-70%) | 58.3% (7/12; 32%-81%) | 18.4% (7/38; 9%-33%) |
| predicted intent | 74.4% (67/90; 65%-82%) | 82.6% (19/23; 63%-93%) | 50.0% (19/38; 35%-65%) |
| predicted intent in {security, compliance, feature_request, unclear} (fixed rule, no fitting) | 75.6% (68/90; 66%-83%) | 100.0% (16/16; 81%-100%) | 42.1% (16/38; 28%-58%) |
| predicted intent x predicted urgency | 73.3% (66/90; 63%-81%) | 79.2% (19/24; 60%-91%) | 50.0% (19/38; 35%-65%) |
| gold intent (not runtime; ceiling of intent info) | 80.0% (72/90; 71%-87%) | 81.2% (26/32; 65%-91%) | 68.4% (26/38; 53%-81%) |

The fixed 'predicted intent in the four must_not intents -> escalate' rule on all 341: accuracy 75.1% (256/341; 70%-79%).

- gold urgency=low: expected escalate 32.0% (41/128; 25%-41%)
- gold urgency=medium: expected escalate 34.5% (78/226; 29%-41%)
- gold urgency=high: expected escalate 47.9% (70/146; 40%-56%)

Within the 326 answerable, non-must_not tickets (where routing is not forced by must_not/answerability), expected escalate share by gold urgency: low 0.0% (0/87; 0%-4%); medium 0.0% (0/148; 0%-3%); high 16.5% (15/91; 10%-25%)

**Reading.**
- [measured] `review` is not a valid label value, so under the evaluation harness every review is a miss. The 8.5% routing accuracy of policy A is a harness artifact as much as a classifier result; by design its true safety behaviour (0 must_not violations, 100% of expected escalations kept away from auto-respond) is invisible in the exact-match metric.
- [measured] Rows C-E are what-ifs, not deployed behaviour: they show that if raw self-confidence were trusted at 0.80, auto-respond precision would be 59.4% (95/160) - the same as the always-auto-respond base rate (59.2%) - and 30 of 64 must_not tickets would be auto-answered. The calibrated rows B/E prove the point of calibration-v1: calibrated urgency tops out at 0.656.
- [measured] The router only hard-escalates `security_incident` (and high urgency). The other three must_not intents (compliance_request, feature_request, unclear_request) are protected today only by the review default and, for unclear_request, by the ambiguity gate (14/14 flagged). This is a policy gap that becomes live the moment calibration is activated.
- [measured] High urgency is a poor escalation criterion against these labels: policy A escalates 59 tickets and 49.2% (29/59) are expected-escalate (base rate 40.8%).
- [measured] What actually predicts `expected_route`: must_not (determined by intent) and answerable_from_docs (a retrieval/knowledge-base property, 143/143 unanswerable are escalate); history.escalated=False implies auto_respond in 219/219 and the 15 remaining escalations are database_issue/performance_degradation tickets with history.escalated=True. The rule (must_not OR not answerable) gets 95.7% on holdout (precision 100%, recall 88.5%). Runtime-feasible information is weaker: predicted intent alone gets 74.4% and the fixed four-intent rule 75.6% (precision 100% on 16 predicted, recall 42%) vs 57.8% base rate. Urgency adds nothing (predicted urgency 60.0%; gold urgency = base rate). history.* fields are not available at run time and would be leakage if used.
- [inferred] The route labels look like they were derived from (intent-based must_not, KB coverage, historical escalation), not from urgency. 30 of 97 repeated-text groups also carry conflicting expected_route; 28 of those also differ in answerable_from_docs and 23 in history.escalated, and answerable_from_docs conflicts across identical texts in 36 of 97 groups, so even this 'KB coverage' flag is not a function of the text.

## 5. Retrieval, citations and answerability (small probe files only)

| file | tickets | retrieval hit (answerable) | citation doc-ID matches / cited | answer_status | route |
|---|---|---|---|---|---|
| development_citation_probe | 12 | 12/12 | 6/8 | {'needs_human': 2, 'not_generated': 4, 'draft_ready': 6} | {'review': 8, 'escalate': 4} |
| development_citation_probe_v2 | 12 | 12/12 | 5/7 | {'draft_ready': 6, 'needs_human': 2, 'not_generated': 4} | {'review': 8, 'escalate': 4} |
| development_citation_probe_v2_16 | 16 | 16/16 | 10/16 | {'not_generated': 5, 'draft_ready': 9, 'needs_human': 2} | {'escalate': 5, 'review': 11} |

Overlap of probe tickets with the 341-ticket calibration prediction set: development_citation_probe: 0/12, development_citation_probe_v2: 0/12, development_citation_probe_v2_16: 0/16.

Pooled latest-version probes (12 + 16 = 28 distinct tickets, all PR-03-v2 / qwen3.8-27b):

| ticket | answerable | expected docs | retrieval hit | top-1 doc | cited | answer_status | route | expected_route | next_step |
|---|---|---|---|---|---|---|---|---|---|
| DEV-0001 | True | DOC-DEPLOY-001 | yes | DOC-DEPLOY-003 | DOC-DEPLOY-003 | draft_ready | review | auto_respond | agent_review |
| DEV-0003 | True | DOC-SEC-003 | yes | DOC-SEC-003 | - | needs_human | review | escalate | ask_clarification |
| DEV-0004 | True | DOC-DEPLOY-002 | yes | DOC-DEPLOY-002 | - | not_generated | escalate | auto_respond | - |
| DEV-0006 | True | DOC-DEPLOY-004,DOC-ACCT-002 | yes | DOC-DEPLOY-004 | DOC-DEPLOY-004,DOC-SEC-002 | draft_ready | review | auto_respond | agent_review |
| DEV-0008 | True | DOC-AUTH-001 | yes | DOC-AUTH-002 | - | needs_human | review | auto_respond | escalate |
| DEV-0009 | True | DOC-DEPLOY-002 | yes | DOC-DEPLOY-002 | - | not_generated | escalate | auto_respond | - |
| DEV-0010 | True | DOC-DEPLOY-004,DOC-ACCT-002 | yes | DOC-DEPLOY-004 | DOC-DEPLOY-004 | draft_ready | review | auto_respond | agent_review |
| DEV-0012 | True | DOC-DATA-001 | yes | DOC-DATA-001 | DOC-DATA-001 | draft_ready | review | auto_respond | agent_review |
| DEV-0014 | True | DOC-AUTH-003 | yes | DOC-AUTH-003 | DOC-AUTH-003 | draft_ready | review | auto_respond | agent_review |
| DEV-0015 | True | DOC-SEC-001 | yes | DOC-SEC-001 | - | not_generated | escalate | escalate | - |
| DEV-0016 | True | DOC-AUTH-004,DOC-SEC-002 | yes | DOC-AUTH-004 | - | not_generated | escalate | auto_respond | - |
| DEV-0017 | True | DOC-ACCT-001 | yes | DOC-ACCT-001 | DOC-ACCT-001 | draft_ready | review | auto_respond | agent_review |
| DEV-0315 | True | DOC-DEPLOY-002 | yes | DOC-DEPLOY-002 | - | not_generated | escalate | auto_respond | - |
| DEV-0492 | True | DOC-DATA-003 | yes | DOC-DATA-003 | DOC-DATA-003 | draft_ready | review | auto_respond | agent_review |
| DEV-0380 | True | DOC-DEPLOY-002 | yes | DOC-DEPLOY-002 | - | not_generated | escalate | auto_respond | - |
| DEV-0074 | True | DOC-BILL-003,DOC-API-001 | yes | DOC-BILL-003 | - | needs_human | review | auto_respond | escalate |
| DEV-0386 | True | DOC-DEPLOY-002 | yes | DOC-DEPLOY-002 | - | not_generated | escalate | auto_respond | - |
| DEV-0094 | True | DOC-ACCT-001 | yes | DOC-ACCT-001 | DOC-ACCT-001,DOC-AUTH-004,DOC-SEC-001 | draft_ready | review | auto_respond | agent_review |
| DEV-0185 | True | DOC-DATA-001 | yes | DOC-DATA-001 | - | needs_human | review | auto_respond | escalate |
| DEV-0218 | True | DOC-AUTH-001 | yes | DOC-AUTH-001 | DOC-AUTH-001 | draft_ready | review | auto_respond | agent_review |
| DEV-0066 | True | DOC-API-002 | yes | DOC-API-002 | DOC-API-002,DOC-DATA-001 | draft_ready | review | auto_respond | agent_review |
| DEV-0414 | True | DOC-BILL-003 | yes | DOC-BILL-003 | - | not_generated | escalate | auto_respond | - |
| DEV-0247 | True | DOC-BILL-001 | yes | DOC-BILL-001 | DOC-BILL-001 | draft_ready | review | auto_respond | agent_review |
| DEV-0166 | True | DOC-API-002,DOC-API-003 | yes | DOC-API-002 | DOC-API-002,DOC-DATA-001 | draft_ready | review | auto_respond | agent_review |
| DEV-0121 | True | DOC-SEC-001,DOC-SEC-002 | yes | DOC-SEC-001 | DOC-AUTH-004,DOC-SEC-001,DOC-SEC-002 | draft_ready | review | escalate | agent_review |
| DEV-0224 | True | DOC-DEPLOY-001,DOC-DEPLOY-003 | yes | DOC-DEPLOY-001 | - | not_generated | escalate | auto_respond | - |
| DEV-0161 | True | DOC-ACCT-001 | yes | DOC-ACCT-001 | DOC-ACCT-001 | draft_ready | review | auto_respond | agent_review |
| DEV-0367 | True | DOC-INT-001 | yes | DOC-INT-001 | DOC-AUTH-004,DOC-INT-001 | draft_ready | review | auto_respond | agent_review |

Pooled retrieval hit among answerable tickets with expected docs: 100.0% (28/28; 88%-100%); top-1 retrieved doc is an expected doc: 92.9% (26/28; 77%-98%).

- answerable_from_docs=True: answer_status {'draft_ready': 15, 'needs_human': 4, 'not_generated': 9}

Pooled citation doc-ID match: 65.2% (15/23; 45%-81%) cited IDs equal an expected doc; drafts produced for tickets labelled not answerable: 0.

Classification in the same 28 probes: intent 82.1% (23/28; 64%-92%), urgency 53.6% (15/28; 36%-70%).

PR-03-v3 vs v2 on the same 15 paired tickets (one v3 row failed validation): v2 urgency 10/15, v3 10/15; both samples are far too small to distinguish prompts.

urgency_spectrum_development: 30 tickets across 7 different free models (not a controlled run): urgency 12/30 match; ambiguous 4, evidence invalid 1. Excluded from quantitative conclusions.

**Reading.** These are 28 tickets (DEV-0001..0017 subset and 16 others; selection procedure not documented in the files I read), none overlapping the 341-ticket set, **all answerable_from_docs=true**; 95% intervals on any rate are about +/-10-20 points. Retrieval looks healthy where it was tested (28/28 expected-doc hits, 26/28 top-1). The 15/23 citation-ID match is a proxy: several 'mismatches' cite a plausible neighbouring document (e.g. DOC-AUTH-004 or DOC-DATA-001 added to an expected doc), so it measures agreement with a possibly incomplete expected_doc_ids list, not wrong claims. Nine of 28 produced no draft because urgency=high escalated them (`not_generated`); 4 `needs_human`. Whether the system declines or fabricates on the 143 unanswerable dev tickets (28.6% of dev) is untested. The urgency_spectrum file mixes seven different free models and is excluded from any quantitative claim; the v3 vs v2 comparison (10/15 vs 10/15) is an inconclusive null.

## 6. Label quality

Sampled 64 urgency errors (58 conflict-free, 6 from conflicting-text groups).

| judgment | n (all) | n (conflict-free) | n (conflict group) |
|---|---|---|---|
| a | 7 | 6 | 1 |
| b | 34 | 32 | 2 |
| c | 23 | 20 | 3 |

(a) gold consistent with the rubric, model wrong; (b) rubric-ambiguous / defensible either way; (c) gold contradicts the rubric.

| gold -> predicted | n sampled | a | b | c |
|---|---|---|---|---|
| high -> low | 4 | 0 | 0 | 4 |
| high -> medium | 15 | 0 | 9 | 6 |
| low -> high | 5 | 0 | 0 | 5 |
| low -> medium | 15 | 1 | 12 | 2 |
| medium -> high | 10 | 5 | 4 | 1 |
| medium -> low | 15 | 1 | 9 | 5 |

Stratum-weighted extrapolation to all 116 conflict-free urgency errors (error-cell sizes as weights; sample is 58 tickets judged by a single reader, so treat as rough): (a) 8%, (b) 60%, (c) 32%.

Examples (a):

- DEV-0002 gold=medium pred=high: "One of our production keys started returning 401 at around yesterday morning without any change on our side. Other keys against the same account are still working." -- one production key 401, other keys still work (workaround): medium; model said high
- DEV-0397 gold=medium pred=high: "one of our production keys start returning 401 at around on Monday without any change on our side. Other keys against same account still working." -- same as DEV-0002
- DEV-0476 gold=medium pred=high: "One of our production keys started returning 401 at around around 14:00 yesterday without any change on our side. Other keys against the same account are still working." -- same as DEV-0002 (copy of the text is labelled high)

Examples (b):

- DEV-0349 gold=high pred=medium: "We are getting errors saying no connection is available. This started when we scaled up our service. The database itself shows very few active queries." -- 'no connection available' errors after scale-up; production impact not stated, high or medium
- DEV-0322 gold=high pred=medium: "We are getting errors saying no connection is available. This started when we scaled up our service. The database itself shows very few active queries." -- identical text to DEV-0349
- DEV-0472 gold=high pred=medium: "A restore we started last Friday is still running. The database is about four hundred gigabytes. Is this a normal duration or has something stalled?" -- 400 GB restore running since Friday, may be stalled; medium or high

Examples (c):

- DEV-0044 gold=low pred=high: "Usage allowance already consumed our spend cap stop production workload overnight. We need it raised immediately and then we need to reconsider how we have this configured. please do the needful." -- spend cap stopped a production workload overnight, 'raised immediately' = critical production unavailability, gold is low
- DEV-0050 gold=high pred=low: "Question about this month's charges invoice showing service we not use. can you check and tell?" -- plain billing question (service we do not use) with no harm or deadline, gold is high
- DEV-0273 gold=high pred=low: "can you please point me at right starting place? i am having created account but the console has more in it than I expect." -- 'point me at the right starting place' is a routine onboarding question, gold is high

### History fields vs gold urgency (observation only; all 500 dev tickets)

| gold urgency | n | median resolution min | IQR | mean csat | escalated | first-contact resolved | repeat contact |
|---|---|---|---|---|---|---|---|
| low | 128 | 132 | 32-782 | 3.06 | 51.6% | 48.4% | 14.8% |
| medium | 226 | 188 | 35-749 | 2.99 | 56.2% | 43.8% | 26.1% |
| high | 146 | 342 | 38-892 | 2.86 | 60.3% | 39.7% | 20.5% |

AUC of resolution_time_minutes separating urgency classes (0.5 = no relationship), overall and within escalated / non-escalated:

| pair | all | escalated only | not escalated only |
|---|---|---|---|
| high vs low | 0.560 | 0.534 | 0.530 |
| high vs medium | 0.550 | 0.561 | 0.550 |
| medium vs low | 0.511 | 0.475 | 0.477 |

Resolution time by history.escalated: median 745 min (escalated, n=281) vs 32 min (not escalated); max non-escalated 55 min, min escalated 91 min (disjoint ranges).

Gold urgency is strongly tied to intent for a few intents (security_incident 92% high, rollback_request 82% high, api_usage_question 4% high) -- predicting the majority urgency of the gold intent matches 55.2% (276/500; 51%-60%) of all 500 labels in-sample.

Conflicting-text groups: 67; 20 contain both a high and a low label (two-level disagreement); 52 of 67 have differing customer_tier across copies. Resolution-time AUC above is weak, so copies are not separable by an obvious history signal.

**Reading [judged].** One reader (the analyst, applying the rubric text in `src/classification.py`) judged each sampled error. The sample is stratified by (gold, predicted) error cell: all of the small cells, 14 from each large cell, plus one conflict-group error per cell, so raw counts over-represent rare cells; the weighted figure is the better summary. Treat the split as roughly one-tenth clear model errors, three-fifths defensible-either-way, one-third rubric-contradicting gold labels, with at least +/-10 points of uncertainty from the sample size and the single reader. Patterns in (c): 'routine question' tickets labelled medium/high (onboarding, billing, CI-key choice), obviously production-impacting tickets labelled low (spend cap stopped production, all automated jobs failing authentication), and active-compromise evidence labelled medium. Identical scenarios appear with gold low and high (the SSO provisioning and shared-account password scenarios), which cannot be rubric-consistent for both.

Observations on history fields (observation only; none may be classifier input): resolution time is determined mainly by `escalated` (all non-escalated <= 55 minutes, all escalated >= 91 minutes). Within each escalation group, resolution time separates urgency classes barely better than chance (AUC 0.53-0.56 high vs others; 0.48 medium vs low), and escalation, FCR and CSAT differ by only 8, 8 and 0.2 points across urgency levels (repeat contact by up to 11 points, non-monotonically). Nothing here suggests labels were produced from history; if anything urgency looks assigned largely independently of the observed fields, with a moderate dependence on intent (tied to the scenario).

## 7. Prompt and policy implications

Hypotheses are listed in the order I would test them. Each is stated so it can fail.

**Preconditions (not prompt changes)**
- **P0 - scenario-grouped split.** Build fit/holdout by scenario cluster (and keep identical texts together), not by exact-text hash. Currently 87/90 holdout tickets have a paraphrase sibling in `fit`, so few-shot examples, per-intent priors and calibrators are all evaluated on paraphrases of their training material. Test: re-run the leakage count (target 0). Zero-shot prompt variants contain no fitted component and can be compared on all 341 tickets with a paired test; only few-shot/threshold/calibration work needs the split.
- **P1 - agree what 'correct urgency' means before optimising it.** With 67/97 exact-duplicate conflicts and 45% within-scenario agreement, an accuracy target near 85% is unreachable on dev labels. Options for the owner: (i) report urgency against the rubric-consistent subset only after a documented audit, (ii) score urgency ordinally/with tolerance for adjacent levels (48% of predictions are off by one), (iii) accept urgency as advisory and take it out of the auto-respond gate. This is a decision, not an experiment.

**Prompt hypotheses**
| id | change | metric and slice | success criterion | what the data say / risk |
|---|---|---|---|---|
| H1 | Add one-line definitions and tie-break rules for the confusable intents (integration_help vs webhook_issue/configuration_help; api_key_issue vs authentication_failure vs security_incident; compliance_request vs data_export; database_issue vs performance_degradation; onboarding vs configuration_help; quota_or_overage vs billing_query). Zero-shot. | intent accuracy and per-class recall on all 341, paired vs PR-03-v2; macro recall | integration_help recall >= 50% (from 0/13), macro recall >= 0.87 (from 0.844), no class loses > 10 points recall, net discordant gain >= 10 tickets | Errors are ~15 scenarios, so there are only ~15 independent decisions: gains could be label-convention fitting. Needs a post-hoc check on the later validation run by someone permitted to use it. |
| H2 | Urgency rubric: make 'routine question / planned work / how-to' explicitly low even when the customer is polite or mentions an invoice, and make 'workaround exists' explicit medium. | urgency accuracy on conflict-free 236, medium->low and low->medium cells | no loss on security/rollback (>= 90%); overall CF accuracy >= 55% | The v3 attempt (active-problem vs routine clarification) tied v2 (10/15). Many gold labels contradict the same rubric (36% of sampled errors), so expected gain is small. |
| H3 | Raise high recall outside security/rollback (currently 11/65). | gold-high recall and predicted-high precision on CF | recall >= 35% with precision >= 60% | Of the 19 sampled gold-high errors, I judged none a clear model error (9 ambiguous, 10 gold contradicts rubric) [judged]; false highs already come from api_key_issue (7), quota_or_overage (5), deployment_failure (5). Expect precision loss; low prior. |
| H4 | Separate calls for intent and urgency. | urgency accuracy on all 341 paired; also intent | urgency CF accuracy +5 points with sign-test p < 0.1 | Joint odds ratio 2.9 shows correlated difficulty, not obviously coupling. Costs 2x calls. Weak evidence for. |
| H5 | Few-shot exemplars (6-9) taken from the `fit` split, scenario-disjoint from the evaluation slice, including rubric-consistent medium/low examples and the 'urgent wording is not enough' case. | CF urgency accuracy on scenario-disjoint holdout; vs per-intent leave-one-out baseline | >= baseline + 5 points on >= 100 CF tickets | Only valid after P0. Few-shot teaches label conventions that may be noise; check that gains do not come from the two near-deterministic intents. |
| H6 | Replace numeric self-confidence with (a) a categorical clear/borderline/ambiguous field or (b) agreement across k samples (identical texts already produced different outputs in 13 groups). | AUROC of the signal for correctness, CF 236 | AUROC >= 0.62 with lower CI bound > 0.55 (now 0.50) | Label noise caps achievable AUROC; the signal could still gate review of unstable predictions. Intent confidence already has 0.65. |
| H7 | Make ambiguity detection track text ambiguity. | accuracy of flagged vs unflagged; flag rate on gold-conflict texts | flagged accuracy >= 10 points below unflagged | Currently inverted (53.6% vs 47.0%) and fires 2.9% on conflict-label texts. Identical texts with different labels cannot be detected from text at all, so ceiling is low. |

**Policy / harness changes the data support (not prompt work)**
- **R1 - must_not routing rule.** Escalate when predicted intent is in {security_incident, compliance_request, feature_request, unclear_request} before any confidence check. Metric: must_not violations in the 'what-if confidence enabled' simulation (now 30/64) -> 0 on all 341, and rule precision >= 95% (measured 100%, n = 16 on holdout). This needs no calibration.
- **R2 - route metric.** Report routing as 'did not auto-respond when escalation was expected' (handoff recall), auto-respond precision, and exact match separately; state that `review` cannot equal a label. Success: the report no longer scores a safe review as a plain miss.
- **R3 - answerability.** `answerable_from_docs` is the strongest non-intent predictor of escalation (143/143), although the flag itself conflicts across identical texts in 36/97 groups. Test retrieval-score or draft-refusal as a runtime proxy on a probe that includes unanswerable tickets (none exist today).

**What prompt work cannot fix**
- Conflicting and near-random urgency labels (exact-duplicate conflicts; 45% vs 35.5% within-scenario agreement) and the 36% of sampled errors where gold contradicts the rubric.
- The `review` route being unmatched by any label, and routing labels that depend on KB coverage and history rather than urgency.
- The calibrated-urgency ceiling: with ~50% accurate labels, calibrated urgency cannot reach 0.80, so auto-respond stays off unless the gate is redefined.
- Sampling limits: 341 tickets from ~76 scenarios; any per-class claim for n < 10 classes.

**Tension with the architecture rule.** `docs/architecture.md` says customer tier, intent, route and history "do not determine urgency". The classifier prompt forbids using tier, route and historical outcome as proxies but does not mention intent. The data show gold urgency is partly predictable from intent (per-intent majority 55.2% in-sample on 500; 91% on security_incident/rollback_request, where the rubric itself implies high). I read the rule as 'do not use as a proxy', and the model is already consistent with that outside those two intents (it is below the intent prior there). Do not add an intent-conditioned urgency prior to the prompt: it would improve in-sample accuracy by ~10 points (58.4% vs 47.5%) but, held out, the gain largely disappears (49-52%), and it contradicts the stated rule. If H5 few-shot examples are used, check that they do not smuggle in an intent prior.

**Bottom line.** [inferred] Do not redo PR-03 wholesale to chase urgency accuracy. Order of work: P0, R1/R2, then H1 (cheap, zero-shot, evaluable on all 341), then at most one of H4/H5/H6 for urgency, accepting that the dev labels cap the measurable gain at a few points.
