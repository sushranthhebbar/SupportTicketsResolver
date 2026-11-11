# Two-assessor draft review

1. Two people each read `review_packet.md` (50 drafts from the final validation run) and
   fill in their own sheet: `assessor_A.csv` and `assessor_B.csv`. Work separately; do not
   compare scores until both are done. The rubric is at the top of the packet.
2. Run `python scripts/score_draft_review.py`. It checks the sheets, then writes
   `review_summary.json` with each assessor's hallucination rate and citation accuracy,
   percent agreement, Cohen's kappa, and the list of disagreements.
3. The assessors resolve the listed disagreements together and record the agreed call.
   Report the agreement figure from step 2 (before resolving), and the rates from both.

The packet has no gold labels and none of the author's earlier review notes
(`docs/validation_draft_review.md`), which should not be read before scoring.
The sheets are blank until the assessors fill them in.
