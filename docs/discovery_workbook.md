# Stage One Discovery Workbook

> Markdown transcription of the supplied Word workbook. Fill in the tables as evidence is gathered. The original template is preserved.

FORWARD DEPLOYED AI ENGINEERING

Capstone Project

Stage One: Discovery

The workbook you complete before you design anything

Fill this in first. Nothing in the later stages is valid unless it can be tracedback to something you recorded on these pages.

| WEEK ONE  ·  DAYS ONE TO THREE |
| --- |

How to use this workbook

This workbook is a set of tables for you to complete. The prompts in the left-hand column tell you what belongs in each row; the remaining columns are yours to fill in. Where a table has blank rows at the bottom, add as many more as you need.

Work through the sections in order. Section one establishes who you are talking to, sections two to five gather the evidence, and section six is where you turn that evidence into a problem statement. Do not attempt section six before the others are genuinely finished, because the whole point of the exercise is that the conclusion follows from the evidence rather than the other way round.

| What finished looks likeYou are finished with discovery when a further interview tells you nothing you did not already know, and when every claim in your problem statement can be pointed at a specific row in one of these tables. If either of those is not yet true, you are not finished, however much time has passed. |
| --- |

Figure 1. Discovery repeats until the answers stop changing.

1   Section one: what the interviews tell you

Your discovery evidence is in two places: the five stakeholder interview transcripts in the datasets folder, and the ticket data itself. Start with the transcripts. Read all five before you write anything, then come back and fill in the table below.

The prompts in the left column are the people you spoke to. For each, record what you were trying to learn from them, what they actually told you, and, importantly, what they seemed not to know about their own operation. That last column is often where the useful material is, because each of the five can only see their own part of the problem.

| Who | What they told you | What they appear not to know | What you want to verify in the data |
| --- | --- | --- | --- |
| Marcus Adeyemi, Head of Support | Wants easier tickets answered so agents can focus on harder work and response times improve without more headcount. Reports first response averages 8–12 hours against a two-hour agreement; first-contact resolution is 42%, which matters to him more than response time. Incorrect answers, added agent workload, poorer enterprise service, and an inability to explain decisions would make the project fail. | He does not know the ticket mix in detail and says any breakdown would be a guess. He sees the escalation rate but may not know how many escalations were straightforward or driven by low confidence/findability. He also does not know from the interview how outcomes vary by language fluency or tier in the full dataset. | Count tickets by intent, urgency, channel, tier, and language fluency. Measure first-contact resolution, escalation, resolution time, repeat contacts, and CSAT across those groups. Check the share answerable from documentation and how many escalations concern doc-answerable issues. |
| Sofia Restrepo, Tier One Agent | Receives roughly 40–70 tickets per day and prioritizes by age. Familiar tickets can take 4–5 minutes; unusual ones up to 40 minutes before escalation. She estimates about 70% are familiar and says agents often rely on personal answer files because internal documentation search is painful. She is open to a relevant article plus a draft for agent review. She believes non-fluent customers take longer and receive the worst satisfaction. | Her estimate that seven in ten tickets are familiar is based on experience, not a count. She may not see how her own queue patterns compare with the whole team, and she does not know whether non-fluent customers actually have worse outcomes across the dataset. | Compare ticket intents and repeated question patterns with her estimate. Analyze first-contact resolution, escalation, resolution time, repeat contacts, and CSAT by language fluency. Check documentation answerability and expected document IDs to see how often a relevant article exists. |
| Daniel Okonkwo, Tier Two Engineer | Says about half of escalations reaching him could have been resolved at tier one with enough confidence or the right documentation; many are answered with a link and a short explanation. Escalations often arrive without a summary or record of prior troubleshooting, so he rereads the thread and repeats questions. He wants context and visible reasoning. He warns that old private snippets may be wrong. | He does not provide a measured estimate of the share of all escalations that tier one could resolve; his “about half” is an informed observation. He may not know how that share varies by intent, documentation coverage, urgency, or customer segment. | Among tickets labeled for escalation, inspect intent, answerability, expected documents, and outcomes. Estimate the share that is documentation-answerable or resolved quickly, while treating those as indicators rather than proof that escalation was unnecessary. Compare escalation and resolution outcomes by category. |
| Ines Varga, Technical Writer | Maintains 29 support knowledge-base articles, which she considers accurate within their review cycle. She believes support agents rarely use them because internal search matches titles and exact terms, while customers describe problems differently. Agents recreate article answers from memory and keep unreviewed personal snippets. She wants any system to identify the source article so errors can be traced to documentation or system behavior. | She says she does not think support uses the articles, but has no usage measurement in the interview to establish how often. She may not know which intents are actually covered, how often tickets are answerable from the corpus, or where article coverage and ticket phrasing fail to match. | Compare each ticket’s answerability label and expected document IDs with the 29-article corpus. Measure documentation-answerable share by intent and look for frequent questions with no expected document. Treat actual internal search usage as unknown unless a usage dataset is supplied. |
| Ravi Menon, Customer | Describes support as slow but good once reached. Waiting matters more when a deployment blocks shipping than for a low-impact how-to question. He searches documentation himself and says he finds an answer about half the time; eventual support replies often repeat it. He would value a clearly disclosed machine draft with its source and human confirmation, but would reject confident incorrect answers or hidden automation. He worries the change could widen the service gap between business and enterprise customers. | His experience is one customer’s account, not a measure of all customers. He cannot know whether customers generally find answers at the same rate, whether urgency predicts impact or wait-time harm, or whether business customers actually receive slower or worse outcomes than enterprise customers across the dataset. | Compare outcomes by urgency and customer tier, including resolution time, first-contact resolution, escalation, and CSAT. Check repeat-contact and documentation-answerability rates. Note that the ticket dataset may not measure customer self-service searches or whether an automated draft was disclosed; those remain evidence gaps. |

Where the accounts disagree

At least three points of disagreement run through the transcripts, and each can be settled by going to the ticket data rather than by deciding whose account sounds more convincing. Identify them, then resolve them with evidence.

| The disagreement | Who says what | How the data settles it | What follows from the answer |
| --- | --- | --- | --- |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

What nobody said

Real stakeholders leave out the things so familiar to them that they no longer notice them. Record anything you expected somebody to raise that none of the five actually did.

| What was never mentioned | Why you would have expected it | How you will check it |
| --- | --- | --- |
|  |  |  |
|  |  |  |
|  |  |  |
|  |  |  |

2   Section two: what the ticket data shows

Before you interpret anything, count it. Load development_tickets.json and fill in the table below from the data itself rather than from impression. Where a figure surprises you, write the surprise down; those are usually the most productive threads to pull.

| What to measure | Your figure | Where the figure came from | What surprised you about it |
| --- | --- | --- | --- |
| Total tickets in the sample | 500 | Source: `evaluation/data/development_tickets.json`; count the top-level ticket records (500 unique IDs, DEV-0001–DEV-0500). |  |
| Split by channel | email: 42.4%<br>chat: 31.0%<br>docs_comment: 15.6%<br>forum: 11.0% | Group all 500 records by `channel`; counts are email 212, chat 155, docs_comment 78, and forum 55. Divide each by 500. |  |
| Split by intent category | account_access: 4.4%<br>api_key_issue: 3.6%<br>api_usage_question: 4.8%<br>authentication_failure: 4.0%<br>billing_query: 4.8%<br>compliance_request: 5.2%<br>configuration_help: 3.4%<br>data_export: 5.8%<br>data_residency: 5.8%<br>database_issue: 5.2%<br>deployment_failure: 5.4%<br>feature_request: 4.0%<br>integration_help: 4.2%<br>onboarding: 4.4%<br>performance_degradation: 4.6%<br>quota_or_overage: 4.6%<br>rate_limit: 2.6%<br>rollback_request: 5.6%<br>security_incident: 5.2%<br>sso_configuration: 5.2%<br>unclear_request: 3.0%<br>webhook_issue: 4.2% | Group all 500 records by `labels.intent`; divide each category count by 500. Category counts in the same order as listed: 22, 18, 24, 20, 24, 26, 17, 29, 29, 26, 27, 20, 21, 22, 23, 23, 13, 28, 26, 26, 15, 21. |  |
| Split by urgency | medium: 45.2%<br>high: 29.2%<br>low: 25.6% | Group all 500 records by `labels.urgency`; counts are medium 226, high 146, low 128. Divide each by 500. |  |
| Proportion marked resolved on first contact | 43.8% | `history.first_contact_resolution` is `true` for 219 of the 500 tickets; divide 219 by 500. |  |
| Average satisfaction rating | 2.97 out of 5 | Arithmetic mean of `history.csat_rating` across all 500 tickets; rounded to two decimals. |  |
| Most frequent single question | “How do I revert to an earlier revision? The release we put out this morning is causing errors and I would rather roll back than try to fix forward.” (2.8% of tickets) | Group `body` text after trimming, lowercasing, and collapsing whitespace; the top phrase appears in 14 of 500 records (2.8%): DEV-0009, DEV-0040, DEV-0042, DEV-0122, DEV-0127, DEV-0157, DEV-0163, DEV-0263, DEV-0315, DEV-0339, DEV-0345, DEV-0386, DEV-0423, DEV-0473. |  |
| Proportion answerable from existing documentation | 71.4% | `labels.answerable_from_docs` is `true` for 357 of the 500 tickets; divide 357 by 500. |  |
| Proportion marked non-fluent, and their outcomes | Non-fluent: 24.0%<br>First-contact resolution: 45.8%<br>Average satisfaction: 3.04/5<br>Escalated: 54.2%<br>Repeat contact: 19.2%<br>Mean resolution time: 466.1 minutes | `language_fluency` = `non_fluent` for 120 of 500 tickets. Within that segment, `history.first_contact_resolution` is true for 55, `escalated` true for 65, and `repeat_contact` true for 23; average `csat_rating` is 3.04 and average `resolution_time_minutes` is 466.1. |  |
| Outcomes by customer tier | Business<br>First-contact resolution: 48.2%<br>Satisfaction: 2.91/5<br>Escalated: 51.8%<br>Repeat contact: 23.2%<br>Mean resolution time: 358.8 minutes<br><br>Enterprise<br>First-contact resolution: 37.3%<br>Satisfaction: 3.05/5<br>Escalated: 62.7%<br>Repeat contact: 24.1%<br>Mean resolution time: 483.7 minutes<br><br>Standard<br>First-contact resolution: 43.1%<br>Satisfaction: 2.98/5<br>Escalated: 56.9%<br>Repeat contact: 19.8%<br>Mean resolution time: 442.1 minutes | Group records by `customer_tier` (business 164, enterprise 83, standard 253). For each tier, calculate rates from `history.first_contact_resolution`, `escalated`, and `repeat_contact`; average `csat_rating` and `resolution_time_minutes`. |  |
| Proportion that are repeat contacts | 21.6% | `history.repeat_contact` is `true` for 108 of the 500 tickets; divide 108 by 500. |  |
|  |  |  |  |
|  |  |  |  |

| Two rows matter more than the restThe proportion of tickets already answerable from existing documentation tells you whether CloudServe lack answers or merely lack a way of reaching them. Those are different problems with different solutions. The non-fluent segment matters for a different reason: something in the transcripts points at it, and the data will tell you whether that person was right. |
| --- |

3   Section three: where the time actually goes

Understanding volume is not the same as understanding effort. A category that accounts for five per cent of tickets but forty per cent of agent hours is where the real problem lives. Work out, as far as your evidence allows, how effort is distributed.

| Ticket category | Share of volume | Estimated share of effort | Why the two differ | Evidence for your estimate |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

The steps an agent takes on a typical ticket

Sofia describes her working process in some detail in the second transcript. Reconstruct it as a sequence of steps and record roughly where the time goes at each one. The steps that sound trivial are frequently where the minutes accumulate.

| Step | What the agent does | Roughly how long | Could this be automated? Say why or why not |
| --- | --- | --- | --- |
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |
|  |  |  |  |
|  |  |  |  |
|  |  |  |  |

4   Section four: what the client counts as success

You cannot improve a number nobody is watching. Marcus names the figures he reports and is explicit about which one he actually cares about, and they are not the same. Record what CloudServe measure, who watches each measure, and what would have to change for this project to be considered worthwhile.

| Measure | Who watches it | Current value | What they would call success | How confident are you in this? |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

The sentence test

Complete the following sentence using only figures you recorded above. If you cannot complete it, your discovery is not finished.

| Prompt | Your answer |
| --- | --- |
| This project will have been worth doing if, within three months of launch, ... |  |
| We will know it did not work if we see ... |  |
| The measure the client will actually be judged on internally is ... |  |

5   Section five: data, constraints and risk

Everything you build depends on data that already exists, and every piece of that data carries constraints. Record what exists, what condition it is in, and what you are not permitted to do with it. Ines and Daniel both raise concerns about data quality that belong in this table.

| Data source | What it contains | Quality and gaps | Access constraints | Private data present? |
| --- | --- | --- | --- | --- |
| Support tickets |  |  |  |  |
| Documentation |  |  |  |  |
| Past resolutions |  |  |  |  |
| Customer records |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

Initial risk register

List what could go wrong once this system is speaking to customers without supervision. You will develop these further in stage five, but the first pass belongs here, while the problem is still fresh and you have not yet become attached to a particular design.

| What could go wrong | How likely | How bad | Who it affects | First thought on preventing it |
| --- | --- | --- | --- | --- |
| The system answers confidently and incorrectly |  |  |  |  |
| Private information appears in a reply |  |  |  |  |
| Some customers get consistently worse answers |  |  |  |  |
| The documentation the system relies on goes out of date |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

6   Section six: the problem statement

Now, and only now, write down what the problem actually is. Every clause of what you write must be supported by a row you have already filled in, and you are asked to cite those rows explicitly. This is the paragraph your entire project rests on.

| Element | Your statement | Which section and row supports it |
| --- | --- | --- |
| What the client asked for |  |  |
| What the evidence suggests they actually need |  |  |
| The gap between those two |  |  |
| Who is affected and how |  |  |
| What will change if this is solved |  |  |
| What is explicitly not in scope |  |  |

The one paragraph version

Write the problem in a single paragraph, in language the head of support would recognise and agree with. No technical vocabulary. If you cannot express it without mentioning retrieval or embeddings, you are describing your solution rather than their problem.

| Problem statement |
| --- |
|  |
|  |
|  |

| Before you move to stage twoRead your problem statement back against each of the five transcripts in turn and ask whether that person would recognise it as a description of their situation. If any of the five would object, either your framing is off or you have found something they cannot see, and you should be able to say which. A statement that all five would simply agree with is usually one that has not gone far enough. |
| --- |
