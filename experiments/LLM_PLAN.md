# Hosted versus local LLM retrieval comparison

The next two iteration slots are 9 and 10 under the user-approved limit.
The goal remains retrieval improvement, not answer generation.

Use the selected non-LLM BM25 pipeline as a fixed reference. Give a hosted
model and a small locally executed model the same retrieval-assistance task,
prompt, output schema, candidate budget, and train evaluation. A fair initial
choice is clause-query rewriting with the contract description preserved.
Pick and document actual models/provider before either experiment. The API
route also uses a model; the comparison is hosted versus local deployment,
not "API versus model" as separate algorithm types.

Keep the original question for scoring. Never expose answer labels, offsets,
test questions, or gold source IDs to either model during development. Validate
model output and use an explicit fallback for invalid output or model failure;
record these events rather than silently discarding questions.

Before any model calls, implement a cache keyed by exact model identifier,
prompt/version, input text, and generation settings. Save validated outputs,
raw responses, usage, timings, and local runtime/model version. Evaluation must
support cache-only replay and fail clearly on a missing cache entry. Never
log credentials; obtain hosted keys from environment variables and retain the
original assignment PDF outside Git.

Report the same character metrics and abstention guardrails plus model-call
latency, complete retrieval latency, cache-replay latency, hosted cost/usage,
and local compute/hardware assumptions. A cached local/hosted replay is not a
fair measure of first-run inference speed. Discuss text transfer/privacy and
local setup costs. Keep both experiments even if one or both are rejected.

The CLI and web app are implemented and verified; the user can check the demo
before model integration. Do not call the project complete until final config
freeze, held-out evaluation, actual test-run counts, final failure analysis,
REPORT.md, and clean-environment reproduction checks are complete. FAISS,
hybrid retrieval, and other deferred extensions are not part of this checkpoint.

## Selected setup

Hosted first: Gemini through Google AI Studio's API key, with the proposed
model/config in `llm_configs/gemini.json`. Confirm actual account access with
one request before filling the train cache. Local second: installed Phi-3 Mini
via Ollama, with exact inspected digest in `llm_configs/local_phi3.json`.
The shared cache/schema/fallback infrastructure is implemented and tested.
There are 53 unique clause questions among the 163 train records, allowing
reuse without repeat model calls. No provider or local generation has occurred.
