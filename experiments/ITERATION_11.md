# Pure dense baseline declared before iteration 11

Use the locally available all-MiniLM-L6-v2 model at the pinned revision in
semantic_configs/minilm.json. It is an Apache-2.0 general-purpose, 384-dimensional
sentence/paragraph embedder, not a legal-specialist model. Use CPU with four
PyTorch threads for this initial reproducible setup. No download is currently
needed; runtime loading is explicitly local-only.

Encode the original full question, search all indexed chunks with normalized
vectors and exact FAISS IndexFlatIP, and return the same original passage text
and offsets. No BM25 candidate generation/routing/fusion, LLM, or gold IDs are
used. Preserve the 1,000-character/200-overlap chunks and k=1,3,5,10.

The model's published default limit is 256 wordpieces. Keep that default for
this basic baseline, count/report document and query inputs exceeding it,
and disclose truncation as a limitation. Do not silently change chunking or
raise the sequence length after seeing metrics. Source passage offsets still
refer to the original full chunks, even if their encoded input is truncated.

Cache vectors with model/config/library identities, ordered text hashes and
checksums. Record index building separately from query encoding/search; replay
latency cannot replace first-use encoding latency in the operational decision.
Keep the same numeric objective/guardrails and compare against the original
BM25 baseline plus the selected stemmed BM25 reference. This is a baseline for
a new retrieval family, not a guaranteed accepted replacement.

Score only 140 answerable and 23 negative train questions. Test remains closed.
Document no-match behavior and the untuned positive cosine threshold. The
semantic phase has three planned trials (11–13); Kanon access and any external
embedding payload approval are separate later work.

Reference: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
