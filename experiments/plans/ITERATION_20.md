# Iteration 20: rerank the user-selected hybrid

Reference: hybrid_bm25_minilm_rrf_abstention, retaining its 0.55 dense cosine
gate unchanged. Reorder its top 20 fused candidates with local pretrained
cross-encoder/ms-marco-MiniLM-L6-v2, revision
233902d25c440f23af6f7d6e94d2946bac0bee0a. Score the original full question
and original source passages; no LLM, gold source routing or fine-tuning.
Return the highest scoring k original source spans. Raw cross-encoder logits
are ranking scores, not calibrated probabilities. Add no new score threshold
in this experiment, isolating reranking while preserving upstream abstention.

Before measurement: require unique recall@5 gain at least 0.01 against the
chosen hybrid, precision at least 95% of reference, false answerable abstention
at most 5%, and correct negative abstention no worse. Report both overlap
conventions, hit rate, first-use versus cache latency and truncation at 512
pair tokens. Quality and operational latency remain separate: flag first-use
p95 above max(50 ms, twice reference p95). Evaluate all 140 answerable and
23 negative train questions. Test remains untouched.

Exact request identities, source candidates, logits, pair lengths and timing
are cached. Default evaluator and interfaces replay only; explicit --fill
permits local inference for missing entries. Download public model weights
once; no contract text or questions leave the machine. No invalid output
fallback or threshold tuning is introduced. Prior prompts/configs remain intact.
