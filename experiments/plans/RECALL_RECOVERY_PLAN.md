# Two recall-recovery experiments, declared before generation

Cleanup, nine-version selection, the tenth slot and test evaluation are paused.
Preserve iteration 21 unchanged. User aspirational train targets: unique
precision@5 around 50%, recall@5 around 70%, correct negative abstention at
least 20/23, and false answerable abstention at most 4/140 (not 4/143).
These are targets, not guaranteed results. Keep the prospective 5% maximum
false abstention as a minimum guardrail, with the stricter 4/140 target shown
separately. Do not change the negative question set or evaluate test.

Train-only error analysis found gold overlap for 18 of iteration 21's 46
false abstentions within top 5, 31 within top 10, and 40 within top 20 of its
unchanged hybrid. These labels were used for diagnosis, never for routing or
selecting passages at inference.

Iteration 22: lower cosine cutoff to 0.50, keep fusion pool 20 per component,
and supply 10 passages to Gemini. Use the new complete-clause evidence prompt,
up to five exact evidence excerpts, summary at most 45 words, and output cap
3,072 tokens. This is a combined pipeline change, not a causal ablation of
each setting. Model/API settings otherwise match iteration 21. All 163 train
queries are covered; upstream rejections avoid calls.

Iteration 23: if iteration 22 produced valid nonempty source evidence, reuse
that answer and its cache. Otherwise lower cutoff to 0.45, retrieve 40
candidates per component and supply the top 20 fused passages to the same
Gemini prompt/settings. The decision to recover uses only upstream model
status and evidence emptiness, never query labels, gold overlap or scores.
This includes invalid-output fallbacks and upstream abstentions. No-answer
recovery is a second inference stage, not a pilot or benchmark subset: final
measurement still covers all 163 train queries.

Strict target success requires all four targets above simultaneously. Also
report improvement over iteration 21: precision at least 95% of its value,
recall gain at least one point, correct negative abstention at least 20/23,
and false abstention at most 5%. Report every component, exact counts and
whether each condition passed; do not relabel a trade-off as target success.

Both versions use request-identity caches. Run 2 reuses successful Run 1
responses without API calls. Pace starts at least five seconds apart, stop
on HTTP/transport errors, preserve failures and never silently regenerate
invalid outputs. Default evaluation and interfaces remain cache-only.
API payloads contain public contract passages and questions, no assignment
PDF, secrets, gold offsets/answers or test records. Log actual usage/versions,
first-use and replay timing, failures, fallback rates and source validation.
