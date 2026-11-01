# Evaluation report — development draft

## Current status

The current system is a local BM25 passage retriever. Three attempted improvements were rejected; the original baseline remains selected. This report contains train results only. Final model selection, required interfaces, final test evaluation, and the final case-study comparison are not complete. Test evaluation runs so far: **0**. No headline test result is available.

## System design

Contracts are read as UTF-8 text with universal newline conversion. The baseline creates 1,000-character windows with 200-character overlap, tokenizes lowercase word sequences, and uses BM25Okapi (k1=1.5, b=0.75). Search ranks all indexed passages and returns exact original text, file paths, and half-open character offsets. Only positive scores are returned; this threshold has not been calibrated. No answer labels or gold document filters enter inference.

## LLM use

No LLM is part of this pipeline. We first establish measurable local retrieval. A later LLM comparison is planned only after the core works, with cached outputs, protected credentials, and explicit cost/latency/privacy analysis.

## Evaluation setup

The prescribed mini selection contains 194 CUAD questions over 29 contracts, with 272 validated answer spans. The fixed split yields 140 answerable train and 54 answerable test questions. The separately frozen synthetic negative set has 23 train and 7 test questions. It was committed at `52fc955` before improvement experiments. All tuning and diagnostics use train. Shared corpus documents can occur across query splits under this setup; the held-out unit is the question, not the contract.

We report character metrics at k=1,3,5,10 and both abstention directions. The development objective uses union-of-intervals character coverage. The authors' reference scorer sums pairwise passage overlaps; overlapping chunks can inflate its recall beyond one. Both are retained explicitly in `evaluation/metric_audit.json`; see `evaluation/metrics.md`. Earlier decisions remain based on the original declared unique-character objective. These metrics do not measure legal reasoning or answer generation.

## Train comparison

All rows below use the same 140 answerable train questions. Precision and recall are macro means. These are model configurations, not three different algorithm families.

| Configuration | Unique precision@5 | Unique recall@5 | Reference precision@5 | Reference recall@5 | Decision |
|---|---:|---:|---:|---:|---|
| baseline | 1.74% | 18.16% | 1.76% | 19.24% | Selected baseline |
| stopwords | 1.61% | 15.89% | 1.66% | 17.37% | Rejected |
| smaller_chunks | 0.78% | 4.09% | 0.71% | 4.09% | Rejected |
| lower_length_normalization | 1.79% | 18.82% | 1.80% | 19.90% | Rejected: gain below minimum |

All four configurations falsely returned passages for all 23 train negatives (0/23 correct abstentions). All returned passages for all 140 answerable train questions (0/140 false abstentions). Returning something therefore cannot be interpreted as knowing an answer exists.

## Iteration history

The primary objective is at least a 1 percentage-point gain in unique-character recall@5. Guardrails retain at least 95% of reference precision, limit answerable false-abstention increase to 2 points, negative correct-abstention loss to 5 points, and p95 latency to max(50 ms, twice the reference). The baseline's zero negative success makes that guardrail initially weak. These are engineering tolerances, not validated production criteria.

1. **Common-word filtering:** Codex proposed removing a fixed function-word list after observing wrong-section retrieval. Recall@5 fell from 18.16% to 15.89%; precision also fell. Rejected.
2. **Smaller chunks:** the diagnostic rule selected 500-character windows, retaining 200 overlap and other baseline parameters. Recall@5 fell to 4.09%; precision also fell. Rejected.

`python improve.py` evaluates the current configuration, diagnoses errors, chooses an untried catalog proposal based on failure counts, evaluates it, accepts/rejects it, and persists the selection for the next command. It runs one step by default. The full history spans `experiments/log.jsonl` and `experiments/loop_log.jsonl`. At least two more distinct iterations are required.

3. **Less length normalization:** the loop selected b=0.30 with all other baseline settings unchanged. Unique recall@5 improved to 18.82% and precision@5 to 1.79%. The 0.66-point recall gain missed the predeclared 1-point minimum, so the candidate was rejected despite the small gain.

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

The first two changes reduced clause coverage. The third improved it modestly but failed the declared minimum gain. None met the adoption criteria, so the baseline remains selected. All current approaches run locally without per-query model API fees; compute and maintenance are still costs. Local retrieval avoids sending query/contract text to a hosted inference provider, but that alone does not establish enterprise privacy compliance. Current false returns and low recall make this a development prototype, unsuitable for autonomous legal decisions. A final comparison must include measured quality, abstention, representative latency, deployment/privacy implications, and cost assumptions.

## Limitations and remaining work

- Complete at least two further distinct improvement iterations and improve answerability.
- Add and verify the shared web app and user-facing search CLI.
- Freeze final configurations before test evaluation; append an actual run record for every test execution and report the count.
- Report baseline versus final train/test results with query counts and discuss the gap.
- Refresh error analysis for the final configuration and include at least ten concrete failures.
- The negative set is synthetic, topic-repetitive, and not legally expert-labeled; seven test negatives provide a very imprecise estimate. Do not edit the frozen set to suit outcomes.
- Cross-references, definitions, redactions, and missing external schedules can change interpretation and remain unresolved.
- Reproduce setup in a clean environment, verify commands and timings, and finalize README instructions.
- No final 4–5-approach business comparison is claimed yet. Two parameter changes are not proof of distinct retrieval methods.

## Reproduction sources

- Baseline: `results/bm25_baseline/20261101T020109139330Z`.
- Abstention: `results/bm25_abstention/20261101T020853204883Z`.
- Iteration outputs: `results/iteration_01/`, `results/iteration_02/`, and `results/iteration_03/`.
- Reference-metric supplement: `evaluation/metric_audit.json` (scores saved train predictions; no model calls).
- Tests: `python -m pytest -q`. Setup and notebook order are in README.
- Final test reproduction commands and measured final-run timings: pending; no test execution has occurred.
