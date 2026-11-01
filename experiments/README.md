# Experiment directory

Each iteration folder contains its record, configuration snapshot, metrics, file index and a runnable review notebook. Full raw results and shared source remain central to avoid inconsistent copies.

| Iteration | Approach | Review |
|---|---|---|
| 00 | Original BM25 baseline | [00](iterations/00/README.md) |
| 01 | BM25 + stopword removal | [01](iterations/01/README.md) |
| 02 | BM25 + 500-character chunks | [02](iterations/02/README.md) |
| 03 | BM25 with b=0.30 | [03](iterations/03/README.md) |
| 04 | BM25 with k1=0.80 | [04](iterations/04/README.md) |
| 05 | BM25 + document/clause routing | [05](iterations/05/README.md) |
| 06 | BM25 + focused clause query | [06](iterations/06/README.md) |
| 07 | BM25 + focused clause query + fallback | [07](iterations/07/README.md) |
| 08 | BM25 + focused query, fallback and stemming | [08](iterations/08/README.md) |
| 09 | BM25 + Gemini query expansion | [09](iterations/09/README.md) |
| 10 | BM25 + Phi-3 query expansion | [10](iterations/10/README.md) |
| 11 | MiniLM + FAISS, fixed windows | [11](iterations/11/README.md) |
| 12 | Phi-3 reference on the same small subset | [12](iterations/12/README.md) |
| 13 | BM25/Phi-3 + one-shot summary and evidence | [13](iterations/13/README.md) |
| 15 | Clause-aware MiniLM + FAISS | [15](iterations/15/README.md) |
| 16 | Clause-aware MiniLM + cutoff 0.20 | [16](iterations/16/README.md) |
| 17 | Definition/reference-enriched MiniLM + FAISS | [17](iterations/17/README.md) |
| 18 | Original MiniLM + cutoff 0.40 | [18](iterations/18/README.md) |
| 19 | BM25 + MiniLM hybrid, ungated | [19](iterations/19/README.md) |
| 20 | Hybrid + 0.55 + local cross-encoder reranker | [20](iterations/20/README.md) |
| 21 | Hybrid + 0.55 + Gemini, five passages | [21](iterations/21/README.md) |
| 22 | Run 1: Gemini, ten passages, cutoff 0.50 | [22](iterations/22/README.md) |
| 23 | Run 2: conditional twenty-passage recovery at 0.45 | [23](iterations/23/README.md) |
| 24 | Run 2: Gemini 3.1 quota-amended recovery | [24](iterations/24/README.md) |

Reserved iteration 14 was not run: [Kanon preparation](unrun/kanon/README.md).

Historical pre-cleanup source is under source_snapshots/pre_cleanup_20261101/ for provenance. It is not the active runtime.
