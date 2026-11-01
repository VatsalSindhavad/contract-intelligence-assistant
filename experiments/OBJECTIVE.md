# Improvement objective declared before iteration 1

Maximize mean character recall at k=5 on answerable train questions. Relevant
clause coverage matters because missing restrictions could lead to an incorrect
business decision. Keeping k fixed limits how many passages a reviewer reads.

Accept a candidate only if all conditions hold against the current reference:

- Recall@5 gains at least 1 percentage point, avoiding promotion for tiny gains.
- Precision@5 retains at least 95% of reference precision, limiting added noise.
- False abstention on answerable questions rises by no more than 2 points.
- Correct abstention on train negatives falls by no more than 5 points.
- Search p95 stays below max(50 ms, twice the reference p95), allowing timing
  noise while keeping this small local system responsive.

All points are absolute percentage points unless a ratio is stated. These are
engineering choices for this case study, not validated production tolerances.
The baseline has zero correct negative abstentions, so that guardrail initially
provides no protection. Better abstention must be a later, explicit experiment;
acceptance here never means the system is ready for legal use.

Baseline train diagnosis at k=5: all 140 questions retrieve their source
document; 103 retrieve no answer characters, 22 partially cover the gold span,
and 15 completely cover it. These groups describe top-k span coverage, not a
legal interpretation of correctness.

Iteration 1 proposes removing common function words during both document and
query tokenization. Common words can dilute passage ranking within the correct
contract. Keep chunking, BM25 parameters, score threshold, and k unchanged.
The fixed list preserves negation words such as "not" and "no". This is a
train-only hypothesis; rejection is a valid outcome.

The proposal is authored by Codex from the train failure summary. This step
implements one iteration only. The remaining required iterations will follow
one at a time, with the same objective unless a justified amendment is recorded
before running further candidates. No test results are inspected.
