# Iteration plan and current status

The user has now authorized a separate semantic phase after the completed
BM25 study. The current plan is: trial 11 local dense baseline,
12 Kanon dense baseline, and 13 selected dense retrieval with Gemini. The
global limit is now 13. The ten-trial limit below describes the earlier phase;
its historical results and decisions remain unchanged. Hybrid is deferred
until the complete submission-ready checkpoint.

The baseline is separate. The user allows at most ten total improvement
iterations and requested two accepted non-LLM improvements before LLM trials.

| Iteration | Change | Outcome |
|---|---|---|
| 1 | Corpus/query common-word filtering | Rejected |
| 2 | Smaller chunks | Rejected |
| 3 | Lower length normalization | Rejected: gain below minimum |
| 4 | Lower term saturation | Rejected |
| 5 | Document identification then clause ranking | Accepted |
| 6 | Focused clause tokens | Rejected: false abstention |
| 7 | Focused tokens with zero-match fallback | Accepted |
| 8 | Combined accepted pipeline plus English stemming | Accepted |
| 9 | Gemini query expansion + best BM25 | Retrieval gain; fails first-use latency |
| 10 | Local Phi-3 query expansion + best BM25 | Retrieval gain; fails first-use latency |

The two requested improvements and one further combined improvement are complete. No iteration slots
remain, including possible LLM work. Choose the next proposal from evidence,
not to fill a table; never loosen rules after observing a result. Replays do
not count as distinct iterations. Minimum core iteration count is satisfied.

Before optional LLM or hybrid/reranker work, finish the working core interfaces
and report. All train development remains separate from test; freeze final
comparison configurations before final test reporting. Current answerability
is still weak and must not be hidden by improved retrieval scores.

FAISS dense retrieval is permitted as a retrieval implementation. It needs an
embedding model; the index alone does not create semantic representations.
Compare dense retrieval alone before claiming a hybrid benefit. Hybrid with
a reranker remains a stretch feature and is not implemented. A future trial
must justify added dependencies, compute, privacy implications, and latency.

Before LLM trials, select and justify model/provider, read keys from environment
variables, cache request-keyed outputs, support cache-only evaluation, and log
cost/latency/settings. Preserve every rejected and accepted configuration.

All ten trials are complete. Next steps are result review, final configuration
freeze, held-out evaluation and reporting, not new proposal generation.
