# Contract retrieval experiments

Work proceeds one notebook at a time: data validation, a simple baseline,
measured improvements, a working core application, then LLM experiments.
Each approach will retain its configuration, run instructions, predictions,
and metrics. At least five improvement iterations will be logged, including
rejected changes. The eventual 4–5 approach comparison will explain retrieval
quality, abstention, latency, cost, privacy, and operational tradeoffs.

The current budget is at most ten improvement iterations beyond baseline.
Eight non-LLM trials are recorded, with three accepted changes. See
`experiments/PLAN.md`. LLMs remain deferred until the core works.

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
Web/search CLI commands are below; final test reproduction instructions will
be added when the final evaluator exists.

Notebook 06 reviews the saved third iteration (BM25 length normalization) and
provides an editable question cell for either configuration without advancing
the loop. Its measured findings are recorded in REPORT.md.

## Accepted non-LLM approaches

Notebook 08 reviews saved trials 5–7 and provides an editable question cell.
Load `configs/bm25_document_then_clause.json` or
`configs/bm25_focused_clause_fallback.json` into `BM25Retriever`; the baseline
and rejected `configs/bm25_focused_clause.json` also remain runnable.
Routing activates for `Consider document description; clause question`.
Plain questions fall back to full-query search. These format assumptions
must be considered when comparing approaches and using the future interfaces.

Notebook 09 reviews the accepted combined pipeline plus English stemming.
Its configuration is `configs/bm25_focused_stemmed.json`; NLTK Snowball needs
no separate corpus download. Earlier configurations remain available.

## Search interfaces

```powershell
python cli.py "Consider the Wireless Content License Agreement between Fox Mobile Entertainment and Glu Mobile; What is the expiration date of this contract?" --k 3
python cli.py --list-configs
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true --browser.gatherUsageStats false
```

Open http://127.0.0.1:8501 after starting Streamlit. Both interfaces default to
`bm25_focused_stemmed` and share `search_service.py`. The service loads corpus
text and saved configuration only, never train/test question labels. Select
any preserved configuration; the CLI supports `--config NAME`, `--k N`, and
`--json`. Results include exact passage text, source, offsets, score, and timing.

See `DEMO.md` for the walkthrough, expected example, no-match check, and known
limitations. Model loading/index building occurs before displayed search timing.
Streamlit caches each model until the config/manifest fingerprint changes or
the server restarts. Restart after changing corpus files or retrieval code.

## Choose a saved version

Run these commands from the project folder after installing requirements and
running data preparation notebook 01. Configuration names omit `.json`.

| CLI configuration | Version | Experiment outcome |
|---|---|---|
| `bm25_baseline` | Original full-query BM25 | Baseline reference |
| `bm25_stopwords` | Common-word filtering | Rejected, iteration 1 |
| `bm25_chunks_500` | Smaller chunks | Rejected, iteration 2 |
| `bm25_b_030` | Lower length normalization | Rejected, iteration 3 |
| `bm25_k1_080` | Lower term saturation | Rejected, iteration 4 |
| `bm25_document_then_clause` | Document identification then clause search | Accepted, iteration 5 |
| `bm25_focused_clause` | Focused clause terms without fallback | Rejected, iteration 6 |
| `bm25_focused_clause_fallback` | Focused terms with fallback | Accepted, iteration 7 |
| `bm25_focused_stemmed` | Accepted pipeline plus stemming | Accepted, iteration 8; default |

```powershell
python cli.py --list-configs
$question = "Consider the Wireless Content License Agreement between Fox Mobile Entertainment and Glu Mobile; What is the expiration date of this contract?"
python cli.py $question --config bm25_baseline --k 5
python cli.py $question --config bm25_document_then_clause --k 5
python cli.py $question --config bm25_focused_clause_fallback --k 5
python cli.py $question --config bm25_focused_stemmed --k 5 --json
```

Replace the name after `--config` with any table entry to run that version,
including rejected experiments. `--k` returns up to 1–20 positive-score
passages. Omitting `--config` selects `bm25_focused_stemmed`. `--json` changes
the output format only. These commands search a question; they do not rerun
benchmark evaluation or advance the improvement loop. Outcomes describe train
experiment decisions, not whether a configuration can execute.

The same versions are selectable in the web app. Start it using the command
above, select a configuration, and click Search to apply that choice.
