# Matched final train/test comparison

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
