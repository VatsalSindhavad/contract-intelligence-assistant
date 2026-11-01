# Dense abstention control and first hybrid

Declared before measurement. Iteration 18 tests original fixed-window MiniLM
at the same six cutoffs as enriched MiniLM (0.40/0.45/0.50/0.55/0.60/0.65).
Use the same selection criteria: precision at least 95% of ungated retrieval,
recall loss at most two percentage points, false answerable abstention at
most 5%, and strictly improved correct negative abstention. Choose highest
correct negative abstention, then recall, precision, then lower threshold.
This isolates cutoff effects from enrichment and saves all predictions.

Iteration 19 combines the best accepted lexical configuration (focused,
stemmed BM25) with original MiniLM + FAISS. Original MiniLM is chosen over
clause/enriched variants because its ungated precision and recall are both
higher. Both components use identical original 1,000-character windows with
200-character overlap. Retrieve 20 candidates per component, deduplicate by
source offsets, and sum weighted reciprocal ranks: 0.75 lexical, 0.25 dense,
constant 60. Weights reflect the much stronger measured lexical reference;
they are fixed before scoring, not selected from test performance.

Compare against BM25 and dense on all 140 answerable and 23 negative train
questions. No reranker or LLM. Require recall gain at least one point over
BM25, precision at least 95% of BM25, correct abstention no worse, and false
abstention at most 5%. Report latency separately. Log rejection honestly.
The six dense top-score cutoffs are also measured as separate hybrid
abstention trials under the same 5% and two-point recall constraints. This
uses cosine confidence, never RRF scores as probabilities. Original semantic
confidence can miss lexical support; that is a known hypothesis to test.
Threshold qualification alone does not qualify the hybrid against BM25.

All threshold outcomes are train tuning estimates. Test remains untouched.
