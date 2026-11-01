# Precision-focused local extraction pilot, declared before measurement

Semantic development is paused at trial 11. The user now authorizes further
evidence-driven BM25 experiments, with all failures retained and a later
selection of ten representative versions. Old total-trial caps are superseded.
Kanon and dense+Gemini have not been run and are not assigned completed IDs.

Trial 12 is a small local pilot, not a full 163-query evaluation. Select ten
answerable and five negative train records by ascending stripped-query SHA-256.
No outcome-based example selection or held-out data is used. Retain query IDs.

Use the preserved local Phi-3 query-expansion BM25 pipeline from trial 10 to
retrieve the same fixed top-five candidates. Add Phi-3 exact-excerpt extraction
with the user's “nothing more, nothing less, one line” instruction. The exact
instruction-only prompt is in prompts/extract_answer_v1.txt; no example is used.
Send only the query and retrieved passages to localhost. Never supply gold
answers, annotations, labels, or expert offsets to the model.

The model returns one-line JSON identifying one passage and an exact quote.
Validate the schema and require a unique exact substring in the cited passage.
Compute source offsets from that substring. Hallucinated/paraphrased/ambiguous
output is invalid and falls back to the original ranked candidates; a valid
explicit no-answer response returns nothing. Preserve raw outputs, failures,
and all questions. Do not score a paraphrased answer as retrieved characters.

The 8,192-token context is deliberately larger than the earlier question-only
rewrite context. Verify a conservative UTF-8 byte/token bound before calls;
reject oversized inputs rather than silently truncate passages. Keep the same
model digest, temperature, seed, and 256-token output cap. This is a different
task, not an equal-compute comparison with query expansion.

Declare the new precision objective before measurement: gain at least one
percentage point of unique-character precision@5, lose no more than two points
of recall, increase answerable false abstention by at most two points, and do
not reduce correct negative abstention. Report model-generation/first-use and
cached replay latency separately. The earlier operational latency ceiling is
retained as a separate operational gate. Small pilot counts make these gates
coarse and provisional; do not claim statistical significance.

If the pilot fails to improve precision with preserved coverage/abstention,
stop and reassess with the user. Do not continue to Gemini or semantic work.
If it passes, a full train comparison is still required before adoption or
claiming a general gain. Cache outputs for offline presentation and replay.
