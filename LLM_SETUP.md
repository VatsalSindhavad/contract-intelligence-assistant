# Gemini first, Phi-3 Mini second

The hosted experiment will use a Gemini API key created in Google AI Studio.
The model identifier is configured in `llm_configs/gemini.json`. Current model
availability was checked against Google's model documentation; access and quota
still depend on the account. One approved connection-check request has succeeded; no retrieval evaluation has been performed.

## Set the key locally

1. Open https://aistudio.google.com/apikey and create a Gemini API key.
2. Open `secrets/gemini_api_key.txt` locally and paste only the key, then save.
3. Tell Codex that the key file is ready. Do not paste the key into chat.

The key file is deliberately ignored by Git. Alternatively, set
`GEMINI_API_KEY` in the terminal executing the commands. Keys are read only for
live API calls; caches store prompts, outputs, usage, and timings without keys.
Never paste credentials into notebooks or commit them.

## First check: one request only

```powershell
python prepare_llm.py --config gemini
python prepare_llm.py --config gemini --fill --max-new 1
```

The first command inspects the cache without calling a model. The second makes
at most one new request, caches it, and validates its output. It is a connection
and schema check, not a scored improvement iteration. If access/quota fails,
stop and inspect only the sanitized error status; do not print request headers.
Provider errors are cached explicitly and must be reviewed before the full run.

Both models will receive the same clause question and prompt, with the same
24-word output limit and 256-token generation cap. Document descriptions and
contract contents are not sent to Gemini. Original query text still determines
document routing; generated terms only supplement clause ranking. Invalid model
output falls back to the original BM25 query. Full evaluation will use cached
outputs and must never silently call a model on cache misses.

## Local model, later

`phi3:mini` is already installed in Ollama: 3.8B parameters, Q4_0 quantization,
approximately 2.2 GB model file. The inspected machine has about 16 GB RAM.
The exact installed model digest/runtime is recorded in
`llm_configs/local_phi3.json`. No download or local generation has been started.
The preparation command currently refuses local generation to preserve the
requested hosted-first sequence. Enable it only after the hosted checkpoint.

## What is not complete yet

Credential/access verification passed for one approved question. The remaining
52 question requests, full cache population, and scored iteration 9 are pending. Iteration 10 follows with Phi-3. The existing numerical acceptance
rules remain unchanged. Report model-generation latency separately from cache
replay and retrieval; never treat replay speed as first-run inference speed.
Final held-out evaluation, cost/privacy analysis, report, and reproduction
checks remain required. FAISS and hybrid retrieval remain deferred.

References:

- https://ai.google.dev/gemini-api/docs/api-key
- https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite
- https://docs.ollama.com/api/generate
