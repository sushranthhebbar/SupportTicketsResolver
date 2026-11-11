# Credential and history scan (11 November 2026)

Scope: all 47 commits on every branch and the current tree. `gitleaks` is not installed on
this machine, so I ran the equivalent checks with `git grep` over every revision. Run
`gitleaks detect` on your own machine before submitting as an independent second check.

| Check | Result |
|---|---|
| Is `.env` ignored, and was it ever committed? | Ignored (`.gitignore`); no commit ever added it. |
| Files ever added with names suggesting secrets (`.pem`, `.key`, `secret`, `credential`, `token`, `.db`, `.sqlite`) | None. Only `.env.example` (placeholders). `storage/`, with the decision database, is ignored. |
| Known key formats in any revision (Groq `gsk_`, OpenRouter `sk-or-`, GitHub `ghp_` / `github_pat_`, AWS `AKIA`, Slack `xox*`, Google `AIza`) | No matches. |
| Generic `key/secret/token/password = value` assignments (code and docs, JSON excluded) | Only placeholders (`your_groq_api_key`, `set_a_long_random_agent_token`), a test fixture and the fake values in the guardrail and failure demos. |
| The actual values of `MODEL_API_KEY`, `OPENROUTER_API_KEY` and `AGENT_API_TOKEN` from the local `.env`, searched for in every revision | Not found in any commit. |

Result: no credential found in the history. The fake credentials in
`scripts/demo_guardrail_ticket.py`, `scripts/demo_failure_modes.py` and the tests are
invented strings, not real keys.

Not covered: JSON and JSONL result files were excluded from the generic-assignment search
(they hold ticket text), but the exact-value and known-format searches did include them.
The submission zip must be built from a fresh clone so the local `.env`, `.venv` and
`storage/` are not packed.
