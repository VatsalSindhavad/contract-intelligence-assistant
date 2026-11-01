from retrieval import BM25Retriever, tokenize


def config(**extra):
    return dict(chunk_size=1000, chunk_overlap=200, k1=1.5, b=0.75, min_score=0, **extra)


def test_stemming_matches_inflections_and_keeps_original_offsets():
    documents = {'a': 'licensing licensed license', 'b': 'payments invoice money', 'c': 'governing jurisdiction law'}
    retriever = BM25Retriever(documents, config(stemming='english'))
    hits = retriever.search('licenses', k=1)
    assert hits[0]['file_path'] == 'a'
    assert hits[0]['text'] == documents['a'][hits[0]['start']:hits[0]['end']]


def test_baseline_tokens_remain_unchanged_without_stemming():
    retriever = BM25Retriever({'a':'license', 'b':'money', 'c':'court'}, config())
    assert retriever.normalize(tokenize('licenses licensing')) == ['licenses', 'licensing']


def test_stemming_keeps_negation_and_runs_routed_fallback():
    retriever = BM25Retriever({'a':'AsterCo license not transferable', 'b':'BetaCo money', 'c':'CedarCo court'},
                              config(stemming='english', query_mode='document_then_clause',
                                     clause_query_cleanup=True, clause_cleanup_fallback=True))
    assert retriever.normalize(['not', 'without']) == ['not', 'without']
    assert retriever.search('Consider AsterCo; licenses')[0]['file_path'] == 'a'
