# Unanswerable evaluation set

`unanswerable.json` contains 30 synthetic negative questions, created after
the initial BM25 retrieval baseline and before any improvement experiment.
No negative-query retrieval scores were inspected before freezing the set.
Labels mean the indexed corpus does not establish the requested answer;
they do not imply that the answer is false in the real world.

Three categories have ten questions each:

- Missing agreements: fictional counterparties and an absent agreement.
- Missing provisions: a named indexed contract and an unsupported technology
  requirement. Search anchors are checked across the complete indexed corpus.
- Subsequent events: an indexed contract and a specific 2026 operational fact
  that cannot be established from this historical corpus.

Construction uses corpus-wide literal searches, source-document inspection,
and the temporal boundary of the documents. Search absence alone is not a
semantic proof. Synthetic topics and fictional agreements may be easier than
realistic near-miss clauses; later human/legal review remains necessary.
This is a reproducible initial evaluation set, not expert legal annotation.

`frozen_manifest.json` binds the questions to the exact corpus text hashes.
`03_unanswerable_validation.ipynb` checks the labels' supporting conditions,
the required deterministic split, and the frozen hashes before evaluating
the unchanged baseline on **train negatives only**. It never retrieves test
negatives. Questions must not be changed during the improvement loop.

The first Git commit freezes this set before improvement work. Its commit
hash can be found with `git log -- evaluation/unanswerable.json`.
