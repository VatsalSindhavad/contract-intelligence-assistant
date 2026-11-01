# Proposal declared before iteration 5

Saved baseline predictions identify the correct source contract at rank 1 for
all 140 answerable train questions, but 103 questions have no gold span coverage
at k=5. All train questions use the explicit `Consider ...; question` format.
This suggests separating contract identification from passage ranking.

Add the `document_then_clause` query mode: use the full query's highest-scoring
BM25 passage to infer one contract; score passages in that contract using the
question after the first semicolon. No source IDs or labels are supplied to
search. For unformatted questions, retain the original full-query behavior.
Keep chunking, BM25 parameters, threshold, and k unchanged.

This rule is now the first untried catalog item for wrong-section failures.
The catalog amendment is explicit and occurs before candidate measurement.
The numerical acceptance policy is unchanged. No dense retrieval, LLM,
reranker, clause-aware chunking, or reference resolution is added.

Risks: one incorrectly inferred document can discard all relevant passages;
format-dependent parsing may not help free-form questions. Measure train
quality and both abstention directions; report these limits. Test remains
untouched. The user now allows up to ten total iterations and requests two
accepted non-LLM improvements before LLM work. Acceptance is not guaranteed.
