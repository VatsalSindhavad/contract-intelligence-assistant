# Evaluation report

## Summary and recommendation

This project searches the prescribed CUAD contract subset and returns source
passages with character offsets. The study progressed from lexical BM25 to
query expansion, source-grounded summaries, semantic retrieval, indexing
changes, hybrid retrieval and conditional recovery. Every attempt is retained,
including failures. The final held-out comparison is limited to the original
baseline and two candidates selected using train data.

Run 1 is the provisional recommendation because it rejects more unanswerable
train questions and is simpler than Run 2. Run 2 improves train precision,
recall and false answerable abstention. Neither satisfies the complete train
guardrails; this is a measured prototype, not a production-ready legal system.
The held-out comparison is complete: Run 1 achieved 58.14% precision and
56.94% recall at k=5, rejecting 5/7 negatives and falsely rejecting 4/54
answerable questions. Quota-amended Run 2 achieved 65.87%/62.99%, rejected
2/7 negatives and falsely rejected 0/54. The baseline achieved 0.80%/13.87%.
Each configuration was evaluated once; no tuning followed these outcomes.

## Data and evaluation setup

The prescribed mini selection yields 194 answerable CUAD questions over 29
contracts. All 272 supplied answer spans were verified against Python UTF-8
text slices before indexing. The deterministic question hash split produces
140 train and 54 test answerable questions. Thirty authored unanswerable
questions split into 23 train and seven test negatives. They were committed
before improvements in commit 52fc955 and remain byte-identical to the frozen
question/corpus manifest. The corpus includes contracts referenced by both
splits, as required; labels never enter inference.

Negative labels are supported by corpus-wide literal checks, document
inspection and the historical time boundary. Absence searches are not a
semantic proof; these authored negatives need broader human/legal review.
Development and configuration selection use train only. Test questions are
used only after selection and execution freeze. Only baseline, Run 1 and
Run 2 receive final test evaluation; the other approaches remain train-only.
A test ledger records complete and interrupted attempts per configuration.

### Metrics and sample sizes

Precision and recall are measured at k=1, 3, 5 and 10; k=5 is the declared main
comparison. Each result is a macro-average across all answerable questions,
including zero scores when the system abstains. Every character is identified
by its original document and position; output offsets are checked again.

- Unique-character precision = retrieved/gold intersecting characters divided
  by unique retrieved characters. Recall uses unique gold characters as the
  denominator. Overlapping source intervals are merged first.
- Benchmark pairwise precision/recall sum overlaps for retrieved/gold pairs
  and divide by passage/gold lengths. Overlapping retrieved passages can count
  the same gold characters more than once, so pairwise recall may exceed 100%.
  We retain this convention separately rather than clipping or relabelling it.
- Correct abstention = negatives returning no passages divided by all negatives.
  False abstention = answerable questions returning no passages divided by all
  answerable questions. Both rates and exact counts are reported.
- Hit rate records any gold character overlap. Median/p95 latency distinguishes
  cached replay from first-use inference; startup, downloads and quota pacing
  are stated separately. API tokens/calls are observed usage, not an invoice.

Train denominators are 140 and 23; test denominators are 54 and seven. A single
negative test question changes correct abstention by 14.29 percentage points,
so those results need cautious interpretation. Generated summary words are
not scored as retrieved evidence. Exact quote validity does not establish
semantic summary correctness. See [metric definitions](evaluation/metrics.md)
and the saved per-query scores for both conventions.

## System design

The baseline indexes 1,000-character windows with 200-character overlap using
BM25. Lexical improvements infer a contract using the full question, then
rank within it using clause-focused terms. Fallback prevents empty results
when cleaned terms have no matches; Snowball stemming normalises inflections.
Gemini and local Phi-3 query expansion were compared on that same base.

Pure semantic retrieval uses pinned all-MiniLM-L6-v2 vectors, L2 normalisation
and exact FAISS IndexFlatIP search. FAISS is the index, not the embedding
model. Clause-boundary chunking and same-contract definition/reference context
were measured separately. Neither beat the original dense reference overall.
The selected hybrid combines twenty candidates per component through weighted
reciprocal-rank fusion: lexical weight 0.75, dense weight 0.25, rank constant
60. Exact duplicate source intervals merge. These weights were declared before
measurement because lexical retrieval was stronger. RRF scores are not
probabilities. The rejected local cross-encoder reranker remains documented.

### Final candidate 1: broader single-stage evidence

Run 1 applies a 0.50 cutoff to the best dense cosine score, retrieves the top
ten fused passages, and sends only their text plus the question to Gemini
3.5 Flash-Lite. The prompt asks for a one/two-line summary and up to five exact
complete answering clauses, preserving necessary conditions, exceptions and
negation. A synthetic expiry/termination example is included; benchmark answers
are not examples. Partial support can be returned with missing parts stated.
If no supplied text supports the question, the model must explicitly abstain.

Quotes are mapped back to original document offsets. Valid evidence is scored;
summary prose is displayed separately. Invalid source/schema output falls back
to the original retrieved passages and remains in aggregates. A gate rejection
avoids the API. Missing presentation caches produce an error, never a silent
provider call. The full prompt and settings are versioned.

### Final candidate 2: conditional recovery

Run 2 first runs the exact Run 1 policy. A valid nonempty evidence response is
reused. No-answer, upstream rejection or invalid output triggers a second
attempt: cutoff 0.45, forty candidates per retriever and twenty fused passages
for the same Gemini model and prompt. This is a two-stage policy, not an
independent model applied uniformly at 0.45. The routing decision sees only
output status/evidence presence, never labels or gold scores. Every question,
including reused answers and failures, enters the final aggregate.

### Why these implementation choices

Direct Python, FAISS and REST calls keep data flow and cache behaviour visible
for modification and review. LangChain is permitted but not required for
these operations; adding orchestration alone is not evidence of retrieval
improvement. Models are pretrained, with no fine-tuning on this dataset.
Local Phi-3 and the reranker were measured alternatives, not silently removed.
Kanon was prepared but never run after the API requirement was excluded.

## Objectives and self-improvement loop

The initial train objective prioritised recall@5 gains of at least one point,
precision at least 95% of the current reference and protected abstention and
latency. Later precision experiments declared a one-point precision gain and
at most two points of recall loss before measurement. The user subsequently
set a prospective 5% false-abstention ceiling; historical decisions were not
rewritten to fit the new limit. The last two runs declared aspirational
50% precision, 70% recall, at least 20/23 correct negative abstentions and at
most 4/140 false abstentions. Not all targets were achieved.

The automatic loop evaluates train, groups failures, chooses an untried
matching proposal from a rule catalogue, evaluates it, applies the objective
and records accept/reject plus selected configuration. Original logs include
more than five improvement iterations beyond baseline. A single-command
five-step isolated demonstration was verified after reorganisation: three
accepted changes followed by two rejections. It copied no test file and did
not change the main campaign. Its scratch iteration IDs are not new project
approaches. The main campaign blocks new core proposals after entering the
LLM phase; replay displays historical decisions without new tuning.

Command: `python manage.py improve --demo --steps 5`. Original decisions:
`python manage.py improve --replay`. The complete configs, objectives, diagnoses,
outputs and decisions remain in the [experiment index](experiments/README.md).

## Train results: ten presentation versions

All rows below use 140 answerable and 23 negative train questions at k=5. These ten illustrate the progression; only baseline and the last two candidates are evaluated on test.

| Version | Precision | Recall | Benchmark precision | Benchmark recall | Correct abstention | False abstention |
|---|---:|---:|---:|---:|---:|---:|
| Original BM25 baseline | 1.74% | 18.16% | 1.76% | 19.24% | 0/23 (0.00%) | 0/140 (0.00%) |
| Improved BM25 with stemming | 7.88% | 67.01% | 8.38% | 76.60% | 0/23 (0.00%) | 0/140 (0.00%) |
| BM25 + Gemini query expansion | 8.47% | 79.10% | 8.93% | 89.58% | 0/23 (0.00%) | 0/140 (0.00%) |
| BM25 + Phi-3 query expansion | 8.07% | 70.75% | 8.51% | 80.07% | 0/23 (0.00%) | 0/140 (0.00%) |
| BM25 + Phi-3 summary and evidence | 20.08% | 68.92% | 20.44% | 75.64% | 7/23 (30.43%) | 3/140 (2.14%) |
| MiniLM + FAISS with 0.55 cutoff | 4.03% | 35.75% | 4.19% | 38.90% | 9/23 (39.13%) | 1/140 (0.71%) |
| Hybrid with 0.55 cutoff | 7.12% | 65.51% | 7.49% | 74.24% | 9/23 (39.13%) | 1/140 (0.71%) |
| Hybrid + 0.55 cutoff + Gemini | 54.15% | 46.93% | 54.19% | 48.87% | 23/23 (100.00%) | 46/140 (32.86%) |
| Run 1: ten-passage Gemini at 0.50 | 65.70% | 61.38% | 65.69% | 62.79% | 17/23 (73.91%) | 17/140 (12.14%) |
| Run 2: Gemini 3.1 quota-amended recovery | 73.02% | 65.59% | 73.04% | 67.19% | 0/23 (0.00%) | 0/140 (0.00%) |

### Detailed baseline / Run 1 / quota-amended Run 2 comparison

| Pipeline | Provider / context | Precision@5 | Recall@5 | Correct abstention | False abstention | Train hit rate |
|---|---|---:|---:|---:|---:|---:|
| Original BM25 baseline | Local BM25; fixed windows | 1.74% | 18.16% | 0/23 | 0/140 | 26.43% |
| Run 1: ten-passage Gemini at 0.50 | Gemini 3.5; cutoff 0.50; ten passages | 65.70% | 61.38% | 17/23 | 17/140 | 80.00% |
| Run 2: conditional recovery with Gemini 3.1 | Gemini 3.5 first stage; 3.1 recovery; cutoff 0.45; twenty passages | 73.02% | 65.59% | 0/23 | 0/140 | 86.43% |

The original all-3.5 Run 2 remains separately documented in stage 23. The final mixed-provider variant is stage 24, declared for quota reasons before test scoring. Its improved false-abstention rate must not hide the failure to reject any train negative questions. Run 1 remains the provisional business recommendation; neither final candidate passes every train criterion.

| Pipeline | k | Precision | Recall | Benchmark precision | Benchmark recall |
|---|---:|---:|---:|---:|---:|
| Original BM25 baseline | 1 | 0.56% | 1.72% | 0.56% | 1.72% |
| Original BM25 baseline | 3 | 1.36% | 7.43% | 1.45% | 8.50% |
| Original BM25 baseline | 5 | 1.74% | 18.16% | 1.76% | 19.24% |
| Original BM25 baseline | 10 | 1.81% | 32.16% | 1.87% | 35.52% |
| Run 1: ten-passage Gemini at 0.50 | 1 | 65.99% | 47.48% | 65.99% | 47.48% |
| Run 1: ten-passage Gemini at 0.50 | 3 | 65.76% | 58.64% | 65.75% | 59.86% |
| Run 1: ten-passage Gemini at 0.50 | 5 | 65.70% | 61.38% | 65.69% | 62.79% |
| Run 1: ten-passage Gemini at 0.50 | 10 | 65.62% | 65.21% | 65.64% | 67.19% |
| Run 2: conditional recovery with Gemini 3.1 | 1 | 73.11% | 51.99% | 73.11% | 51.99% |
| Run 2: conditional recovery with Gemini 3.1 | 3 | 72.98% | 63.59% | 73.03% | 65.02% |
| Run 2: conditional recovery with Gemini 3.1 | 5 | 73.02% | 65.59% | 73.04% | 67.19% |
| Run 2: conditional recovery with Gemini 3.1 | 10 | 72.92% | 67.70% | 72.96% | 70.24% |

Valid Gemini responses contain at most five quotes, often fewer. Some recall gain at k=10 comes from invalid-output fallbacks returning additional original passages.

### Operational comparison

| Pipeline | New train API requests | Input / output tokens | First-use p50 / p95 ms | Cache p50 / p95 ms |
|---|---:|---|---|---|
| Run 1 | 160 | 440,022 / 20,394 | 2281.18 / 4463.85 | 12.37 / 16.30 |
| Run 2, incremental calls | 58 | 292,876 / 5,002 | 2621.53 / 6037.28 | 13.03 / 29.12 |

Run 2 first-use timing includes the first stage; incremental token/call totals count only its extra requests. Run 1 used 160 calls with 24 invalid fallbacks and three upstream rejections. Run 2 reused 105 valid answers and made 58 additional calls; it ended with 21 invalid fallbacks. All six train negative false returns in Run 1 and all ten in Run 2 came from invalid-output passage fallbacks. Most remaining output failures involve empty evidence with a noncanonical no-answer sentence. Changing that fallback would be a new policy, not a retroactive repair of these figures. Demo-only requests are excluded from evaluation/usage totals.

## Final held-out results

| Configuration | Precision@5 | Recall@5 | Correct abstention | False abstention | Test attempts |
|---|---:|---:|---:|---:|---:|
| Run 1: Gemini 3.5 | 58.14% | 56.94% | 5/7 (71.43%) | 4/54 (7.41%) | 1 |
| Run 2: 3.5 first stage + 3.1 recovery | 65.87% | 62.99% | 2/7 (28.57%) | 0/54 (0.00%) | 1 |
| Original BM25 baseline | 0.80% | 13.87% | 0/7 (0.00%) | 0/54 (0.00%) | 1 |

Run 2 here is the explicitly amended Gemini 3.1 recovery policy, not the original all-3.5 version. All three cover the same 54 answerable and seven negative questions.

<details>
<summary>All k values, benchmark scores, hit rates and cached latency</summary>


<!-- FINAL_TEST_RESULTS_START -->

Only the frozen baseline and two train-selected candidates were evaluated. No test tuning.

| Model | k | Queries | Precision | Recall | Benchmark precision | Benchmark recall | Hit rate | Correct abstention | False abstention | Cached p50/p95 ms | Test attempts |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| broad10 | 1 | 54 | 53.56% | 45.16% | 53.56% | 45.16% | 59.26% | 5/7 | 4/54 | 13.03/16.57 | 1 |
| broad10 | 3 | 54 | 58.10% | 54.53% | 58.23% | 56.21% | 72.22% | 5/7 | 4/54 | 13.03/16.57 | 1 |
| broad10 | 5 | 54 | 58.14% | 56.94% | 58.21% | 58.61% | 74.07% | 5/7 | 4/54 | 13.03/16.57 | 1 |
| broad10 | 10 | 54 | 58.00% | 58.79% | 58.05% | 61.16% | 75.93% | 5/7 | 4/54 | 13.03/16.57 | 1 |
| recovery20 | 1 | 54 | 61.63% | 51.31% | 61.63% | 51.31% | 66.67% | 2/7 | 0/54 | 13.58/28.28 | 1 |
| recovery20 | 3 | 54 | 65.77% | 60.59% | 65.76% | 61.38% | 77.78% | 2/7 | 0/54 | 13.58/28.28 | 1 |
| recovery20 | 5 | 54 | 65.87% | 62.99% | 65.86% | 63.78% | 79.63% | 2/7 | 0/54 | 13.58/28.28 | 1 |
| recovery20 | 10 | 54 | 65.75% | 65.15% | 65.76% | 66.63% | 83.33% | 2/7 | 0/54 | 13.58/28.28 | 1 |
| baseline | 1 | 54 | 0.31% | 1.85% | 0.31% | 1.85% | 1.85% | 0/7 | 0/54 | 6.53/8.17 | 1 |
| baseline | 3 | 54 | 0.80% | 8.07% | 0.76% | 8.07% | 11.11% | 0/7 | 0/54 | 6.53/8.17 | 1 |
| baseline | 5 | 54 | 0.80% | 13.87% | 0.76% | 13.87% | 18.52% | 0/7 | 0/54 | 6.53/8.17 | 1 |
| baseline | 10 | 54 | 1.74% | 27.94% | 1.79% | 30.39% | 40.74% | 0/7 | 0/54 | 6.53/8.17 | 1 |

<!-- FINAL_TEST_RESULTS_END -->

</details>

The matched train/test comparison is in [FINAL_COMPARISON.md](evaluation/FINAL_COMPARISON.md). Run 1 lost 7.55 precision points and 4.44 recall points from train; the amended Run 2 lost 7.15 and 2.60 points respectively. Run 1 still exceeds the 5% false-abstention guardrail. Run 2 rejects fewer negatives. The small seven-question negative test set limits confidence in either rate. No model settings were changed after these scores. One HTTP 503 during response preparation was preserved and retried; it did not produce an additional evaluation attempt.

## Every approach and what it changed

| Stage | Approach | What we learned |
|---|---|---|
| 00 | Original baseline | Simple lexical starting point; weak recall. |
| 01 | Stopword removal | Did not improve the declared objective. |
| 02 | Smaller chunks | Shorter windows did not yield an accepted improvement. |
| 03 | BM25 length normalisation b=0.30 | Small gain below the predeclared minimum. |
| 04 | BM25 saturation k1=0.80 | Rejected against the reference. |
| 05 | Document then clause routing | Accepted: party names no longer dominated clause ranking. |
| 06 | Focused clause cleanup | Recall improved but false abstention failed its guardrail. |
| 07 | Cleanup with zero-match fallback | Accepted: recovered matches lost to filtering. |
| 08 | Combined improvements plus stemming | Accepted lexical reference. |
| 09 | Gemini query expansion | Highest train recall, with latency and abstention limitations. |
| 10 | Local Phi-3 query expansion | A reproducible local-versus-hosted comparison. |
| 11 | Pure MiniLM + FAISS | Basic semantic retrieval lost to tuned lexical retrieval. |
| 12 | Exact-answer Phi-3 pilot | Small subset only; precision gain came with unacceptable recall loss. |
| 13 | Full-train Phi-3 summary/evidence | Precision improved; output failures required many fallbacks. |
| 14 | Kanon preparation | Not run; no metric or improvement is claimed. |
| 15 | Clause-aware MiniLM chunks | Slight precision improvement but substantial recall loss. |
| 16 | Clause-aware cutoff sweep | Higher rejection rates also rejected answerable questions. |
| 17 | Definitions/cross-reference enrichment | No overall retrieval gain; threshold effects required a control. |
| 18 | Original dense cutoff control | Matched enrichment abstention without its retrieval loss. |
| 19 | BM25/dense hybrid and cutoff sweep | Did not beat tuned BM25; 0.55 became the user-selected reference. |
| 20 | Hybrid + local reranker | Worse precision and recall; excluded from the final pipeline. |
| 21 | Hybrid + five-passage Gemini evidence | Strong precision, but 46/140 false abstentions. |
| 22 | Run 1: ten passages and complete clauses | Better overlap and fewer false abstentions; incomplete target attainment. |
| 23 | Original Run 2: all-3.5 conditional recovery | Further overlap improvement; negative abstention degraded. |
| 24 | Quota-amended Run 2: 3.1 recovery | Matched train counterpart; negative abstention failed badly due to invalid-output fallback. |

The complete table below includes each measured threshold variant. There are 46 full-train configurations, not 45 independent model families. Repeated verification runs are not new approaches. The historical pilot is isolated because it used ten answerable and five negative questions. Configurations, raw outputs and decisions are linked from experiments/iterations/.

### All full-train model and threshold outputs

| Stage | Configuration | Precision@5 | Recall@5 | Correct abstention | False abstention |
|---|---|---:|---:|---:|---:|
| 00 | Original BM25 baseline | 1.74% | 18.16% | 0/23 | 0/140 |
| 01 | BM25 + stopword removal | 1.61% | 15.89% | 0/23 | 0/140 |
| 02 | BM25 + 500-character chunks | 0.78% | 4.09% | 0/23 | 0/140 |
| 03 | BM25 with b=0.30 | 1.79% | 18.82% | 0/23 | 0/140 |
| 04 | BM25 with k1=0.80 | 1.57% | 16.16% | 0/23 | 0/140 |
| 05 | BM25 + document/clause routing | 5.15% | 47.12% | 0/23 | 0/140 |
| 06 | BM25 + focused clause query | 5.81% | 50.72% | 1/23 | 12/140 |
| 07 | BM25 + focused clause query + fallback | 6.28% | 53.50% | 0/23 | 0/140 |
| 08 | BM25 + focused query, fallback and stemming | 7.88% | 67.01% | 0/23 | 0/140 |
| 09 | BM25 + Gemini query expansion | 8.47% | 79.10% | 0/23 | 0/140 |
| 10 | BM25 + Phi-3 query expansion | 8.07% | 70.75% | 0/23 | 0/140 |
| 13 | BM25/Phi-3 + one-shot summary and evidence | 20.08% | 68.92% | 7/23 | 3/140 |
| 11 | MiniLM + FAISS, fixed windows | 4.03% | 35.75% | 0/23 | 0/140 |
| 15 | Clause-aware MiniLM + FAISS | 5.12% | 19.74% | 0/23 | 0/140 |
| 17 | Definition/reference-enriched MiniLM + FAISS | 3.87% | 35.70% | 0/23 | 0/140 |
| 16 | Clause-aware MiniLM + cutoff 0.20 | 5.12% | 19.74% | 0/23 | 0/140 |
| 16 | Clause-aware MiniLM + cutoff 0.30 | 5.12% | 19.74% | 0/23 | 0/140 |
| 16 | Clause-aware MiniLM + cutoff 0.40 | 5.12% | 19.74% | 0/23 | 0/140 |
| 16 | Clause-aware MiniLM + cutoff 0.50 | 5.12% | 19.74% | 1/23 | 0/140 |
| 16 | Clause-aware MiniLM + cutoff 0.60 | 4.91% | 19.02% | 14/23 | 10/140 |
| 16 | Clause-aware MiniLM + cutoff 0.70 | 1.91% | 7.12% | 22/23 | 84/140 |
| 16 | Clause-aware MiniLM + cutoff 0.80 | 0.00% | 0.00% | 22/23 | 140/140 |
| 17 | Enriched MiniLM + cutoff 0.40 | 3.87% | 35.70% | 0/23 | 0/140 |
| 17 | Enriched MiniLM + cutoff 0.45 | 3.87% | 35.70% | 0/23 | 0/140 |
| 17 | Enriched MiniLM + cutoff 0.50 | 3.87% | 35.70% | 3/23 | 0/140 |
| 17 | Enriched MiniLM + cutoff 0.55 | 3.87% | 35.70% | 9/23 | 1/140 |
| 17 | Enriched MiniLM + cutoff 0.60 | 3.64% | 33.14% | 15/23 | 11/140 |
| 17 | Enriched MiniLM + cutoff 0.65 | 2.57% | 22.91% | 20/23 | 52/140 |
| 18 | Original MiniLM + cutoff 0.40 | 4.03% | 35.75% | 0/23 | 0/140 |
| 18 | Original MiniLM + cutoff 0.45 | 4.03% | 35.75% | 0/23 | 0/140 |
| 18 | Original MiniLM + cutoff 0.50 | 4.03% | 35.75% | 3/23 | 0/140 |
| 18 | Original MiniLM + cutoff 0.55 | 4.03% | 35.75% | 9/23 | 1/140 |
| 18 | Original MiniLM + cutoff 0.60 | 3.82% | 33.90% | 16/23 | 11/140 |
| 18 | Original MiniLM + cutoff 0.65 | 2.68% | 23.68% | 20/23 | 52/140 |
| 19 | BM25 + MiniLM hybrid, ungated | 7.14% | 66.23% | 0/23 | 0/140 |
| 19 | Hybrid + cutoff 0.40 | 7.14% | 66.23% | 0/23 | 0/140 |
| 19 | Hybrid + cutoff 0.45 | 7.14% | 66.23% | 0/23 | 0/140 |
| 19 | Hybrid + cutoff 0.50 | 7.14% | 66.23% | 3/23 | 0/140 |
| 19 | Hybrid + cutoff 0.55 | 7.12% | 65.51% | 9/23 | 1/140 |
| 19 | Hybrid + cutoff 0.60 | 6.83% | 62.66% | 16/23 | 11/140 |
| 19 | Hybrid + cutoff 0.65 | 4.85% | 44.08% | 20/23 | 52/140 |
| 20 | Hybrid + 0.55 + local cross-encoder reranker | 3.59% | 34.89% | 9/23 | 1/140 |
| 21 | Hybrid + 0.55 + Gemini, five passages | 54.15% | 46.93% | 23/23 | 46/140 |
| 22 | Run 1: Gemini, ten passages, cutoff 0.50 | 65.70% | 61.38% | 17/23 | 17/140 |
| 23 | Run 2: conditional twenty-passage recovery at 0.45 | 70.43% | 64.56% | 13/23 | 12/140 |

| 24 | Run 2: Gemini 3.1 quota-amended recovery | 73.02% | 65.59% | 0/23 | 0/140 |

The small exact-answer pilot improved precision from 3.06% to 6.00% on its own ten-question subset, but recall fell from 45.88% to 35.40%; correct negative abstention was 2/5. It was rejected. These numbers are not comparable to full-train aggregates. Superseded boundary-fix and timing replays remain preserved in the [all-model audit](evaluation/ALL_MODELS_SUMMARY.md).

## Concrete failure analysis

The following twelve examples were chosen from train after scoring. Gold spans are used here only for diagnosis. Full questions, source paths, offsets, annotated text and returned evidence are in [the detailed failure file](evaluation/ERROR_ANALYSIS_TRAIN.md). No test labels were used to redesign the pipelines.

| Case | Stage | Failure | Question excerpt / query ID | Diagnosis |
|---|---:|---|---|---|
| 1 | 22 | partial_evidence | Are there any exceptions to competitive restrictions in this contract? (`5aacd88644`) | Returned evidence overlaps the annotated answer but omits part of its span. Longer complete-clause evidence or additional support may help; this is an offset-level diagnosis. |
| 2 | 22 | partial_evidence | Does this contract include any right of first refusal, right of first offer, or right of first negot (`13d8e76465`) | Returned evidence overlaps the annotated answer but omits part of its span. Longer complete-clause evidence or additional support may help; this is an offset-level diagnosis. |
| 3 | 22 | partial_evidence | How is intellectual property ownership assigned in this contract? (`505f5239e0`) | Returned evidence overlaps the annotated answer but omits part of its span. Longer complete-clause evidence or additional support may help; this is an offset-level diagnosis. |
| 4 | 22 | wrong_section | What is the expiration date of this contract? (`83b1521f8c`) | Returned evidence has zero character overlap with the annotated answer; rank/source selection needs review. |
| 5 | 22 | false_abstention | Is there a covenant not to sue included in this contract? (`4e02d75b0e`) | No gold overlap in the first-stage supplied context; retrieval expansion or routing is needed. |
| 6 | 22 | wrong_section | What is the expiration date of this contract? (`652ee16919`) | Returned evidence has zero character overlap with the annotated answer; rank/source selection needs review. |
| 7 | 22 | false_abstention | Does this contract include any revenue or profit-sharing arrangements? (`4270fd03ea`) | Retrieved context contained some gold overlap, but no evidence was returned. |
| 8 | 22 | wrong_section | Is there a non-compete clause in this contract? (`e72f339f6d`) | Returned evidence has zero character overlap with the annotated answer; rank/source selection needs review. |
| 9 | 22 | false_abstention | What are the audit rights under this contract? (`4c60c9594f`) | No gold overlap in the first-stage supplied context; retrieval expansion or routing is needed. |
| 10 | 23 | invalid_fallback | Does the agreement allow sublicensing to third-party platforms? (`f03c96c14e`) | The output failed validation, so the declared fallback returned original passages for a labeled unanswerable query. Strict formatting plus fallback policy caused this false return. |
| 11 | 23 | invalid_fallback | When does the exclusivity period end? (`8880cd6a3b`) | The output failed validation, so the declared fallback returned original passages for a labeled unanswerable query. Strict formatting plus fallback policy caused this false return. |
| 12 | 23 | invalid_fallback | Which clause requires approval before using ChatGPT on customer communications? (`439a5a9054`) | The output failed validation, so the declared fallback returned original passages for a labeled unanswerable query. Strict formatting plus fallback policy caused this false return. |

Wrong-section and partial-evidence cases motivate better ranking and full-clause support, but the measured generic reranker did not help. False abstentions have two causes: missing evidence in the supplied context, and missed support despite some relevant retrieved text. Invalid-output fallbacks expose a separate engineering issue: an incompatible no-answer sentence can turn an otherwise cautious output into returned passages. These causes should not be conflated.

## Business trade-offs and limitations

| Choice | Benefit | Cost or risk |
|---|---|---|
| Original BM25 | Cheap, local, transparent, no provider dependency | Weak baseline recall and no useful negative abstention |
| Tuned BM25 | Strong local recall with simple operational setup | Broad passages keep character precision low; unsupported questions still return text |
| Local Phi-3 | Offline inference option, cached and inspectable | Slow first use and frequent exact-output failures; no quality guarantee from brevity |
| Pure semantic / hybrid | Semantic candidates complement lexical matches | Extra model/index dependencies; hybrid did not automatically beat tuned BM25 |
| Run 1 | Stronger evidence precision with one generation stage; fewer negative false returns than Run 2 on train | API dependency and false answerable abstention above the target |
| Run 2 | Recovery increases precision/recall and reduces false answerable abstention on train | Extra latency/calls and weaker negative abstention due to fallback behaviour |
| Cached presentation | Fast, repeatable, no API cost during known demonstrations | A cache is not proof of live-model reliability or generalisation |

Neither late Gemini version passed every train gate. A claim of production readiness would require broader annotated negatives, human review of summary faithfulness and legal qualifications, confidence calibration, robust invalid-output handling, privacy/retention decisions and operational monitoring. Those are limitations, not completed features.

The test set is small and repeated train-based choices create selection optimism. Test results may differ in either direction. All three held-out outcomes must be reported, including failures; no settings are changed in response. Generated summaries are not legally authoritative. Definition/reference parsing is heuristic, handles unique same-document targets only, and was not adopted as a retrieval improvement. Local encoder truncation and exact-quote validation failures remain recorded rather than hidden.

## Reproducibility and deliverables

The organised project contains root web/CLI/command entry points, shared src/, explicit scripts/, all configurations and prompts, checked caches, append-only logs, per-iteration record folders, ten presentation notebooks, complete implementation walkthroughs, frozen negatives and core tests. README.md gives setup, data/model preparation, offline demo, train evaluation, loop demonstration and frozen test commands. Runtime/library/model versions, source hashes, usage and raw predictions are retained.

Code and settings are frozen in evaluation/execution_freeze.json before held-out generation. evaluation/test_runs.jsonl is the authoritative attempt ledger; preparation-time counters in historical manifests are snapshots, not a replacement for that ledger. Provider outputs are cached, credentials are not. Personal guides and the source assignment PDF are excluded. Git history must also be checked before publication so excluded personal files do not remain in old commits.

Useful entry points: [selected ten](evaluation/SELECTED_VERSIONS.md), [complete model summary](evaluation/ALL_MODELS_SUMMARY.md), [iteration folders](experiments/README.md), and [presentation notebooks](notebooks/presentation/README.md).

## Quota-driven provider amendment before held-out scoring

After Run 1 test responses were prepared, the user confirmed only one Gemini
3.5 daily request remained and requested Gemini 3.1 for recovery. No test
metrics had been calculated. The original freeze was archived; the amendment
was recorded before generation in evaluation/PROTOCOL_AMENDMENT_31.json.
Run 1, its cached answers, prompts, cutoffs, candidate pools, validation and
fallback stayed fixed. Only Run 2 recovery calls changed provider model.

The original all-3.5 Run 2 remains iteration 23. A matched train counterpart
for the mixed 3.5/3.1 policy is iteration 24: 73.02% precision, 65.59% recall,
0/23 correct negative abstentions and 0/140 false answerable abstentions.
The poor negative result is a failure, not an improvement: invalid no-answer
outputs fell back to retrieved passages. Its final held-out result must not
be compared against iteration 23 as if both used the same provider.

The final three-model test table uses baseline, Run 1 and this explicitly
amended Run 2. Both train counterparts and original results remain visible.
The protocol change was driven by quota, not test quality or label inspection.

## Matched train/test results for the three final configurations

All test configurations were selected before metrics were viewed; one evaluation attempt each. Run 2 uses the declared quota-amended provider policy on both splits.

| Model | Split | Answerable / negative n | Precision@5 | Recall@5 | Benchmark P/R | Correct abstention | False abstention |
|---|---|---|---:|---:|---|---:|---:|
| Run 1 (Gemini 3.5) | train | 140 / 23 | 65.70% | 61.38% | 65.69% / 62.79% | 17/23 (73.91%) | 17/140 (12.14%) |
| Run 1 (Gemini 3.5) | test | 54 / 7 | 58.14% | 56.94% | 58.21% / 58.61% | 5/7 (71.43%) | 4/54 (7.41%) |
| Run 2 (3.5 first stage + 3.1 recovery) | train | 140 / 23 | 73.02% | 65.59% | 73.04% / 67.19% | 0/23 (0.00%) | 0/140 (0.00%) |
| Run 2 (3.5 first stage + 3.1 recovery) | test | 54 / 7 | 65.87% | 62.99% | 65.86% / 63.78% | 2/7 (28.57%) | 0/54 (0.00%) |
| Baseline (local BM25) | train | 140 / 23 | 1.74% | 18.16% | 1.76% / 19.24% | 0/23 (0.00%) | 0/140 (0.00%) |
| Baseline (local BM25) | test | 54 / 7 | 0.80% | 13.87% | 0.76% / 13.87% | 0/7 (0.00%) | 0/54 (0.00%) |

| Model | Test minus train precision | Test minus train recall |
|---|---:|---:|
| Run 1 (Gemini 3.5) | -7.55 points | -4.44 points |
| Run 2 (3.5 first stage + 3.1 recovery) | -7.15 points | -2.60 points |
| Baseline (local BM25) | -0.94 points | -4.30 points |

No pipeline tuning or new provider calls followed these scores. A service HTTP 503 during response preparation was preserved and retried as a transport failure; it was not an additional model evaluation. See test_runs.jsonl for evaluation attempts and cache/failed_attempts provenance for the provider failure.

### Test inference and replay accounting

| Configuration | Unique API responses used | Model versions | Tokens (input / output) | Estimated first-use p50 / p95 ms | Cached p50 / p95 ms |
|---|---:|---|---|---|---|
| broad10 | 58 | gemini-3.5-flash-lite: 58 | 162,110 / 7,310 | 4123.72 / 14021.12 | 13.03 / 16.57 |
| recovery20 | 74 | gemini-3.5-flash-lite: 58, gemini-3.1-flash-lite: 16 | 244,786 / 9,079 | 4799.04 / 14020.50 | 13.58 / 28.28 |
| baseline | 0 | Local BM25 | 0 / 0 | 6.53 / 8.17 | 6.53 / 8.17 |

Run 2 response/token totals include reused first-stage calls; they are not additional API charges for replay. Sixteen extra recovery calls used Gemini 3.1. The Run 1 provider 503 was retained in failed-attempt history and retried once without model-output regeneration. Timing excludes startup and quota pacing. Saved-prediction rescoring verifies arithmetic without generating new predictions; the model-evaluation ledger remains one attempt per configuration.

Publication history was filtered only to remove excluded personal/credential/PDF paths; chronological experiment proof and frozen negatives remain. Historical commit-ID mapping is under experiments/source_snapshots/.
