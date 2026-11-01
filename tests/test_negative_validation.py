import json
from pathlib import Path

import pytest

from negative_validation import assign_split, evaluate_negative_train, validate_negatives
from retrieval import load_inputs


def test_split_is_deterministic_and_strips_whitespace():
    assert assign_split(' question ') == assign_split('question')


def test_reject_test_negatives():
    with pytest.raises(ValueError):
        evaluate_negative_train(None, [dict(split='test', answerable=False)])


def test_counts_both_abstentions_and_false_returns():
    class StubRetriever:
        def search(self, query, k):
            return [] if query == 'absent' else [dict(score=1)]
    records = [dict(query_id=str(i), query=q, category='example', split='train', answerable=False)
               for i, q in enumerate(['absent', 'matched'])]
    result = evaluate_negative_train(StubRetriever(), records)
    assert result['correct_abstention_rate'] == 0.5
    assert result['false_return_rate'] == 0.5


def test_frozen_set_matches_local_corpus():
    root = Path(__file__).resolve().parents[1]
    if not (root / 'data/prepared/manifest.json').exists():
        pytest.skip('Prepare data to run corpus validation.')
    _, documents, _ = load_inputs(root)
    records, frozen = validate_negatives(root, documents)
    assert len(records) == frozen['question_count'] == 30


def test_detects_edited_query_set(tmp_path):
    folder = tmp_path / 'evaluation'
    folder.mkdir()
    (folder / 'unanswerable.json').write_text('[]', encoding='utf-8')
    (folder / 'frozen_manifest.json').write_text(json.dumps(dict(query_set_sha256='wrong')), encoding='utf-8')
    with pytest.raises(ValueError, match='modified'):
        validate_negatives(tmp_path, {})
