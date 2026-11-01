# Current campaign and finalisation

All modelling stages are complete. The original baseline and 23 experiment
stages (including one historical small pilot) are preserved. Reserved iteration
14, Kanon, was not run. There are 46 full-train model/threshold configurations;
verification replays are not additional approaches.

Ten versions form the presentation sequence under notebooks/presentation/.
Only Run 1 (iteration 22), quota-amended Run 2 (iteration 24), and the original baseline are
selected for held-out evaluation. The API limit reset was confirmed by the
user. Code/config dependencies are frozen in evaluation/execution_freeze.json;
All three held-out evaluations are complete, once each. No test tuning occurred.
Run 2 uses the user-approved Gemini 3.1 recovery amendment with a matching
train counterpart; the original all-3.5 variant remains stage 23.

The report must include every train approach and all three held-out outcomes,
including failures. Run 1 is a provisional recommendation, not a guardrail-
passing winner. Run 2 has higher train precision and recall but poorer correct
negative abstention. Neither met the complete train targets.

The main train improvement campaign remains in log.jsonl and loop_log.jsonl.
From the root, `python manage.py improve --replay` displays its decisions.
`python manage.py improve --demo --steps 5` runs an isolated automatic train-
only campaign without copying test.json or changing main logs/configs. The
main campaign blocks new core proposals after its LLM phase.

Historical plans live in plans/. Each iteration folder indexes its settings,
walkthrough, original logs and raw results. Source snapshots preserve code
before relocation. Personal guides, secrets and the source assignment PDF
remain excluded. Final tasks are held-out reporting, notebook/interface
verification, documentation consistency and private-submission checks.
