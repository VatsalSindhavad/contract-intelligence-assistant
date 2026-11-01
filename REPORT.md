# Evaluation report — development draft

## Current status

The ten-trial BM25/LLM phase and pure-semantic iteration 11 are complete. Three non-LLM improvements are accepted; Both Gemini and Phi-3 improve retrieval but fail the first-use latency guardrail. The selected model combines document routing, focused clause search with fallback, and English Snowball stemming. The shared CLI and Streamlit app are implemented and verified. Final test evaluation and the complete case-study report remain pending. Test evaluation runs so far: **0**.

## System design

The original baseline uses lowercase word tokenization, BM25Okapi (k1=1.5, b=0.75), 1,000-character windows with 200 overlap, and a positive-score rule. It searches all 29 contracts and returns exact text, paths, and half-open offsets.

Accepted iteration 5 uses the highest full-query BM25 passage to infer a document, then ranks that document's passages using the question after the semicolon in `Consider ...; question`. Accepted iteration 7 filters common words and generic contract-question scaffolding from that clause query, falling back to the unfiltered clause query if no focused match exceeds the threshold. Indexed text, document routing, and chunk settings are unchanged. No gold source ID, answer span, or negative label enters inference. Plain unformatted questions retain baseline global search; format dependence is a limitation.

Iteration 8 additionally stems indexed and query tokens with NLTK English Snowball, after clause cleanup. Stored evidence remains exact. This normalizes inflections without resolving all semantic synonyms.

## LLM use

Gemini query expansion is implemented, cached, and scored in iteration 9. Three accepted non-LLM improvements now provide a comparison reference. Before later LLM work: finish the working core, choose/justify the model, protect environment-based keys, cache request-keyed outputs, enable cache-only evaluation, and measure cost, latency, and privacy implications. FAISS/dense and hybrid retrieval are not implemented or assumed to improve quality.

## Evaluation setup

The prescribed mini subset has 194 CUAD queries over 29 contracts, with 272 exact answer spans verified. Fixed splits contain 140/54 answerable and 23/7 unanswerable train/test questions. The synthetic negative set was frozen at commit `52fc955` before improvement. Queries, not documents, are held out; the indexed corpus is shared as prescribed. Development is train-only.

Character metrics are macro means at k=1,3,5,10. Our declared objective uses unique-character interval coverage; the authors' reference scorer sums pairwise passage overlaps. The latter can count repeated coverage more than once. Both are retained in results and `evaluation/metric_audit.json`. See `evaluation/metrics.md`. They are not answer-generation accuracy or legal correctness.

## Train comparison

All quality rows use 140 answerable train questions. The following are BM25 pipeline variants, not separate algorithm families.

| Configuration | Unique precision@5 | Unique recall@5 | Reference precision@5 | Reference recall@5 | Decision |
|---|---:|---:|---:|---:|---|
| Baseline | 1.74% | 18.16% | 1.76% | 19.24% | Original reference |
| stopwords | 1.61% | 15.89% | 1.66% | 17.37% | Rejected |
| smaller_chunks | 0.78% | 4.09% | 0.71% | 4.09% | Rejected |
| Length normalization | 1.79% | 18.82% | 1.80% | 19.90% | Rejected |
| Term saturation | 1.57% | 16.16% | 1.60% | 17.24% | Rejected |
| Document then clause | 5.15% | 47.12% | 5.37% | 52.11% | Accepted |
| Focused clause without fallback | 5.81% | 50.72% | 6.07% | 56.27% | Rejected |
| Focused clause with fallback | 6.28% | 53.50% | 6.51% | 59.16% | Accepted |
| Combined pipeline plus stemming | 7.88% | 67.01% | 8.38% | 76.60% | Accepted |
| Gemini query expansion + best BM25 | 8.47% | 79.10% | 8.93% | 89.58% | Quality/replay checks pass; first-use latency fails |
| Local Phi-3 query expansion + best BM25 | 8.07% | 70.75% | 8.51% | 80.07% | Quality/replay checks pass; first-use latency fails |
| Pure MiniLM + FAISS | 4.03% | 35.75% | 4.19% | 38.90% | Rejected against best BM25; beats original baseline |

## Abstention and speed

The baseline, accepted iteration 5, and accepted iteration 7 all have 0/140 false abstentions on answerable train queries, but also 0/23 correct abstentions on train negatives. The intermediate iteration 6 attained 1/23 correct negative abstentions but wrongly abstained on 12/140 answerable questions and was rejected. Fallback recovers answerable-query coverage at the cost of that one negative success. Passing a guardrail relative to a weak reference does not solve answerability.

In the iteration-7 run, baseline/current/candidate p95 search latency was approximately 8.77/13.27/10.52 ms on this machine. Local timing excludes index construction and evaluation and is not a production load benchmark. These non-LLM measurements involve no model API calls; hosted usage is reported separately below.

## Iteration history and acceptance

Primary objective: gain at least 1 percentage point of unique-character recall@5 over the current accepted reference. Guardrails retain 95% of reference precision, allow at most 2 points more answerable false abstention and 5 points less negative correct abstention, and cap p95 at max(50 ms, twice reference p95). These engineering tolerances were declared before trials and have not been loosened.

1. Common-word filtering: rejected; recall and precision declined.
2. Smaller fixed chunks: rejected; recall and precision declined.
3. Lower length normalization: rejected; recall gain of 0.66 points missed the minimum.
4. Lower term saturation: rejected; recall and precision declined.
5. Separate document identification and clause ranking: accepted; recall@5 18.16% to 47.12%.
6. Focused clause terms: rejected despite 50.72% recall; 12 false answerable abstentions broke the guardrail.
7. Focused terms with zero-match fallback: accepted against iteration 5; recall@5 47.12% to 53.50%, with guardrails met.

The loop evaluates, diagnoses, selects an untried catalog proposal, measures it, accepts/rejects it, and persists the selection. The catalog was amended before iterations 5–7 with explicit proposal documents and prerequisite checks. Both historical logs are retained. The minimum five iterations is met; eight are complete and the user allows at most ten total. Do not count replays as new iterations or manufacture accepted outcomes.

8. English stemming on the combined accepted pipeline: accepted; unique recall@5 rose from 53.50% to 67.01%, precision@5 from 6.28% to 7.88%. Complete gold coverage rose from 57 to 82 questions. In this run candidate p95 was about 10.50 ms; both abstention rates remain unchanged.

## Ten concrete train failures

These examples come from saved baseline top-5 predictions. Group labels describe observed coverage. Causal explanations are hypotheses unless directly supported by offsets. Query IDs locate the full predictions and annotations.

### 1. Wrong section — `b5a0948cd3cf1a4070748a4899cab8bea0dde912b91f0f1e6cc422262c392fcb`

Consider the Service Agreement between BicycleTX Ltd and Nigel Crockett for Chief Business Officer Position; What is the governing law for this contract?

Gold source: `cuad/BICYCLETHERAPEUTICSPLC_03_10_2020-EX-10.11-SERVICE AGREEMENT.txt`. Gold ranges: [[53956, 54252]]. Retrieved ranges in that source: 0:1000, 56000:57000, 56800:57041. Unique recall@5: 0.00%.

Top result excerpt: Exhibit 10.11  DATED 26 September 2019  BicycleTX Ltd  and  Nigel Crockett  ___________________________________________________  SERVICE AGREEMENT  ________________________________

Diagnosis: the source contract is retrieved, but none of the top-five spans intersects any gold clause. Passage ranking, rather than finding the contract, failed. A lexical match is insufficient evidence of the requested provision.

### 2. Wrong section — `5aacd88644962ff51293f4cc0ae5f18f1815d9a615908bd8283a990dcf5c4569`

Consider the Service Agreement between BicycleTX Ltd and Nigel Crockett for Chief Business Officer Position; Are there any exceptions to competitive restrictions in this contract?

Gold source: `cuad/BICYCLETHERAPEUTICSPLC_03_10_2020-EX-10.11-SERVICE AGREEMENT.txt`. Gold ranges: [[33572, 34034]]. Retrieved ranges in that source: 0:1000, 56000:57000, 40800:41800. Unique recall@5: 0.00%.

Top result excerpt: Exhibit 10.11  DATED 26 September 2019  BicycleTX Ltd  and  Nigel Crockett  ___________________________________________________  SERVICE AGREEMENT  ________________________________

Diagnosis: the source contract is retrieved, but none of the top-five spans intersects any gold clause. Passage ranking, rather than finding the contract, failed. A lexical match is insufficient evidence of the requested provision.

### 3. Wrong section — `13d8e76465cd5d5ff8d880d4fcf36657d918c9f750e2aad64d336b3e99babdc2`

Consider the Service Agreement between BicycleTX Ltd and Nigel Crockett for Chief Business Officer Position; Does this contract include any right of first refusal, right of first offer, or right of first negotiation?

Gold source: `cuad/BICYCLETHERAPEUTICSPLC_03_10_2020-EX-10.11-SERVICE AGREEMENT.txt`. Gold ranges: [[6235, 6531], [6533, 7937]]. Retrieved ranges in that source: 0:1000, 56000:57000. Unique recall@5: 0.00%.

Top result excerpt: Exhibit 10.11  DATED 26 September 2019  BicycleTX Ltd  and  Nigel Crockett  ___________________________________________________  SERVICE AGREEMENT  ________________________________

Diagnosis: the source contract is retrieved, but none of the top-five spans intersects any gold clause. Passage ranking, rather than finding the contract, failed. A lexical match is insufficient evidence of the requested provision.

### 4. Wrong section — `505f5239e0ca460f383a732198b07e7d4dd7f828487adaaae04dbc49d1ae98c4`

Consider the Service Agreement between BicycleTX Ltd and Nigel Crockett for Chief Business Officer Position; How is intellectual property ownership assigned in this contract?

Gold source: `cuad/BICYCLETHERAPEUTICSPLC_03_10_2020-EX-10.11-SERVICE AGREEMENT.txt`. Gold ranges: [[44840, 45359]]. Retrieved ranges in that source: 0:1000, 56000:57000, 56800:57041. Unique recall@5: 0.00%.

Top result excerpt: Exhibit 10.11  DATED 26 September 2019  BicycleTX Ltd  and  Nigel Crockett  ___________________________________________________  SERVICE AGREEMENT  ________________________________

Diagnosis: the source contract is retrieved, but none of the top-five spans intersects any gold clause. Passage ranking, rather than finding the contract, failed. A lexical match is insufficient evidence of the requested provision.

### 5. Wrong section — `41ece44a0165f292b5f7c0cd8f4402ff9844983a576937f2ed8b13f1829a6a31`

Consider the Cooperation Agreement between HPIL ENERGYTECH Inc. and GINARES GROUP AG for Renewable Energy Projects; What is the governing law for this contract?

Gold source: `cuad/HPILHOLDING_01_07_2015-EX-99.1-COOPERATION AGREEMENT.txt`. Gold ranges: [[16867, 17117]]. Retrieved ranges in that source: 3200:4200, 0:1000, 19200:20008, 5600:6600, 13600:14600. Unique recall@5: 0.00%.

Top result excerpt: .................................................................................................................... 8 23. Entire Agreement.........................................

Diagnosis: the source contract is retrieved, but none of the top-five spans intersects any gold clause. Passage ranking, rather than finding the contract, failed. A lexical match is insufficient evidence of the requested provision.

### 6. Partial coverage — `bf000ecae1bd79c66b1d52b3f9ff4b6b45d7ced0a7d7b30ac631cea668ad353f`

Consider the Strategic Alliance Agreement between Information System Associates, Inc. and Rubicon Software Group plc; Are the licenses granted under this contract non-transferable?

Gold source: `cuad/DUOSTECHNOLOGIESGROUP,INC_04_21_2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT.txt`. Gold ranges: [[5690, 6080], [6537, 7080]]. Retrieved ranges in that source: 0:1000, 45600:46298, 6400:7400, 17600:18600, 8800:9800. Unique recall@5: 58.20%.

Top result excerpt: Exhibit 10.1    STRATEGIC ALLIANCE AGREEMENT    This Strategic Alliance Agreement (this "Agreement"), effective as of 15 April, 2009 (the "Effective Date"), is by and between Infor

Diagnosis: retrieved spans intersect the annotation but leave some gold characters uncovered. Missing coverage is visible in the ranges above; it may arise from chunk boundaries or ranking away other required passages. This is not a complete clause retrieval.

### 7. Partial coverage — `22389b42dacb7f7d34051a1c8d4a0389db11ba2c3994296821274ee72e77b01e`

Consider the Supply Agreement between Florida Chemical Company, LLC and Flotek Chemistry, LLC for Terpene Products; Does this contract include any volume restrictions?

Gold source: `cuad/FLOTEKINDUSTRIESINCCN_05_09_2019-EX-10.1-SUPPLY AGREEMENT.txt`. Gold ranges: [[958, 1076], [3210, 3809]]. Retrieved ranges in that source: 0:1000, 18400:19355, 15200:16200, 4000:5000, 16000:17000. Unique recall@5: 5.86%.

Top result excerpt: Exhibit 10.1  Information identified with "[***]" has been excluded from this exhibit because it is both not material and would likely cause competitive harm to the registrant if p

Diagnosis: retrieved spans intersect the annotation but leave some gold characters uncovered. Missing coverage is visible in the ranges above; it may arise from chunk boundaries or ranking away other required passages. This is not a complete clause retrieval.

### 8. Partial coverage — `8d29c26280a10046885b4fb8a344825d05cdfb57c7f6b215e84cfe358569228f`

Consider the Intellectual Property Agreement for COVID-19 Treatment Development between Marv Enterprises, LLC, Premier Biomedical, Inc., and Technology Health, Inc.; Does this contract include an exclusivity agreement?

Gold source: `cuad/PREMIERBIOMEDICALINC_05_14_2020-EX-10.2-INTELLECTUAL PROPERTY AGREEMENT.txt`. Gold ranges: [[3388, 4736], [12938, 13072], [14754, 15163]]. Retrieved ranges in that source: 0:1000, 13600:14600, 22400:23282, 1600:2600, 14400:15400. Unique recall@5: 21.63%.

Top result excerpt: Exhibit 10.2   INTELLECTUAL PROPERTY AGREEMENT   This Intellectual Property Agreement (this "Agreement") is entered into on May 12, 2020 ("Effective Date"), concerning the pursuits

Diagnosis: retrieved spans intersect the annotation but leave some gold characters uncovered. Missing coverage is visible in the ranges above; it may arise from chunk boundaries or ranking away other required passages. This is not a complete clause retrieval.

### 9. False return — `f03c96c14eab136aa7e9cf1879c3265c77f7c0a671b4857f2a4ea858d4c70951`

Consider the distribution agreement between NimbleCove Media and BluePeak Distribution; Does the agreement allow sublicensing to third-party platforms?

Returned source: `cuad/DUOSTECHNOLOGIESGROUP,INC_04_21_2009-EX-10.1-STRATEGIC ALLIANCE AGREEMENT.txt` at [7200, 8200), score 31.240.

Returned excerpt: e Documentation.  Rubicon shall promptly notify ISA of each such upgrade to the Rubicon Offering and the Documentation which will be available to ISA under this  Agreement.     2.4

Diagnosis: the missing agreement cannot be answered using another indexed agreement. Shared contract vocabulary still produces a positive score.

### 10. False return — `446845f6921873c1ec8c4bf3a72699bf58775e7dad5ce3382725df439ba0aa4f`

Consider the Wireless Content License Agreement between Fox Mobile Entertainment and Glu Mobile; Which clause permits training generative AI models on the licensed content?

Returned source: `cuad/GluMobileInc_20070319_S-1A_EX-10.09_436630_EX-10.09_Content License Agreement4.txt` at [0, 1000), score 67.230.

Returned excerpt: AMENDMENT NO. 3  Dated as of February 19, 2007  Reference is hereby made to that certain fully executed Wireless Content License Agreement Number 12965 dated as of December 16, 200

Diagnosis: the named contract exists but does not establish the technology-specific provision. A positive lexical score does not validate the premise of the question.

## Business interpretation

Document naming terms helped locate contracts but could distract passage ranking. Separating the tasks and focusing the clause wording increased relevant clause coverage under the same five-passage budget. The second accepted change improves both recall and precision over the first accepted reference. These measured train gains justify keeping the candidates for comparison, not deploying them as autonomous legal decision makers.

Privacy benefits are limited to local inference: queries and text are not sent to an external model provider. This alone is not enterprise privacy compliance. Compare later dense/LLM approaches using fixed query counts, both abstention directions, latency, cost assumptions, and data-transfer implications.

## Limitations and remaining work

- Web app and user search CLI are implemented using the same inference service; 46 tests pass and all nine saved configurations passed a source-offset smoke check. Run commands are documented in README.md.
- Improve or clearly disclose weak answerability; current selected model returns text for every train negative.
- Structured-query parsing and single inferred-document routing can fail on other phrasing or an incorrect source match.
- Freeze comparison configurations before final test evaluation and persist a real test-run counter. Report train/test gaps and counts.
- Refresh this baseline error analysis for the final selected model and include at least ten diagnosed failures.
- Negative labels are synthetic, repetitive, and not expert legal annotations; seven test negatives give an imprecise estimate. Do not edit the frozen set.
- Definitions, cross-references, redactions, and missing schedules remain unresolved.
- Verify a clean setup and final timings; finish README run instructions and private submission checks.
- Use the remaining budget only for explicit measured proposals; later LLM outputs require caching and secret protection.

## Reproduction

Run notebooks 01–03 to prepare/measure the baseline. Historical trial notebooks replay or review earlier work; `python improve.py` advances one new trial. Notebook 08 reviews trials 5–7; notebook 09 reviews the combined stemmed model. Both run saved configurations without advancing the loop. Accepted config files are in `configs/` and every accepted/rejected snapshot remains under its result directory.

Results: `results/bm25_baseline/`, `results/bm25_abstention/`, and `results/iteration_01/` through `results/iteration_08/`. Complete logs: `experiments/log.jsonl` and `experiments/loop_log.jsonl`. Tests: `python -m pytest -q`. Final test reproduction commands are pending; zero test executions have occurred.

## Interface checkpoint

`python cli.py "question"` and `python -m streamlit run app.py` share
`search_service.py`. They load only the verified corpus and selected saved
configuration, not benchmark question labels. The app offers configuration
selection, exact passage text, sources/offsets, scores, and JSON export. The
CLI supports configuration selection, k, and JSON output. Empty/invalid input
and no-match paths were tested. A local HTTP health check and nine-configuration
smoke test are saved in `results/interface_smoke.json`. Zero-match behavior
must not be mistaken for calibrated abstention on realistic negative questions.

Hosted model integration is implemented and cached; local Phi-3 is also complete.
Both use the same retrieval-assistance task; see
`experiments/LLM_PLAN.md`. No new benchmark iteration was consumed by interface
work, and no test performance was measured.

## Runnable versions and comparison procedure

All nine versions are preserved as configuration files and can be selected in
both interfaces. Rejected means the train experiment failed our acceptance
criteria; it does not mean the implementation is unavailable.

| Configuration name | Trial | Status |
|---|---:|---|
| `bm25_baseline` | Baseline | Original comparison reference |
| `bm25_stopwords` | 1 | Rejected |
| `bm25_chunks_500` | 2 | Rejected |
| `bm25_b_030` | 3 | Rejected |
| `bm25_k1_080` | 4 | Rejected |
| **✓ `bm25_document_then_clause`** | 5 | Accepted |
| `bm25_focused_clause` | 6 | Rejected |
| **✓ `bm25_focused_clause_fallback`** | 7 | Accepted |
| **✓ `bm25_focused_stemmed`** | 8 | Accepted; current default |

From the project folder, use the same question and k to inspect versions:

```powershell
python cli.py --list-configs
$question = "Consider the Wireless Content License Agreement between Fox Mobile Entertainment and Glu Mobile; What is the expiration date of this contract?"
python cli.py $question --config bm25_baseline --k 5 --json
python cli.py $question --config bm25_focused_stemmed --k 5 --json
```

Substitute any configuration name from the table. For the web interface, run
`python -m streamlit run app.py`, select the same configuration/question/k, and
click Search. Full setup and command options are in README.md.
The nine-configuration source-offset smoke check is recorded in
`results/interface_smoke.json`. Single-question inspection is a walkthrough,
not a replacement for the aggregate evaluation above and not a new iteration.

**✓ Better than baseline** marks accepted train improvements that passed all
acceptance checks; held-out test performance remains unmeasured. The CLI list
and web selector use the same label. Small gains or candidates failing a
guardrail retain explanatory labels instead. Configuration command names are
unchanged; omit the display labels when passing `--config`.

## Hosted LLM iteration 9

Gemini 3.5 Flash-Lite received 53 unique train clause questions with the fixed
query-expansion prompt. Contract descriptions, parties, original document text,
gold spans, and the private assignment PDF were not sent. These inputs were
explicitly reviewed and approved before external transmission. This is input
minimization by query structure, not general-purpose name redaction.

All 53 outputs passed schema/length/numeric checks. The first batch hit HTTP
429; spacing and retry preserved the failed attempt and reused valid caches.
Successful unique responses consumed 8,257 input and 1,284 output tokens
(9,541 total). Actual charge is account-dependent and not inferred here.

On 140 answerable train queries, unique-character recall@5 improved from
67.01% to 79.10%, precision from 7.88% to 8.47%, and complete coverage from
82 to 95 questions. Correct negative abstention remains 0/23 and answerable
false abstention remains 0/140. Estimated first-use p95 is 2.58 seconds;
cache/retrieval p95 is 15.95 ms. The 50-ms-floor operational latency guardrail
fails on first use; all quality/replay checks pass. No threshold was relaxed
and the accepted non-LLM model remains selected. These are train results, not
proof of generalization or legal answer quality.

`notebooks/10_gemini_bm25.ipynb` and the `llm_gemini_rewrite` interface option
are cache-only. The presentation path was checked with network and credential
access disabled. See README.md and the question inputs in the cache records.
Complete results: `results/iteration_09/`; decisions and latency modes:
`experiments/llm_log.jsonl`. Replays remain the same proposal, not new iterations.
At the end of the hosted checkpoint Phi-3 had not run; its completed comparison is documented below. Test evaluation count remains zero.

## Local Phi-3 iteration 10 and hosted comparison

The installed Phi-3 Mini 3.8B Q4_0 model was verified by digest and Ollama
runtime before generation. The same 53 unique train clause questions, prompt,
output schema, 256-token cap, validators, original-query retention, and BM25
reference were used. Local seed was 42 and context length 2,048 tokens. Inputs
were short enough for that context; tokenizers and compute still differ.

Phi-3 produced 47 valid outputs and six invalid outputs. Invalid responses
were retained and used the original query; they were not regenerated to hide
failures. Unique-character recall@5 is 70.75% versus the reference's 67.01%
and Gemini's 79.10%. Precision is 8.07% versus 7.88% and 8.47% respectively.
Complete gold coverage is 84/140 versus 82/140 for non-LLM and 95/140 for
Gemini. Both LLMs still have 0/23 correct negative abstentions and 0/140
answerable false abstentions.

Estimated local first-use median/p95 is 0.68/3.74 seconds; replay p95 is about
15.20 ms. Gemini's corresponding median/p95 is 1.46/2.58 seconds and replay
p95 15.95 ms. Local median was lower, but its tail was slower. The first local
call took 52.08 seconds including 36.84 seconds loading; other calls reused
the resident model. The runtime snapshot reports about 3 GB VRAM allocation
on a machine with about 16 GB RAM. No hosted fee applies to local execution,
but hardware/electricity costs are not estimated. Token counts from different
tokenizers should not be treated as equal units of useful work.

Both LLMs pass quality/replay checks and fail the unchanged operational
first-use latency ceiling. Gemini is the stronger train-quality candidate;
Phi-3 provides local execution with lower transfer exposure but more invalid
outputs. This does not establish an overall winner before held-out evaluation
and deployment-budget decisions. The accepted stemmed BM25 stays default.

All 106 unique model-output records are cached. Both LLM interface options
were checked with network and credential access disabled. Notebook 11 reviews
the hosted/local comparison. Ten distinct iterations are complete; further
proposal work is outside the current budget. Final configuration freeze,
held-out evaluation/run counting, final error analysis, and reproduction
remain required. Test evaluation count is still zero.

## Pure semantic iteration 11

The first dense-only comparison uses the locally available Apache-2.0
all-MiniLM-L6-v2 model at revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41.
Normalized 384-dimensional vectors are searched by exact FAISS IndexFlatIP.
The original full query searches globally across all 1,522 chunks. No BM25
routing/candidates/fusion, LLM, or gold document filter is used. Original
1,000-character chunks with 200 overlap and source offsets are unchanged.
This compares complete pipelines: the tuned BM25 route and global dense
baseline have different document-selection policies, not just different scores.

On 140 answerable train questions, unique-character recall@5 is 35.75% and
precision@5 4.03%. This exceeds the original BM25 baseline (18.16%/1.74%) but
not the accepted tuned BM25 pipeline (67.01%/7.88%). Both the recall-gain and
precision guardrails fail against that reference, so the dense baseline is
not selected as a replacement. Complete coverage is 33/140, partial 32/140,
and zero overlap 75/140. Correct negative abstention is 0/23 and false
answerable abstention is 0/140. The initial positive-cosine threshold is untuned.

The model's default 256-wordpiece limit truncates 105/1,522 source chunks;
no train queries exceed the limit. Returned text/offsets still cover the
original full chunks, including tails that may not have been encoded. This
can limit relevance, but its causal contribution is not isolated here. Do
not generalize this one basic, general-purpose model to all semantic retrieval.

Initial model/vector/index build took about 76.51 seconds on CPU (four PyTorch
threads). Estimated first-use query median/p95 is 10.17/12.97 ms. Document/query
vectors are cached with exact model/config/library identities and checksums.
No hosted API or model download was used; the model was already present and
runtime loading is explicitly offline. Model weights remain an external setup
dependency, not a Git artifact.

See notebook 12, semantic_configs/minilm.json, dense_retrieval.py,
evaluate_dense.py, results/iteration_11/, and experiments/semantic_log.jsonl.
The CLI/web choice is dense_minilm_faiss. Kanon and dense+Gemini trials remain
planned; final test performance is still unmeasured. Hybrid is still deferred.

The notebook/web runtime required an isolated local embedding worker to avoid
a Windows PyTorch DLL initialization issue; the standalone train benchmark
used the same pinned CPU encoder directly. The verified presentation query
replays saved vectors with no model loading or external calls. This runtime
fix does not constitute another model experiment.

## Local precision pilot (trial 12; separate cohort)

Semantic work was paused at the user's request. This is a new post-retrieval
candidate on top of the preserved local Phi-3 query-expansion/BM25 pipeline,
not a change to any earlier model. The exact instruction-only prompt is in
prompts/extract_answer_v1.txt; no worked example was included. The request
contains only the question and retrieved passages. Gold labels/answers/offsets
are used only after inference for scoring.

Ten answerable and five negative train records were fixed by query-hash order
before generation. This small pilot is not directly comparable to the 140/23
full-train tables. It intentionally tests the user's concise one-line answer
idea while requiring an exact source quote so retrieval offsets remain valid.

| Same pilot cohort | Reference local rewrite + BM25 | Exact-excerpt candidate |
|---|---:|---:|
| Answerable queries | 10 | 10 |
| Unique precision@5 | 3.06% | 6.00% |
| Unique recall@5 | 45.88% | 35.40% |
| Reference precision@5 | 3.38% | 6.17% |
| Reference recall@5 | 54.57% | 39.09% |
| Correct negative abstentions | 0/5 | 2/5 |
| False answerable abstentions | 0/10 | 0/10 |

The new phase's policy was declared before measurement: at least a one-point
precision gain, at most a two-point recall loss, and protected abstention.
Precision rose 2.94 points, but recall fell 10.48 points, so the quality gate
failed. The existing operational latency check also failed. First-use timing
includes both the upstream local rewrite and extraction; a cached replay was
rerun to correct timing accounting, with identical quality scores. Both saved
run records remain the same proposal, not two new experiments.

Nine of fifteen outputs passed source/schema validation, including two explicit
no-answer responses. Six were invalid: five quotes were not exact substrings
of the cited passage, and one JSON string was truncated/unparseable. Invalid
outputs retain the original candidates rather than removing difficult queries.
Every returned excerpt was checked against the original document slice.
Validity does not mean the quote necessarily answers the question correctly.

Returned characters averaged 2,638 versus 4,980.8 input characters on the ten
answerable queries; fallback passages explain why not every result is short.
Four zero-overlap reference failures became six after extraction. A concise
fact can omit required clause evidence or select the wrong text; shorter output
alone is not successful retrieval. The exact-copy constraint also exposed the
small model's quoting/format-following limitations.

The candidate is not adopted. There is no full-train expansion, Gemini
extraction, or semantic continuation yet. Stop and review possible output/
prompt redesign rather than spend API quota. Possible future hypotheses are
selecting source sentence IDs instead of copying or asking for the complete
answering clause with qualifiers; these are suggestions, not measured trials.

All 15 local request/response records are cached in cache/local_extractions/.
See notebook 13, experiments/precision_log.jsonl, and
results/iteration_12_precision_pilot/. The original pipelines, prompts, and
caches remain available. Test performance remains unmeasured.
