# Contract Intelligence Assistant

Private repository: https://github.com/VatsalSindhavad/contract-intelligence-assistant

Search a fixed contract corpus, inspect ranked source passages and character
offsets, and return no evidence when support is insufficient. The default demo
compares Run 1, Run 2 and the original BM25 baseline. All previous attempts,
including unsuccessful ones, remain documented and reproducible.

## Setup

Use Python 3.12 and Git. From the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-semantic.txt
python manage.py prepare_data
python manage.py prepare_semantic --download
```

The data command downloads the pinned public CUAD benchmark, selects the
prescribed 194-query subset, verifies source offsets, and prepares the fixed
train/test split. Existing validated data is reused. Data preparation is not
held-out performance evaluation. MiniLM model weights are downloaded locally
and are not committed. Python/package/model revisions are recorded in results.
The measured machine used torch 2.11.0+cu128 with CPU inference; a different
library build may rebuild checked vector caches from the same pinned weights.

For notebook presentation, open notebooks/presentation/ in VS Code/Jupyter and
select this Python environment. The experiment walkthroughs are under
notebooks/experiments/. All relative paths are resolved from the project root.

## Web app and CLI

```powershell
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
python cli.py --list-configs
```

Open http://127.0.0.1:8501/. The web app shows exactly three choices:

| Name | Pipeline |
|---|---|
| llm_hybrid_gemini_broad10 | Run 1: ten passages, cutoff 0.50, complete-clause Gemini evidence |
| llm_hybrid_gemini_recovery20_31 | Run 2: Run 1 plus conditional twenty-passage recovery at 0.45 |
| bm25_baseline | Original lexical baseline |

```powershell
$question = "Consider the Wireless Content License Agreement between Fox Mobile Entertainment and Glu Mobile; What is the expiration date of this contract?"
python cli.py "$question" --config llm_hybrid_gemini_broad10 --k 5
python cli.py "$question" --config llm_hybrid_gemini_recovery20_31 --k 5 --json
python cli.py "$question" --config bm25_baseline --k 5
python cli.py --list-configs --all-configs
```

The default question is cached. The interfaces do not call hosted models,
load a secret for replay, or spend API quota. An unknown LLM request fails with
a cache-missing message. The original baseline can retrieve arbitrary questions
locally. Historical runnable configurations remain accessible by explicit
--config; --all-configs lists them without crowding the main interface.
Returned matches are evidence for review, not a guarantee of answerability.

## Train evaluation and self-improvement loop

```powershell
python manage.py evaluate_config --config bm25_baseline
python manage.py run_recall_recovery --stage broad10
python manage.py run_recall_recovery --stage recovery20_31
python manage.py improve --replay
python manage.py improve --demo --steps 5
python -m pytest -q
```

The generic evaluator writes a separate manual train result and does not edit
historical logs. The two recovery commands evaluate completed caches only.
The loop demo copies train/corpus inputs into an isolated campaign, evaluates,
diagnoses errors, proposes an untried config, applies acceptance checks and
logs each step. It never copies test.json. The original main campaign is
preserved and refuses new core proposals after the hosted/local phase.
The five-step loop demo takes roughly a minute on the measured machine;
cached final-pipeline train evaluation takes tens of seconds. Model/index
startup and network pacing are separate from reported per-query latency.

Explicit generation commands are separate from presentation/evaluation:

```powershell
python manage.py run_recall_recovery --stage broad10 --prepare
python manage.py run_recall_recovery --stage broad10 --fill --max-new 160 --pause 5
python manage.py run_recall_recovery --stage recovery20 --prepare
python manage.py run_recall_recovery --stage recovery20 --fill --max-new 163 --pause 5
```

See docs/LLM_SETUP.md for the ignored key location, pinned local models and
cache behaviour. Never commit keys. Gemini outputs, usage, model versions,
validation failures and exact inputs are cached before continuing. Inputs
contain public contract text and questions; gold answers and the original
assignment PDF are not sent. Provider failures stop generation. Invalid model
outputs retain the declared fallback instead of being silently regenerated.

## Frozen held-out evaluation: three configurations only

Quota amendment: Run 1 uses Gemini 3.5. Run 2 reuses that first stage and
uses Gemini 3.1 for recovery. Its original all-3.5 version remains in the
experiment history. The provider change was user-requested before test scores
were viewed and has a matching train evaluation; see
evaluation/PROTOCOL_AMENDMENT_31.json.

The ten presentation versions are not ten held-out runs. Only Run 1, Run 2 and
baseline are selected, using train results. Settings and code are frozen before
held-out generation. Do not change them after viewing test outcomes.

```powershell
python manage.py final_test
python manage.py final_test --freeze
python manage.py final_test --model broad10 --prepare
python manage.py final_test --model broad10 --fill --max-new 61 --pause 5
python manage.py final_test --model recovery20 --prepare
python manage.py final_test --model recovery20 --fill --max-new 61 --pause 5
python manage.py final_test --evaluate --model all
```

Run --freeze once; it deliberately refuses to replace an existing freeze.
Prepare/fill broad10 before recovery20. Run 2 reuses supported first-stage
answers and prepares only recovery inputs. Both final evaluations still cover
all 54 answerable and seven negative test questions. The baseline needs no API.
The --evaluate action is cache-only, preflights cache completeness, validates
source offsets and records every complete or partial attempt in
evaluation/test_runs.jsonl. Repeating evaluation requires explicit
--allow-repeat and increases the recorded count. For presentation, read the
saved results rather than re-evaluating. Figures and limitations belong in
REPORT.md; final result files live under results/final_test/.

## Reproduce reported numbers without model calls

Open `notebooks/presentation/FINAL_TEST_RESULTS.ipynb` and run all cells. It
loads saved predictions, recomputes both metric conventions and abstention,
and checks them against the recorded results. It does not run retrieval,
Gemini or a new pipeline evaluation. Public data must first be prepared with
`python manage.py prepare_data`.

The held-out generation/evaluation commands above document the completed
original execution; they are not required just to view or audit scores. The
freeze is intentionally environment/input specific. The saved-prediction
notebook is the portable zero-API reproduction path. The authoritative ledger
records one original evaluation attempt for each of three configurations.

## Where everything lives

| Folder/file | Purpose |
|---|---|
| app.py, cli.py, manage.py | Web, search CLI and command launcher |
| src/ | Shared retrieval, generation, evaluation and presentation helpers |
| scripts/ | Explicit preparation/evaluation/loop commands |
| notebooks/presentation/ | Ten short, runnable presentation notebooks |
| notebooks/experiments/ | Complete original implementation walkthroughs |
| experiments/iterations/ | One indexed folder per baseline/experiment stage |
| experiments/*log.jsonl | Original append-only campaign decisions |
| experiments/plans/ | Historical proposals and predeclared phase policies |
| experiments/source_snapshots/ | Source provenance before reorganisation |
| experiments/unrun/ | Clearly marked preparation that was not executed |
| configs/, llm_configs/, semantic_configs/ | Every pipeline's settings |
| evaluation/ | Frozen negatives, metric definitions, selections and summaries |
| prompts/ | Versioned prompts and synthetic examples |
| results/ | Raw predictions, metrics, events and environment metadata |
| cache/ | Checked vectors and request-keyed outputs; model weights ignored |
| tests/ | Core and interface tests; API calls are mocked |
| data/, secrets/, personal_notes/ | Local-only inputs, credentials and personal guides |

Start with evaluation/SELECTED_VERSIONS.md for the ten-stage presentation,
evaluation/ALL_MODELS_SUMMARY.md for every measured model/threshold, and
experiments/README.md for per-iteration records. REPORT.md contains results,
business trade-offs and failure analysis. Personal interview guides remain in
a single excluded folder and are not part of the submission.

## Architecture and assumptions

The baseline uses fixed-window BM25. Later lexical variants route a full
question to a contract and rank using focused clause terms. MiniLM vectors
feed an exact normalized FAISS index. The hybrid fuses ranks, then uses the
best dense cosine score as a gate; that score is not a probability. Run 1
summarises ten passages and returns exact complete-clause evidence. Run 2
reuses valid evidence or expands retrieval and tries twenty passages.
Generated summaries are displayed separately from scored source quotes.

Only the prescribed CUAD mini contracts are indexed. The frozen unanswerable
set was committed before improvements and is never edited to improve scores.
Development uses train only. Both unique-character and benchmark pairwise
overlap metrics are retained because overlapping passages affect their
interpretation; see evaluation/metrics.md. Pipeline names represent controlled
experiments, not claims that every later version improves every metric.
Direct Python/FAISS/REST integrations keep the pipeline inspectable; no
LangChain orchestration is required for these operations.

## AI assistance and submission boundary

Codex assisted with implementation, tests, diagnostics and documentation.
Gemini and local Phi-3 were used in the explicitly recorded inference
experiments; these are pretrained models, not models fine-tuned on this data.
All decisions and failures must be explainable and editable during review.
The original assignment PDF, credentials, personal notes, downloaded weights,
data and temporary runtime files are excluded from Git. Prior local history
must be audited before the private GitHub submission is created/published.

Verification checkpoint: [deliverables and checks](docs/DELIVERABLES_CHECK.md).
The private repository was created under VatsalSindhavad. Publication excludes
credentials, the source assignment PDF, personal guides, downloaded weights
and data; reproducible downloads and cached outputs are provided.

Publication history was filtered only to remove excluded personal/credential/PDF paths; chronological experiment proof and frozen negatives remain. Historical commit-ID mapping is under experiments/source_snapshots/.
