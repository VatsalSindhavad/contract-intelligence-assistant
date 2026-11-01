# Hosted query expansion declared before iteration 9 scoring

Gemini receives only the reviewed train clause questions (preserved in cache request records) and the
fixed shared prompt. Generated terms supplement the original clause query;
original full-query document routing remains unchanged. Numeric facts, output
schema, and length are validated; invalid output uses the original query.

Compare with the selected stemmed BM25 model from iteration 8, and also report
the original baseline. Score 140 answerable and 23 negative train questions.
All 53 unique clause-question responses must be present before evaluation;
cache-only misses fail rather than silently call a model. No test data is used.

Keep the existing numerical objective/guardrails. Report both cache-replay
latency and estimated first-use latency (saved generation time plus measured
replay/retrieval time per question). Apply the operational latency guardrail to
the first-use estimate, not only the fast replay path. Also record a separate
replay-mode decision. A quality gain does not override a failed latency rule.
First-use latency is an estimate from separately timed components, not a direct
load test. Cache fill uses 53 calls rather than one call for each repeated type.

Persist token usage and provider modelVersion. Actual billing depends on the
account; do not claim zero cost or infer an invoice from token counts alone.
Do not change prompt/settings after seeing the result and call it the same
iteration. Phi-3 remains deferred until the hosted checkpoint completes.
