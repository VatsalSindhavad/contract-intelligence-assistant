# Contract retrieval experiments

Work proceeds one notebook at a time: data validation, a simple baseline,
measured improvements, a working core application, then LLM experiments.
Each approach will retain its configuration, run instructions, predictions,
and metrics. At least five improvement iterations will be logged, including
rejected changes. The eventual 4–5 approach comparison will explain retrieval
quality, abstention, latency, cost, privacy, and operational tradeoffs.

The current target is seven distinct improvement iterations beyond baseline,
including later LLM experiments. See `experiments/PLAN.md`. Core quality takes
priority over the planned count; LLMs remain deferred until the core works.

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

Codex helped inspect requirements, write and run notebooks, implement retrieval
and evaluation, create synthetic negative questions, build the rule-based
experiment loop, write tests, and maintain documentation. No LLM API is part
of retrieval yet. Review and understand each component before presenting it.

## BM25 baseline

After data preparation, run all cells in `notebooks/02_bm25_baseline.ipynb`.
Shared functions are in `retrieval.py`; initial settings are in
`configs/bm25_baseline.json`. Edit the demo question in the notebook for an
interactive walkthrough. Later variants should use separate configuration
files and names, preserving the baseline.

Each execution writes a new directory under `results/bm25_baseline/` with
configuration and environment metadata, per-query scores, retrieved passages,
and aggregate train metrics. No external model or API is required.
Train unanswerable evaluation is available in notebook 03; threshold calibration
remains pending. The baseline uses only a positive-score rule. The development
evaluator rejects test data.

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
This notebook replays the historical first proposal. Rerunning it does not
count as a new improvement iteration; use the loop below to advance.

## Diagnostic-driven improvement loop

Run `python improve.py` for **one new iteration**, then inspect its result.
The command diagnoses the selected configuration on train, chooses an untried
change from `experiments/proposals.json`, evaluates it, and accepts or rejects
it using the existing guardrails. It resumes from `experiments/loop_log.jsonl`.
The original iteration is preserved in `experiments/log.jsonl`. Consider both
logs when counting distinct iterations. New results also compare the original
baseline. When the catalog is exhausted, the command stops without a new entry.

`python improve.py --steps 3` runs three successive steps when desired.
Use one step while reviewing results. Do not run `run_experiment.py` to advance
the loop: that script replays only the historical first proposal.
Recorded configurations under each result folder can be loaded into
`BM25Retriever` to rerun accepted or rejected approaches. Notebook 05 reviews
saved loop results without starting another experiment when run again.

## Setup commands

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m ipykernel install --user --name contract-retrieval --display-name "Contract retrieval"
```

Select that kernel in VS Code or your Jupyter installation. The project was
checked with Python 3.12.4. Direct dependencies match the installed evaluation
environment; a clean-environment reproduction is still a release check.
Run notebooks 01, 02, and 03 in order to prepare and measure the baseline.
Notebook 04 replays the first experiment; notebook 05 reviews saved loop runs.
Recorded timings belong to the report, and will be refreshed for final runs.

## Architecture and assumptions

Notebook 01 downloads and validates the selected data. `retrieval.py` chunks,
indexes, searches, and scores passages. `negative_validation.py` validates the
frozen negative set. `improve.py` diagnoses train failures and proposes settings
from `experiments/proposals.json`. Settings live in JSON; runs retain snapshots.
Both future interfaces will call the same retrieval implementation.

We search all selected contracts rather than using gold document IDs as filters.
Offsets are Python string indices in half-open intervals `[start, end)` after
UTF-8 text-mode newline conversion. Queries are equally weighted. Synthetic
negative labels mean the requested fact is not established by the corpus.
Definitions, external schedules, and cross-references are not resolved; record
these as limitations rather than treating an incomplete clause as legal advice.

Experiment decisions use unique-character precision/recall to avoid counting
overlapping chunks twice. Additional `benchmark_precision`/`benchmark_recall`
fields reproduce the authors' pairwise passage-overlap convention. That recall
can exceed 1 with overlapping retrieved passages. Report both conventions
explicitly; do not label them interchangeably. See `evaluation/metrics.md`.

See `CORE_CHECKLIST.md` for delivery status and `REPORT.md` for measured results.
Web/search CLI commands and final test reproduction instructions will be added
when those interfaces and the final evaluator exist.

Notebook 06 reviews the saved third iteration (BM25 length normalization) and
provides an editable question cell for either configuration without advancing
the loop. Its measured findings are recorded in REPORT.md.
