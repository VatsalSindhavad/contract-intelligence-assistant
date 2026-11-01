# Iteration 17: definition and cross-reference context

Declared before scoring. Use original fixed-window MiniLM + FAISS as the
reference because clause chunking was rejected for recall loss. The corpus
alone provides numbered section headings and quoted-term definitions. Resolve
only unique same-document targets; leave absent or ambiguous targets unresolved.
No gold spans enter indexing or retrieval. Keep every original passage and its
offsets unchanged. Do not recursively expand references.

Encode up to 900 characters of additional context separately using the same
pinned MiniLM model; normalize the original vector plus 0.25 times the context
vector. Separate encoding avoids replacing original passage tokens with added
context. The 256-wordpiece encoder limit still applies independently to both
inputs; record context truncation. Context is used only for ranking, never
scored as if it were returned evidence. Save resolved targets and offsets.

Evaluate all 140 answerable and 23 negative train questions at k=1/3/5/10.
Report both overlap conventions, hit rate, both abstention directions, query
latency and indexing time. Accept enrichment only if precision improves by
at least 0.005 or recall by at least 0.01, neither falls by more than 0.02,
false abstention is at most 5%, and correct negative abstention does not fall.

Then separately log top-score thresholds 0.40/0.45/0.50/0.55/0.60/0.65.
Require precision at least 95% of ungated enrichment, recall loss at most two
points, false abstention at most 5%, and strictly improved negative abstention.
Choose highest correct negative abstention, then recall, precision, then lower
threshold. This is train-only tuning, not independent validation; retain every
failed threshold and do not revise historical guardrails. Enrichment success
and threshold success are separate decisions. Test remains untouched.
