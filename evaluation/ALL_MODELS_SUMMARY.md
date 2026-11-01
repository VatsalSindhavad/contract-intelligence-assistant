# All completed model and threshold experiments

This is the summary of the full experiment history, separate from [the selected ten](SELECTED_VERSIONS.md). **★** marks the ten presentation versions; only baseline, Run 1 and Run 2 are selected for test, as recorded in final_test_selection.json; it does not mean all guardrails passed. All headline numbers below use unique-character overlap at k=5. Correct abstention counts negative questions rejected; false abstention counts answerable questions wrongly rejected. Higher precision/recall/correct abstention and lower false abstention are preferred.

Full-train tables use 140 answerable and 23 negative questions. The small historical pilot is isolated below and must not be ranked directly against those tables. Three frozen configurations have now completed test evaluation once each; see FINAL_COMPARISON.md. These tables remain train-only. Additional k values and benchmark pairwise scores are retained in ALL_MODELS_SUMMARY.json and the original result files.

## BM25

| Iteration | Version | Precision@5 | Recall@5 | Correct abstention | False abstention |
|---|---|---:|---:|---:|---:|
| 0 | ★ Original BM25 baseline | 1.74% | 18.16% | 0/23 (0.00%) | 0/140 (0.00%) |
| 1 | BM25 + stopword removal | 1.61% | 15.89% | 0/23 (0.00%) | 0/140 (0.00%) |
| 2 | BM25 + 500-character chunks | 0.78% | 4.09% | 0/23 (0.00%) | 0/140 (0.00%) |
| 3 | BM25 with b=0.30 | 1.79% | 18.82% | 0/23 (0.00%) | 0/140 (0.00%) |
| 4 | BM25 with k1=0.80 | 1.57% | 16.16% | 0/23 (0.00%) | 0/140 (0.00%) |
| 5 | BM25 + document/clause routing | 5.15% | 47.12% | 0/23 (0.00%) | 0/140 (0.00%) |
| 6 | BM25 + focused clause query | 5.81% | 50.72% | 1/23 (4.35%) | 12/140 (8.57%) |
| 7 | BM25 + focused clause query + fallback | 6.28% | 53.50% | 0/23 (0.00%) | 0/140 (0.00%) |
| 8 | ★ BM25 + focused query, fallback and stemming | 7.88% | 67.01% | 0/23 (0.00%) | 0/140 (0.00%) |

## BM25 with LLM

| Iteration | Version | Precision@5 | Recall@5 | Correct abstention | False abstention |
|---|---|---:|---:|---:|---:|
| 9 | ★ BM25 + Gemini query expansion | 8.47% | 79.10% | 0/23 (0.00%) | 0/140 (0.00%) |
| 10 | ★ BM25 + Phi-3 query expansion | 8.07% | 70.75% | 0/23 (0.00%) | 0/140 (0.00%) |
| 13 | ★ BM25/Phi-3 + one-shot summary and evidence | 20.08% | 68.92% | 7/23 (30.43%) | 3/140 (2.14%) |

## Pure semantic and indexing changes

| Iteration | Version | Precision@5 | Recall@5 | Correct abstention | False abstention |
|---|---|---:|---:|---:|---:|
| 11 | MiniLM + FAISS, fixed windows | 4.03% | 35.75% | 0/23 (0.00%) | 0/140 (0.00%) |
| 15 | Clause-aware MiniLM + FAISS | 5.12% | 19.74% | 0/23 (0.00%) | 0/140 (0.00%) |
| 17 | Definition/reference-enriched MiniLM + FAISS | 3.87% | 35.70% | 0/23 (0.00%) | 0/140 (0.00%) |

## Semantic abstention sweeps

| Iteration | Version | Precision@5 | Recall@5 | Correct abstention | False abstention |
|---|---|---:|---:|---:|---:|
| 16 | Clause-aware MiniLM + cutoff 0.20 | 5.12% | 19.74% | 0/23 (0.00%) | 0/140 (0.00%) |
| 16 | Clause-aware MiniLM + cutoff 0.30 | 5.12% | 19.74% | 0/23 (0.00%) | 0/140 (0.00%) |
| 16 | Clause-aware MiniLM + cutoff 0.40 | 5.12% | 19.74% | 0/23 (0.00%) | 0/140 (0.00%) |
| 16 | Clause-aware MiniLM + cutoff 0.50 | 5.12% | 19.74% | 1/23 (4.35%) | 0/140 (0.00%) |
| 16 | Clause-aware MiniLM + cutoff 0.60 | 4.91% | 19.02% | 14/23 (60.87%) | 10/140 (7.14%) |
| 16 | Clause-aware MiniLM + cutoff 0.70 | 1.91% | 7.12% | 22/23 (95.65%) | 84/140 (60.00%) |
| 16 | Clause-aware MiniLM + cutoff 0.80 | 0.00% | 0.00% | 22/23 (95.65%) | 140/140 (100.00%) |
| 17 | Enriched MiniLM + cutoff 0.40 | 3.87% | 35.70% | 0/23 (0.00%) | 0/140 (0.00%) |
| 17 | Enriched MiniLM + cutoff 0.45 | 3.87% | 35.70% | 0/23 (0.00%) | 0/140 (0.00%) |
| 17 | Enriched MiniLM + cutoff 0.50 | 3.87% | 35.70% | 3/23 (13.04%) | 0/140 (0.00%) |
| 17 | Enriched MiniLM + cutoff 0.55 | 3.87% | 35.70% | 9/23 (39.13%) | 1/140 (0.71%) |
| 17 | Enriched MiniLM + cutoff 0.60 | 3.64% | 33.14% | 15/23 (65.22%) | 11/140 (7.86%) |
| 17 | Enriched MiniLM + cutoff 0.65 | 2.57% | 22.91% | 20/23 (86.96%) | 52/140 (37.14%) |
| 18 | Original MiniLM + cutoff 0.40 | 4.03% | 35.75% | 0/23 (0.00%) | 0/140 (0.00%) |
| 18 | Original MiniLM + cutoff 0.45 | 4.03% | 35.75% | 0/23 (0.00%) | 0/140 (0.00%) |
| 18 | Original MiniLM + cutoff 0.50 | 4.03% | 35.75% | 3/23 (13.04%) | 0/140 (0.00%) |
| 18 | ★ Original MiniLM + cutoff 0.55 | 4.03% | 35.75% | 9/23 (39.13%) | 1/140 (0.71%) |
| 18 | Original MiniLM + cutoff 0.60 | 3.82% | 33.90% | 16/23 (69.57%) | 11/140 (7.86%) |
| 18 | Original MiniLM + cutoff 0.65 | 2.68% | 23.68% | 20/23 (86.96%) | 52/140 (37.14%) |

## Hybrid and reranking

| Iteration | Version | Precision@5 | Recall@5 | Correct abstention | False abstention |
|---|---|---:|---:|---:|---:|
| 19 | BM25 + MiniLM hybrid, ungated | 7.14% | 66.23% | 0/23 (0.00%) | 0/140 (0.00%) |
| 19 | Hybrid + cutoff 0.40 | 7.14% | 66.23% | 0/23 (0.00%) | 0/140 (0.00%) |
| 19 | Hybrid + cutoff 0.45 | 7.14% | 66.23% | 0/23 (0.00%) | 0/140 (0.00%) |
| 19 | Hybrid + cutoff 0.50 | 7.14% | 66.23% | 3/23 (13.04%) | 0/140 (0.00%) |
| 19 | ★ Hybrid + cutoff 0.55 | 7.12% | 65.51% | 9/23 (39.13%) | 1/140 (0.71%) |
| 19 | Hybrid + cutoff 0.60 | 6.83% | 62.66% | 16/23 (69.57%) | 11/140 (7.86%) |
| 19 | Hybrid + cutoff 0.65 | 4.85% | 44.08% | 20/23 (86.96%) | 52/140 (37.14%) |
| 20 | Hybrid + 0.55 + local cross-encoder reranker | 3.59% | 34.89% | 9/23 (39.13%) | 1/140 (0.71%) |

## Hybrid with Gemini

| Iteration | Version | Precision@5 | Recall@5 | Correct abstention | False abstention |
|---|---|---:|---:|---:|---:|
| 21 | ★ Hybrid + 0.55 + Gemini, five passages | 54.15% | 46.93% | 23/23 (100.00%) | 46/140 (32.86%) |
| 22 | ★ Run 1: Gemini, ten passages, cutoff 0.50 | 65.70% | 61.38% | 17/23 (73.91%) | 17/140 (12.14%) |
| 23 | Run 2: conditional twenty-passage recovery at 0.45 | 70.43% | 64.56% | 13/23 (56.52%) | 12/140 (8.57%) |

| 24 | ★ Run 2: Gemini 3.1 quota-amended recovery | 73.02% | 65.59% | 0/23 (0.00%) | 0/140 (0.00%) |

## Historical small pilot

| Iteration | Version | Precision@5 | Recall@5 | Correct abstention | False abstention |
|---|---|---:|---:|---:|---:|
| 12 | Phi-3 reference on the same small subset | 3.06% | 45.88% | 0/5 (0.00%) | 0/10 (0.00%) |
| 12 | Phi-3 exact-answer extraction pilot | 6.00% | 35.40% | 2/5 (40.00%) | 0/10 (0.00%) |

## Preserved reruns and unrun work

Quality tables use the latest completed record for each modelling idea. Earlier executions remain retained as audit records, not counted as new models:

| Iteration | Earlier run | Explanation |
|---|---|---|
| 12 | 20261101T065035718115Z | Timing-accounting replay; same pilot, not a second model |
| 15 | 20261101T075039515494Z | Superseded boundary-fix run; corrected complete rerun is shown above |
| 16 | 20261101T075039515494Z | Superseded boundary-fix run; corrected complete rerun is shown above |

Kanon + FAISS (reserved iteration 14) was prepared but **not run**. It has no metric row and is not a measured model. Untried proposals such as larger BM25 chunks and additional score-threshold ideas are proposals only, not experiments with results.

Run 2 is Run 1 plus conditional recovery: 105 first-stage answers were reused and 58 queries retried. Its table row evaluates all 163 train questions, not just retries. Invalid-output fallbacks remain included in every applicable aggregate. The full-train count is **46 measured configurations including threshold variants**, not 45 independent modelling ideas.

Configuration selection and historical acceptance are separate. Historical objectives changed over the project and must not be rewritten after measurement; source logs preserve original decisions. Only the three test candidates require final execution freeze before held-out reporting; the ten remain the presentation shortlist.

The user-approved quota amendment is in PROTOCOL_AMENDMENT_31.json. Original iteration 23 is unchanged; iteration 24 is a matched train counterpart for the final mixed-provider policy.
