# Proposal declared before iteration 7

Iteration 6 improved unique-character recall@5 from 47.12% to 50.72% but wrongly
abstained on 12/140 answerable train questions, exceeding the unchanged
2-percentage-point guardrail. It was rejected and the routed model retained.

Propose focused clause matching with an inference-time zero-match fallback.
Use the focused clause tokens from iteration 6; if no passage in the inferred
contract exceeds the existing score threshold, rerun the accepted unfiltered
clause query in that same contract. Document routing and index stay unchanged.
No answer label or gold source enters this choice.

Both cleanup and its fallback are enabled together because iteration 6 was
rejected: the accepted reference still has neither. This is a single revised
query policy. The candidate is compared with that accepted reference, using
the same numeric objective and guardrails. Negative correct abstention may
regress from iteration 6's 1/23 to the accepted reference's 0/23; report it.
Fallback favors recall and must not be described as proof of answerability.

Commit the proposal before measuring it. Keep test performance untouched.
