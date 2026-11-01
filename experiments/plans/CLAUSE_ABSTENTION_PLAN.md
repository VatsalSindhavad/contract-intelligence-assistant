# Clause chunking and abstention experiments

Kanon preparation (iteration 14) was not run: the user chose to avoid its API requirement. No result is claimed.

Iteration 15 replaces fixed windows with deterministic paragraph/numbered-section boundaries and packed sentence units (maximum 700 characters, no overlap). Oversized units split at whitespace; offsets and all source characters are preserved. This is heuristic clause-aware segmentation, not a legal parser. Definitions and cross-reference expansion are a later separate experiment. MiniLM revision, normalized exact FAISS search and full questions remain unchanged. Compare against iteration 11 on the full 140 answerable and 23 negative train questions.

Iteration 16 tests query-level abstention on iteration 15: retain the original ranked results only when the best cosine score exceeds a fixed threshold. Grid declared before measurement: 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80. Log every threshold, including failures. Require precision no worse than ungated clause retrieval, recall loss at most 0.02, false abstention at most 0.02 (at most 2 of 140), and correct negative abstention strictly improved. Among qualifying thresholds choose highest correct negative abstention, then precision, recall, then lower threshold. If none qualify keep ungated retrieval and report the failure.

These are train-set tuning results, not independent validation estimates. No test labels or questions enter tuning. Report negative counts and false answerable abstention alongside both overlap conventions. Never claim a cosine score is a calibrated probability. Do not replace the best BM25 pipeline based only on this dense comparison.

The clause comparison requires at least a one-percentage-point precision gain,
at most two points of recall loss, at most 2% false answerable abstention, and
no loss of correct negative abstention. The runner encoded these criteria
before measurement.

Final measured run: 20261101T075231505226Z. An initial splitter edge case allowed
43 chunks of 701 characters; fixed and fully rerun before final reporting.
The earlier saved run is superseded, not a separate model iteration. Kanon
remains unrun. The 0.50 gate qualifies relative to clause retrieval only;
the clause configuration itself fails the recall guardrail against MiniLM.

Post-measurement preference: retain 0.60 as the user-preferred exploration
variant, alongside 0.50. This does not retroactively change acceptance rules.
No numeric maximum is prescribed by the assignment. A 5% false-abstention
ceiling would still reject 0.60 (10/140 = 7.14%).

The user subsequently set 5% as the false answerable abstention ceiling for
future experiments (experiments/abstention_policy_v2.json). This allows at
most 7 of the current 140 answerable train queries to be wrongly rejected.
Use this policy in future experiment selection together with separately
declared precision/recall guardrails. Historical 2% decisions remain intact;
0.60 remains above the new limit as well.
