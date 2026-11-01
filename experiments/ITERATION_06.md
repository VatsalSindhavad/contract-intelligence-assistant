# Proposal declared before iteration 6

Iteration 5 was accepted: unique-character recall@5 rose from 18.16% to 47.12%,
and precision@5 from 1.74% to 5.15%. The candidate still misses all answer
characters in 62 train questions. Both abstention directions remain unchanged.

Hypothesis: generic question terms dilute the clause ranking. For the routed
query only, remove common function words and generic words such as contract,
agreement, include, and clause. Keep document routing and indexed text unchanged.
Preserve negation and qualifiers such as not, no, without, and exceptions. If
filtering removes every token, use the unfiltered tokens instead.

This changes only `clause_query_cleanup`; it is a new proposal for the accepted
routed pipeline, not a replay of iteration 1's corpus-wide stopword filtering.
The proposal requires routed mode. Keep all other settings and numerical
acceptance rules unchanged. Compare against the accepted iteration 5 and the
original baseline. Declare and commit this catalog amendment before measurement.

These query rules may be specific to the benchmark's phrasing. A train gain
does not establish generalization. No LLM or optional stretch feature is used.
