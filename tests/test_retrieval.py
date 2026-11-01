import pytest

from retrieval import BM25Retriever, benchmark_character_metrics, character_metrics, evaluate_train, make_chunks


def test_chunks_preserve_offsets_and_cover_document():
    text = 'A\nβ contract ' * 12
    chunks = make_chunks({'a': text}, size=23, overlap=7)
    covered = set()
    for chunk in chunks:
        assert chunk['text'] == text[chunk['start']:chunk['end']]
        covered.update(range(chunk['start'], chunk['end']))
    assert covered == set(range(len(text)))


def test_invalid_overlap():
    with pytest.raises(ValueError):
        make_chunks({'a': 'abc'}, size=2, overlap=2)


def test_overlap_is_counted_once():
    predicted = [dict(file_path='a', start=0, end=10), dict(file_path='a', start=5, end=15)]
    gold = [dict(file_path='a', span=[5, 10]), dict(file_path='a', span=[7, 12])]
    assert character_metrics(predicted, gold) == dict(precision=7 / 15, recall=1.0, hit=1)


def test_wrong_document_is_not_a_match():
    assert character_metrics([dict(file_path='b', start=0, end=10)],
                             [dict(file_path='a', span=[0, 10])])['recall'] == 0


def test_empty_retrieval():
    assert character_metrics([], [dict(file_path='a', span=[0, 10])]) == dict(precision=0, recall=0, hit=0)


def test_retrieval_and_unknown_query():
    config = dict(chunk_size=100, chunk_overlap=0, k1=1.5, b=0.75, min_score=0)
    retriever = BM25Retriever({'a': 'sublicensing permission', 'b': 'payment terms',
                              'c': 'termination notice'}, config)
    assert retriever.search('sublicensing')[0]['file_path'] == 'a'
    assert retriever.search('unseenword') == []
    assert retriever.search('') == []


def test_development_rejects_test_records():
    with pytest.raises(ValueError):
        evaluate_train(None, [dict(split='test')], [1])


def test_benchmark_overlap_convention_is_explicit():
    predicted = [dict(file_path='a', start=0, end=10), dict(file_path='a', start=5, end=15)]
    gold = [dict(file_path='a', span=[5, 12])]
    result = benchmark_character_metrics(predicted, gold)
    assert result == dict(benchmark_precision=12 / 20, benchmark_recall=12 / 7)
    assert character_metrics(predicted, gold)['recall'] == 1


def test_metric_conventions_agree_without_overlap():
    predicted = [dict(file_path='a', start=0, end=10), dict(file_path='b', start=0, end=10)]
    gold = [dict(file_path='a', span=[5, 15])]
    union, benchmark = character_metrics(predicted, gold), benchmark_character_metrics(predicted, gold)
    assert benchmark['benchmark_precision'] == union['precision'] == 0.25
    assert benchmark['benchmark_recall'] == union['recall'] == 0.5


def test_benchmark_empty_and_wrong_source():
    gold = [dict(file_path='a', span=[0, 10])]
    assert benchmark_character_metrics([], gold) == dict(benchmark_precision=0, benchmark_recall=0)
    assert benchmark_character_metrics([dict(file_path='b', start=0, end=10)], gold) == dict(benchmark_precision=0, benchmark_recall=0)


def test_train_evaluation_reports_both_conventions():
    class Stub:
        def search(self, query, k):
            return [dict(file_path='a', start=0, end=10), dict(file_path='a', start=5, end=15)][:k]
    records = [dict(query_id='a', query='example', split='train', snippets=[dict(file_path='a', span=[5, 12])])]
    result = evaluate_train(Stub(), records, [1, 2])
    metrics = result['metrics'][1]
    assert metrics['recall'] == 1
    assert metrics['benchmark_recall'] == 12 / 7
