import pytest
from hybrid_retrieval import HybridRetriever, reciprocal_rank_fusion


def hit(start,score=1):
    return dict(file_path='a',start=start,end=start+1,text='x',score=score)


def test_weighted_fusion_merges_identical_offsets_and_keeps_source():
    results=reciprocal_rank_fusion([[hit(0),hit(2)],[hit(2),hit(3)]],[.75,.25],60)
    assert len(results)==3
    assert results[0]['start']==2
    assert results[0]['score']==pytest.approx(.75/62+.25/61)
    assert results[0]['text']=='x'


def test_confidence_gate_uses_cosine_not_rrf():
    class Model:
        def search(self,query,k): return [hit(0,.6)]
    config=dict(candidate_pool=20,bm25_weight=.75,rrf_constant=60,dense_confidence_threshold=.55)
    model=HybridRetriever(Model(),Model(),config)
    assert model.search('q')
    model.config=dict(config,dense_confidence_threshold=.6)
    assert model.search('q')==[]
    with pytest.raises(ValueError): model.search('q',0)
