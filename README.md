# Contract retrieval experiments

See `experiments/PLAN.md` for current scope. BM25/LLM trials 1–10 and the
basic MiniLM/FAISS trial 11 are preserved. Semantic work is paused while an
instruction-only local Phi-3 extraction pilot tests precision with recall
protection. Every attempt is logged; ten representative versions will be
selected for presentation later. No previous model or result is overwritten.

Work proceeds one notebook at a time: data validation, a simple baseline,
measured improvements, a working core application, then LLM experiments.
Each approach will retain its configuration, run instructions, predictions,
and metrics. At least five improvement iterations will be logged, including
rejected changes. The eventual ten-version presentation comparison will explain retrieval
quality, abstention, latency, cost, privacy, and operational tradeoffs.

There is no current fixed total-trial cap. Preserve every attempt and later
select ten representative presentation versions with the full rejected history
retained. The new precision pilot has its own scope and stop rule; semantic
work remains paused.

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
experiment loop, write tests, and maintain documentation. Gemini-assisted query expansion has since been added and cached. Review and understand each component before presenting it.

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
and latency separately for cache creation and replay. Both hosted Gemini and local Phi-3 rewrites are cached.

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

See `REPORT.md` for measured results, limitations, and remaining evaluation work.
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

Use the example commands above to compare versions. The app displays exact
evidence and a no-match state; reliable negative abstention remains a limitation. Model loading/index building occurs before displayed search timing.
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
| **✓ `bm25_document_then_clause`** | Document identification then clause search | Accepted, iteration 5 |
| `bm25_focused_clause` | Focused clause terms without fallback | Rejected, iteration 6 |
| **✓ `bm25_focused_clause_fallback`** | Focused terms with fallback | Accepted, iteration 7 |
| **✓ `bm25_focused_stemmed`** | Accepted pipeline plus stemming | Accepted, iteration 8; default |

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

**✓ Better than baseline** marks accepted train improvements that passed all
acceptance checks; held-out test performance remains unmeasured. The CLI list
and web selector use the same label. Small gains or candidates failing a
guardrail retain explanatory labels instead. Configuration command names are
unchanged; omit the display labels when passing `--config`.

## Hosted/local LLM preparation

Gemini API was evaluated first; the installed Phi-3 Mini model was evaluated second.
See `LLM_SETUP.md` for local key setup and the one-request check.
`python prepare_llm.py --config gemini` reports cache readiness with no model
calls. The shared prompt is in `prompts/retrieval_rewrite_v1.txt`; model and
generation settings live in `llm_configs/`, separate from runnable BM25 configs.
`llm_rewrite.py` validates and caches outputs and refuses cache-only misses.
The adapter retains the original question for routing and supplements only the
clause query. Hosted iteration 9 and local Phi-3 iteration 10 are scored.

`llm_gemini_rewrite` is available in the CLI and web selector in cache-only mode.
Use `--config llm_gemini_rewrite` or `--config llm_local_phi3_rewrite` with the
example question above for offline cached searches.
The API key is not needed for those cached examples. Missing cache entries fail
clearly without calling a provider. The non-LLM model remains the default.

The implementation uses plain Python, rank-bm25, NLTK, and direct provider HTTP
requests. LangChain is not used; orchestration and caching are explicit.

## Completed hosted/local comparison

The shared prompt was evaluated with Gemini and Phi-3; both output sets are
cached. Select `llm_gemini_rewrite` or `llm_local_phi3_rewrite` in the CLI/web
app. Neither presentation mode needs an API key or running model service for
cached questions. `python evaluate_llm.py --config local_phi3` replays local
train evaluation from cache. Notebook 11 presents the comparison.

Notebook 05 reviews all phase logs, including pilots. The original core loop
engine is `improve.py`, and controlled LLM comparisons use `evaluate_llm.py`.
The old core-proposal sequence is closed; the precision phase uses its separate
runner and declared policy. The current pilot failed its recall gate and is
stopped for review. Final held-out evaluation/reproduction remain pending.

## Pure semantic baseline

Install the optional semantic dependencies with
`python -m pip install -r requirements-semantic.txt`. Obtain the pinned public
model once if it is not already cached:

```powershell
python -c "from huggingface_hub import snapshot_download; snapshot_download('sentence-transformers/all-MiniLM-L6-v2', revision='1110a243fdf4706b3f48f1d95db1a4f5529b4d41')"
python cli.py "Consider the Wireless Content License Agreement between Fox Mobile Entertainment and Glu Mobile; What is the expiration date of this contract?" --config dense_minilm_faiss --k 5
```

The same choice is available in Streamlit. The runtime loads the pinned local
snapshot with offline mode; it never sends document/query text to a provider.
`dense_retrieval.py` uses normalized MiniLM vectors and exact FAISS search over
all source chunks. It does not use BM25 routing. Existing chunking and source
offsets are preserved. Default token limits/truncation are recorded in results.

Notebook 12 reviews iteration 11. `python evaluate_dense.py` replays the declared
train comparison and records the same proposal again, not a new iteration.
Vector caches live under cache/dense/ and are keyed by model/config/library and
text identities; a mismatched environment rebuilds vectors from the pinned
local model. Model weights are not included in Git. Current measurements and
limitations belong to REPORT.md. Kanon access and semantic+Gemini are future
steps; semantic models are separate from the BM25 improvement history.

On this Windows environment, notebook/web embedding of previously unseen
queries uses an isolated local Python worker to avoid a PyTorch DLL loading
issue in those runtimes. The model/settings are unchanged; known vectors load
without the worker. Diagnostic worker logs are ignored by Git.

## Local precision pilot

The new extraction candidate is separate from all prior pipelines. Its exact
instruction-only prompt is prompts/extract_answer_v1.txt; no example is used.
`python run_precision_pilot.py --fill --max-new 1` permits one local generation
for the fixed pilot. `python run_precision_pilot.py` evaluates completed caches
only. The pilot uses ten answerable and five negative train questions selected
independently of outcomes, not the whole train set. Its results must not be
compared directly to the full-train summary numbers.

The model sees only the question and retrieved passages. It must return one
exact source quote; offsets are computed and validated. Invalid output falls
back to the original candidates; explicit no-answer is measured as abstention.
See experiments/precision_objective.json for the predeclared quality gates.
If those fail, pause rather than automatically proceed to Gemini or semantics.
