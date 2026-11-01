# Local comparison declared before iteration 10

Use the installed Phi-3 Mini (3.8B, Q4_0) through local Ollama. The verified
model digest and runtime are pinned in llm_configs/local_phi3.json. No download
or hosted API is needed. The same 53 unique train clause questions, prompt,
schema, temperature 0, 256-token output cap, validation, original-clause
retention and stemmed BM25 reference are used as in Gemini iteration 9.
Local seed is 42 and context length is 2,048 tokens; provider implementations
can differ, so this is a controlled application comparison, not equal compute.

Cache the first local result to verify the runner, then fill missing responses
without changing the prompt or settings based on quality. Invalid output falls
back explicitly and remains in the evaluation denominator. Cache-only replay
must make no local or hosted model calls. Test data stays untouched.

The existing numeric objective and guardrails remain unchanged. Compare with
the fixed non-LLM reference and report Gemini side by side. Apply the latency
guardrail to estimated first-use latency, retaining a separate replay-mode
decision. Local inference has no hosted model fee but uses machine resources;
do not call it cost-free. Include the inspected 16-GB memory context, pinned
quantization/runtime, and saved generation durations in limitations.

This is the tenth distinct proposal, satisfying the user's maximum. Do not
start further improvement proposals without a revised scope. Subsequent work
is verification, reporting, final configuration freeze, and final evaluation.
