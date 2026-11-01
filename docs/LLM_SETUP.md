# Model setup and cache behaviour

Run 1 and Run 2 combine local MiniLM/FAISS retrieval with Gemini 3.5 Flash-Lite.
The baseline is local BM25. Presentation interfaces never call Gemini: exact
known inputs replay saved outputs; missing requests fail explicitly. A hybrid
gate rejection returns nothing without a provider call.

From the root, install requirements-semantic.txt, prepare the public data,
then run `python manage.py prepare_semantic --download`. This fetches pinned
public MiniLM weights and prepares local vectors. Weights are ignored by Git.
The original environment used Python 3.12.4 and torch 2.11.0+cu128 on CPU.
Vector cache identities include library versions, so a different environment
may rebuild vectors. Do not silently regenerate hosted answers to hide a
changed retrieval context.

For explicitly authorised generation, set GEMINI_API_KEY in the environment
or save it in secrets/gemini_api_key.txt. Never paste a key into chat, a
notebook, a config or a commit. Secrets and .env files are ignored. No key is
needed for cached presentation. The API receives only public retrieved text
and the question, not the source assignment PDF or gold answers.

Train generation uses run_recall_recovery --fill. Held-out generation uses
final_test --fill after execution freeze and quota availability. Requests
are paced at least five seconds apart and stop on provider failure. Invalid
outputs remain cached; they are not automatically rerolled. Run 2 reuses
valid first-stage answers and calls Gemini only for its recovery cases.

Phi-3 comparisons remain available. Regeneration requires the pinned Ollama
phi3:mini digest/runtime in llm_configs/. Cached notebook examples need
neither Ollama nor a provider key. The rejected reranker is optional history;
prepare_reranker --download fetches pinned public weights if required.
Kanon was prepared but never run; its files are in experiments/unrun/kanon/.
