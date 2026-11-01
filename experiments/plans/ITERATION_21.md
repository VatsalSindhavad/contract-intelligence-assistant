# Iteration 21: selected hybrid + Gemini summaries and exact evidence

Use hybrid + 0.55 cutoff together with gemini-3.5-flash-lite through its REST
API. No reranker. Pass only the top five original retrieved passages and the
question to Gemini. Preserve the existing one-shot summary/evidence prompt
unchanged; it contains an invented expiry/notice example, never benchmark
labels. Keep summaries at 45 words/two lines and score exact cited source
quotes, not paraphrased summary words. Up to three evidence quotes. Model
output headroom is 1,536 tokens; actual usage and modelVersion are recorded.

If hybrid returns no passages, abstain without an API call. Invalid output
falls back to original hybrid passages; all failures remain in aggregates.
Exact request identities and full output text/metadata are cached before
continuing; default evaluation and interfaces cannot call the API.

Develop on all 140 answerable and 23 negative train queries. Before measuring:
require precision@5 gain of at least one percentage point, recall loss at most
two points, false answerable abstention at most 5%, and correct negative
abstention no worse than the chosen hybrid. Record quality separately from
first-use p95 latency (flag above max(50 ms, twice reference p95)). Measure
both overlap conventions, hit rate and cache replay. Test remains untouched.

The API receives public CUAD contract passages, including names already in
the corpus, and train questions; it never receives secrets, assignment PDF,
gold answers/offsets or test labels. Local request manifests are in the
excluded personal_notes folder. User explicitly requested this API pipeline.
Rate-limit generation with at least five seconds between request starts.
Stop on HTTP/transport failure, preserving successful and failed attempts;
do not silently retry or replace invalid output. Never claim summary factual
accuracy merely because the supporting quotes are valid source substrings.
