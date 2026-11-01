# Character metric conventions

Every character is identified by source document and position. Intervals are
half-open Python string ranges. Metrics are averaged equally over questions.
Empty retrieval has precision and recall zero.

`precision` and `recall` merge overlapping intervals in each document before
counting intersections. This is the unique-character convention used to declare
the experiment objective and make decisions in iterations 1 and 2. It stays
unchanged so earlier decisions are not reinterpreted after seeing outcomes.

`benchmark_precision` and `benchmark_recall` follow the authors' reference
scorer: sum pairwise retrieved/gold overlaps, divide by the sum of retrieved
passage lengths or gold span lengths respectively. The benchmark gold spans
are disjoint. Repeated coverage in overlapping retrieved chunks can make this
recall exceed one; this is why unique-character recall remains our objective.
Do not clip the reference score or present it as unique clause coverage.

The conventions agree when neither input has overlapping intervals. Our
overlapping-chunk pipeline requires reporting the difference explicitly.
Historical result files remain unchanged; `metric_audit.json` supplements
their saved train predictions with reference-compatible metrics. No retrieval
or test evaluation is performed by this audit.

Primary sources checked during the audit:

- https://arxiv.org/abs/2408.10343
- https://github.com/zeroentropy-ai/legalbenchrag/blob/master/legalbenchrag/run_benchmark.py
- https://github.com/zeroentropy-ai/legalbenchrag/blob/master/legalbenchrag/benchmark_types.py
