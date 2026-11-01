from copy import deepcopy
import json
from pathlib import Path

from retrieval import tokenize
from run_experiment import decide, diagnose


def sample(recall=0.2):
    return dict(answerable=dict(metrics=[dict(k=5, precision=0.1, recall=recall)],
                               answerable_false_abstention_rate=0, latency_ms=dict(p95=10)),
                negative=dict(correct_abstention_rate=0.5))


def objective():
    return json.loads((Path(__file__).resolve().parents[1] / 'experiments/objective.json').read_text())


def test_stopword_filter_preserves_negation():
    assert tokenize('The license is not transferable', True) == ['license', 'not', 'transferable']
    assert tokenize('The license', False) == ['the', 'license']


def test_accepts_recall_gain_with_guardrails():
    assert decide(sample(), sample(0.22), objective())['accepted']


def test_rejects_unchanged_recall():
    assert not decide(sample(), sample(), objective())['accepted']


def test_rejects_gain_that_breaks_precision():
    candidate = deepcopy(sample(0.4))
    candidate['answerable']['metrics'][0]['precision'] = 0.08
    assert not decide(sample(), candidate, objective())['accepted']


def test_diagnosis_distinguishes_wrong_document_from_section():
    records = [dict(query_id='a', snippets=[dict(file_path='a', span=[10, 20])])]
    hits = [dict(query_id='a', hits=[dict(file_path='a', start=30, end=40)])]
    assert diagnose(records, hits) == {'right_document_wrong_section': 1}
    hits[0]['hits'][0]['file_path'] = 'b'
    assert diagnose(records, hits) == {'wrong_document': 1}
