# Iteration 14: Kanon 2 + FAISS

Declared before API generation or scoring. Compare legal embeddings against iteration 11 MiniLM using the same 1,000-character chunks, 200-character overlap, full queries, cosine similarity through normalized IndexFlatIP, and top-k values 1/3/5/10. No routing, hybrid, reranker, chunking changes, or LLM.

Use all 140 answerable and 23 negative train questions. Test remains untouched. Report both unique-character and benchmark pairwise precision/recall, abstention, and API preparation versus cached search timing separately. Select no winner from precision alone; examine recall and abstention too.

Explicit `--fill` permits missing embedding requests. Default evaluation is cache-only and fails if any cache is missing. Documents use `retrieval/document`; questions use `retrieval/query`. Refuse overflow instead of silently truncating. Cache exact requests and validated responses with checksums; never record credentials. The provider model alias is mutable, so preserve responses for reproducibility.

Run: `python evaluate_kanon.py --fill` once after saving the Isaacus key; `python evaluate_kanon.py` replays without an API key. Contract chunks and train questions are transmitted to Isaacus. No gold spans or answers are sent.
