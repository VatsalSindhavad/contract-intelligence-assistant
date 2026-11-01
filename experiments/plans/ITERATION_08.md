# Proposal declared before iteration 8

Keep the accepted document-then-clause routing and focused-query fallback.
Add English Snowball stemming to indexed and query tokens. Query scaffolding
is removed before stemming; the original stored text and offsets are unchanged.
For example, license/licenses/licensing share a stem. This is morphological
normalization, not semantic synonym recognition or an LLM.

Motivation: iteration 7 still has 50 zero-overlap and 33 partial-coverage
answerable train failures at k=5. Surface-word differences may contribute.
No individual gain is assumed; stemming can also merge distinct legal terms
or affect document routing. Preserve qualifiers rather than dropping negation.

Only the `stemming` setting changes. Keep chunking, BM25 parameters, k, score
threshold, and all numerical acceptance rules fixed. Compare the candidate
with accepted iteration 7 and the original baseline. Commit this proposal
before measuring it. NLTK's bundled Snowball implementation needs no downloaded
language data. This remains core lexical retrieval; test is not evaluated.
