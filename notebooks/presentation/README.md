# Ten presentation versions

These ten notebooks form the train-history presentation. Only Run 1, Run 2 and baseline are selected for held-out evaluation. Each notebook reads recorded results and a cached example; no provider generation is permitted.

| # | Version | Notebook | Full walkthrough |
|---|---|---|---|
| 1 | Original BM25 baseline | [01_comparison.ipynb](01_comparison.ipynb) | [Full notebook](../experiments/02_bm25_baseline.ipynb) |
| 2 | Improved BM25 with stemming | [02_comparison.ipynb](02_comparison.ipynb) | [Full notebook](../experiments/09_combined_bm25_stemming.ipynb) |
| 3 | BM25 + Gemini query expansion | [03_comparison.ipynb](03_comparison.ipynb) | [Full notebook](../experiments/10_gemini_bm25.ipynb) |
| 4 | BM25 + Phi-3 query expansion | [04_comparison.ipynb](04_comparison.ipynb) | [Full notebook](../experiments/11_local_phi3_comparison.ipynb) |
| 5 | BM25 + Phi-3 summary and evidence | [05_comparison.ipynb](05_comparison.ipynb) | [Full notebook](../experiments/14_phi3_full_summary.ipynb) |
| 6 | MiniLM + FAISS with 0.55 cutoff | [06_comparison.ipynb](06_comparison.ipynb) | [Full notebook](../experiments/17_hybrid_bm25_minilm.ipynb) |
| 7 | Hybrid with 0.55 cutoff | [07_comparison.ipynb](07_comparison.ipynb) | [Full notebook](../experiments/17_hybrid_bm25_minilm.ipynb) |
| 8 | Hybrid + 0.55 cutoff + Gemini | [08_comparison.ipynb](08_comparison.ipynb) | [Full notebook](../experiments/19_hybrid_gemini_summary.ipynb) |
| 9 | Run 1: ten-passage Gemini at 0.50 | [09_comparison.ipynb](09_comparison.ipynb) | [Full notebook](../experiments/20_gemini_broad10.ipynb) |
| 10 | Run 2: conditional recovery with Gemini 3.1 | [10_comparison.ipynb](10_comparison.ipynb) | [Full notebook](../experiments/22_gemini_recovery31.ipynb) |
