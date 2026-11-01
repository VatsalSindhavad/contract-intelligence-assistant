# LLM setup and current status

## Hosted checkpoint complete

Gemini 3.5 Flash-Lite was called through the Gemini API using a locally stored
Google AI Studio key. All 53 unique train-clause outputs are cached and scored
in iteration 9. Cache-only presentations need no API key or network. See
LLM_PRESENTATION.md for the exact CLI/web/notebook walkthrough.

The original key remains in ignored secrets/gemini_api_key.txt or the
GEMINI_API_KEY environment variable. Never paste it into chat, notebooks,
outputs, or commits. Cache files contain inputs, outputs, usage, timings, and
model metadata, not credentials. Contract text and source descriptions were
not sent; only the reviewed clause questions and the fixed prompt were sent.

## Reproduction

Run `python prepare_llm.py --config gemini` to verify cache readiness without
calling a model. Run `python evaluate_llm.py --config gemini` to replay the
train evaluation. Replays are the same proposal, not a new iteration.
`--fill` explicitly authorizes new generation and is unnecessary for the
completed presentation examples. Uncached inputs fail clearly in demo mode.

The first batch hit HTTP 429; successful outputs were retained and the failed
request was retried with pacing. Original failed-attempt history is retained.
All responses passed the fixed output checks. Actual billing depends on the
Google project; reported tokens are not treated as an invoice.

## Local model setup (now evaluated)

The user selected Phi-3 Mini and required hosted-first order. The installed
`phi3:mini` is 3.8B, Q4_0, about 2.2 GB; the machine has about 16 GB RAM.
Exact digest and runtime are recorded in llm_configs/local_phi3.json. Local generation is complete with no new download. The installed digest was
verified before generation. The same prompt, schema and output cap were used.

## Results and remaining work

Gemini improves unique-character train recall@5 from 67.01% to 79.10%, but
estimated first-use p95 of 2.58 seconds fails the unchanged operational latency
guardrail. Cached retrieval p95 is 15.95 ms. The best accepted non-LLM model
stays the default. Neither resolves negative abstention. No test evaluation
has occurred. Final reporting and held-out evaluation remain pending. FAISS and hybrid retrieval remain deferred.

References:
- https://ai.google.dev/gemini-api/docs/api-key
- https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite
- https://docs.ollama.com/api/generate

## Local checkpoint completed

Iteration 10 is complete: 47 valid and 6 explicit fallback outputs cached.
Both models now replay with no network/key/model service. See notebook 11.
