import pytest

from clause_chunking import AbstentionRetriever, clause_chunks


@pytest.mark.parametrize('text', ['First clause. Second clause.\n\n2. Next section; More terms.',
                                   'x'*1500, 'A word '*350, '\n\n', ''])
def test_offsets_coverage_and_size(text):
    chunks = clause_chunks({'contract':text},100)
    assert ''.join(c['text'] for c in chunks)==text
    assert all(c['text']==text[c['start']:c['end']] and len(c['text'])<=100 for c in chunks)
    assert all(a['end']==b['start'] for a,b in zip(chunks,chunks[1:]))


def test_paragraphs_do_not_merge():
    assert len(clause_chunks({'a':'Clause one.\n\nClause two.'}))==2


def test_space_at_limit_does_not_exceed_limit():
    chunks = clause_chunks({'a':'x'*100+' '+'y'*100},100)
    assert all(len(chunk['text'])<=100 for chunk in chunks)


def test_gate_rejects_whole_query_without_reranking():
    class Base:
        config = {}
        def search(self, query, k):
            return [dict(score=.6),dict(score=.1)][:k]
    assert len(AbstentionRetriever(Base(),.5).search('q'))==2
    assert AbstentionRetriever(Base(),.6).search('q')==[]
