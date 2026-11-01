# Ten presentation versions (train results)

Ten versions show progression and trade-offs. Only baseline, Run 1 and quota-amended Run 2 are selected for held-out evaluation. The original all-3.5 Run 2 remains in the complete history. ★ does not imply guardrail acceptance.

| # | Version | Precision@5 | Recall@5 | Correct abstention | False abstention |
|---|---|---:|---:|---:|---:|
| 1 | Original BM25 baseline | 1.74% | 18.16% | 0/23 | 0/140 |
| 2 | Improved BM25 with stemming | 7.88% | 67.01% | 0/23 | 0/140 |
| 3 | BM25 + Gemini query expansion | 8.47% | 79.10% | 0/23 | 0/140 |
| 4 | BM25 + Phi-3 query expansion | 8.07% | 70.75% | 0/23 | 0/140 |
| 5 | BM25 + Phi-3 summary and evidence | 20.08% | 68.92% | 7/23 | 3/140 |
| 6 | MiniLM + FAISS with 0.55 cutoff | 4.03% | 35.75% | 9/23 | 1/140 |
| 7 | Hybrid with 0.55 cutoff | 7.12% | 65.51% | 9/23 | 1/140 |
| 8 | Hybrid + 0.55 cutoff + Gemini | 54.15% | 46.93% | 23/23 | 46/140 |
| 9 | Run 1: ten-passage Gemini at 0.50 | 65.70% | 61.38% | 17/23 | 17/140 |
| 10 | Run 2: conditional recovery with Gemini 3.1 | 73.02% | 65.59% | 0/23 | 0/140 |

Run 2 uses Gemini 3.5 first-stage caches and Gemini 3.1 recovery after a quota-driven, user-approved amendment before test scoring. Its matching train counterpart is iteration 24. All other attempts remain in ALL_MODELS_SUMMARY.md.
