# Full-train local one-shot summary with evidence, declared before measurement

The user explicitly requested no new pilots: use the same full train set as
the earlier baseline/LLM comparisons (140 answerable and 23 negative queries).
This is a new version; no old prompt, model config, or result is overwritten.
The earlier 15-query extraction attempt remains a historical small-cohort
experiment, excluded from the main full-train comparison table.

Phi-3 receives the full query and the same top-five passages from the preserved
local query-expansion BM25 pipeline. The exact prompt is in
prompts/summarise_with_evidence_v1.txt. It contains one declared synthetic
expiry/termination example, not a benchmark question, gold span, or answer.
The required summary is one or two lines and at most 45 words, with supported
answer and necessary qualifiers. Up to three exact quotes provide provenance.

A paraphrased summary is not a retrieval span. Score only validated supporting
quotes with original document/character offsets. Retain the summary for reader
inspection; do not claim it is semantically verified by substring matching.
Validate schema, summary length, new numeric facts, cited IDs, and unique exact
source matches for every quote. A valid empty-evidence no-answer returns no
retrieval. Invalid output falls back to all original candidates and remains in
the denominator. Preserve raw outputs, failures, and fallback counts.

Keep the precision-phase quality policy unchanged: at least one percentage
point precision gain, at most two points recall loss, guarded abstention.
Report existing operational latency separately and include upstream rewrite
and summary generation, not just replay. Candidate pool remains five and
returned evidence can contain fewer than k passages. Record retrieved-character
budgets so a precision gain is not presented without its recall/context cost.

The larger 12,288-token context and 768-token output cap support the new
summary-plus-evidence task; this is not equal-compute to the prior extraction
task. Verify input bounds before generation and record any output truncation.
All inputs are local and train-only; no Gemini, Kanon, FAISS work or held-out
evaluation is performed. Cache every response for offline replay. Evaluate
once all 163 records have a cache entry. Do not reroll invalid generations.

If quality gates fail, stop and reassess rather than expand to Gemini. Semantic
work remains paused until the user reviews the precision result.
