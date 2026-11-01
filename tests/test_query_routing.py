import numpy as np

from retrieval import BM25Retriever, clause_question, clause_tokens


def test_question_parser_preserves_plain_query_and_semicolons():
    assert clause_question('Consider the contract; What is the term; and renewal?') == 'What is the term; and renewal?'
    assert clause_question('What is the term?') is None


def stub_retriever(mode):
    retriever = object.__new__(BM25Retriever)
    retriever.config = dict(query_mode=mode, min_score=0)
    retriever.remove_stopwords = False
    retriever.chunks = [dict(file_path='a', start=0, end=10, text='intro'),
                        dict(file_path='a', start=10, end=20, text='term'),
                        dict(file_path='b', start=0, end=10, text='term')]
    class Index:
        def get_scores(self, tokens):
            return np.array([10., 2., 1.]) if 'consider' in tokens else np.array([1., 8., 20.])
    retriever.index = Index()
    return retriever


def test_route_from_query_then_rank_clause_without_gold():
    retriever = stub_retriever('document_then_clause')
    hits = retriever.search('Consider A; term', k=3)
    assert [h['text'] for h in hits] == ['term', 'intro']
    assert all(h['file_path'] == 'a' for h in hits)


def test_plain_query_uses_original_global_search():
    retriever = stub_retriever('document_then_clause')
    assert retriever.search('term')[0]['file_path'] == 'b'


def test_baseline_does_not_apply_routing():
    assert stub_retriever('full').search('Consider A; term')[0]['text'] == 'intro'


def test_cleanup_removes_scaffold_and_preserves_legal_negation():
    assert clause_tokens('Does this contract include sublicensing without consent?', True) == ['sublicensing', 'without', 'consent']
    assert clause_tokens('Is assignment not allowed?', True) == ['assignment', 'not', 'allowed']


def test_cleanup_never_silently_discards_all_terms():
    assert clause_tokens('the contract', True) == ['the', 'contract']


def test_focused_zero_match_can_fall_back_without_changing_document():
    retriever = stub_retriever('document_then_clause')
    retriever.config.update(clause_query_cleanup=True, clause_cleanup_fallback=True)
    class Index:
        def get_scores(self, tokens):
            if 'consider' in tokens:
                return np.array([10., 2., 1.])
            if tokens == ['unseen']:
                return np.zeros(3)
            return np.array([1., 8., 20.])
    retriever.index = Index()
    assert retriever.search('Consider A; does this contract include unseen?')[0]['file_path'] == 'a'
    assert retriever.search('Consider A; does this contract include unseen?')[0]['text'] == 'term'
    retriever.config['clause_cleanup_fallback'] = False
    assert retriever.search('Consider A; does this contract include unseen?') == []
