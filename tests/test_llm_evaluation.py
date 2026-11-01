from evaluate_llm import first_use_decision
from improve import read_json
from pathlib import Path


def test_model_generation_latency_cannot_be_hidden_by_cache_replay():
    def sample(recall):
        return dict(answerable=dict(metrics=[dict(k=5,precision=0.1,recall=recall)],
                                   answerable_false_abstention_rate=0,latency_ms=dict(p95=10)),
                    negative=dict(correct_abstention_rate=0.5))
    reference, candidate = sample(0.2), sample(0.3)
    events = [dict(original_model_call_ms=1500, cache_retrieval_ms=10)]
    objective = read_json(Path(__file__).resolve().parents[1]/'experiments/objective.json')
    decision, timings = first_use_decision(reference, candidate, events, objective)
    assert decision['checks']['recall_gain']
    assert not decision['checks']['latency']
    assert not decision['accepted']
    assert timings['p95'] == 1510
