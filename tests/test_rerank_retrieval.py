import json

import pytest

from rerank_retrieval import RerankRetriever


class Base:
    def search(self,query,k):
        if query=='negative': return []
        return [dict(file_path='a',start=i,end=i+1,text=str(i),score=1/(i+1)) for i in range(3)]


class Scorer:
    def score(self,query,hits):
        return dict(scores=[-2,4,1],pair_tokens=[100,600,200])


def config():
    return dict(candidate_pool=20,max_length=512,model_id='fake',revision='pinned')


def test_source_preserving_ranking_and_offline_replay(tmp_path):
    model=RerankRetriever(Base(),tmp_path,config(),True,Scorer())
    hits=model.search('q',2)
    assert [h['start'] for h in hits]==[1,2]
    assert hits[0]['text']=='1'
    assert hits[0]['hybrid_score']==.5
    assert model.events[0]['truncated_pairs']==1
    replay=RerankRetriever(Base(),tmp_path,config())
    assert replay.search('q',2)==hits
    assert replay.events[0]['cached']


def test_gate_does_not_call_reranker_and_unknown_cache_fails(tmp_path):
    model=RerankRetriever(Base(),tmp_path,config())
    assert model.search('negative')==[]
    with pytest.raises(RuntimeError,match='cache missing'): model.search('unknown')


def test_corruption_and_model_change_cannot_reuse_cache(tmp_path):
    RerankRetriever(Base(),tmp_path,config(),True,Scorer()).search('q')
    with pytest.raises(RuntimeError,match='cache missing'):
        RerankRetriever(Base(),tmp_path,dict(config(),revision='changed')).search('q')
    path=next((tmp_path/'cache/rerank_scores').glob('*.json'))
    entry=json.loads(path.read_text())
    entry['result']['scores'][0]=100
    path.write_text(json.dumps(entry))
    with pytest.raises(ValueError,match='checksum'):
        RerankRetriever(Base(),tmp_path,config()).search('q')
