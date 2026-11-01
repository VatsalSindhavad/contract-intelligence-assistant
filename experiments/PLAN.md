# Seven-iteration development plan

The baseline is a separate reference. The working target is seven distinct
improvement iterations including LLM work. Accepted and rejected proposals both
count; replaying a proposal does not count again.

| Iteration | Scope | Status |
|---|---|---|
| 1 | BM25 common-word filtering | Complete, rejected |
| 2 | Smaller fixed character chunks | Complete, rejected |
| 3 | Reduced BM25 length normalization | Complete, gain below minimum |
| 4 | Lower BM25 term-frequency saturation | Complete, rejected |
| 5 | Stronger non-LLM change based on failure evidence | Planned; declare before measurement |
| 6 | First LLM-assisted candidate against best non-LLM system | Deferred until core quality, interfaces, and report are ready |
| 7 | Second LLM-assisted change | Deferred; proposal depends on prior evidence |

Seven is a planning target. If the non-LLM system remains weak after iteration
5, continue core improvements and revise the plan before LLM trials. Do not
loosen acceptance criteria after seeing results or claim quality based on a
completed iteration count.

Before LLM work: justify the model/provider, protect environment-based keys,
implement request-keyed output caching and cache-only evaluation, and measure
privacy implications, latency, and cost. Development stays train-only; test
comparisons follow configuration freeze for final reporting.

The main case-study table can group representative approaches. Seven
iterations do not imply seven different algorithm families. Preserve all
configurations and outcomes, including rejected changes.
