# Contract retrieval experiments

Work proceeds one notebook at a time: data validation, a simple baseline,
measured improvements, a working core application, then LLM experiments.
Each approach will retain its configuration, run instructions, predictions,
and metrics. At least five improvement iterations will be logged, including
rejected changes. The eventual 4–5 approach comparison will explain retrieval
quality, abstention, latency, cost, privacy, and operational tradeoffs.

## First step

Use Python 3.12. Install `requirements.txt` in a virtual environment and open
`notebooks/01_data_preparation.ipynb` in Jupyter or VS Code. Run all cells.
The first run requires internet; subsequent runs use validated local files.
Run the notebook from this project or its notebooks directory.

Only the prescribed CUAD mini subset is prepared. No test performance is
measured during preparation. Test labels are retained for final evaluation;
development notebooks must use the train file only. The shared corpus includes
contracts referenced by both splits, as required by the benchmark setup.

Before improvement experiments, author and validate at least 30 unanswerable
questions and commit the fixed set. The original assignment PDF is excluded
from version control.

## AI tool usage

Codex read the supplied brief and helped prepare the data validation notebook
and project setup. Review and understand each cell before proceeding.

## BM25 baseline

After data preparation, run all cells in `notebooks/02_bm25_baseline.ipynb`.
Shared functions are in `retrieval.py`; initial settings are in
`configs/bm25_baseline.json`. Edit the demo question in the notebook for an
interactive walkthrough. Later variants should use separate configuration
files and names, preserving the baseline.

Each execution writes a new directory under `results/bm25_baseline/` with
configuration and environment metadata, per-query scores, retrieved passages,
and aggregate train metrics. No external model or API is required.
Unanswerable evaluation and threshold calibration are pending; this checkpoint
uses only a positive-score rule. The development evaluator rejects test data.

Run core checks from the project root with `python -m pytest -q`.
Notebook outputs and result files contain measured results; the eventual
evaluation report will contain the analysis.

## Unanswerable checkpoint

Run `notebooks/03_unanswerable_validation.ipynb` after the baseline notebook.
The versioned questions and corpus-bound hashes are in `evaluation/`.
This notebook validates the fixed set and evaluates only its train portion.
It uses the original baseline configuration without tuning the threshold.

## Future LLM runs

Read credentials from environment variables; never put keys in source,
notebooks, outputs, or commits. Local environment and secrets files are ignored.
LLM integration must persist request-keyed outputs, model identifiers and
settings, and support cache-only evaluation with no model calls. Measure cost
and latency separately for cache creation and replay. No LLM is used yet.

## First improvement iteration

Read `experiments/OBJECTIVE.md`, then run
`notebooks/04_bm25_first_improvement.ipynb` or `python run_experiment.py`.
Both entry points evaluate the baseline and one common-word filtering candidate
on train, diagnose errors, apply the declared policy, and save every result.
The notebook also provides a question cell to try either approach.

Candidate settings live in `configs/bm25_stopwords.json`. The baseline defaults
remain unchanged. `experiments/log.jsonl` records accepted and rejected runs;
`results/iteration_01/` contains predictions, metrics, decisions, and code hashes.
Only one distinct proposal is implemented in this checkpoint. Rerunning it
does not count as a new improvement iteration.
