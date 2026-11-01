import json

import pytest

from recall_recovery import RecoverySummaryRetriever


@pytest.fixture
def setup(tmp_path):
    (tmp_path/'prompt.txt').write_text('Complete answering clauses only.')
    config=dict(model='gemini-test',model_revision='alias',runtime='test',prompt_file='prompt.txt',temperature=0,
                seed=None,max_output_tokens=3072,context_length=100000,thinking_level='minimal',candidate_k=20,
                max_evidence_quotes=5,max_summary_words=45,invalid_output_policy='return_original_candidates')
    text='The term expires in 2029.'
    hits=[dict(file_path='a',start=0,end=len(text),text=text,score=1)]
    return tmp_path,config,hits


class Previous:
    def __init__(self,status,hits): self.status,self.hits=status,hits
    def resolve(self,query,cache_only=True):
        assert cache_only
        return dict(status=self.status,hits=self.hits,summary='Earlier answer.',model_call_ms=5),{}


def test_supported_answer_is_reused_without_retrieval_or_api(setup):
    root,config,hits=setup
    class Forbidden:
        def search(self,*args): pytest.fail('Successful answer must not be regenerated.')
    model=RecoverySummaryRetriever(Forbidden(),root,config,Previous('valid',hits))
    assert model.search('q')==hits
    assert model.events[-1]['decision']=='reuse_supported_answer'
    assert model.events[-1]['additional_model_ms']==0


@pytest.mark.parametrize('status,has_fallback',[('valid',False),('invalid_output',True),('upstream_abstention',False)])
def test_only_status_and_evidence_trigger_recovery(setup,status,has_fallback):
    root,config,hits=setup
    class Base:
        def search(self,query,k):
            assert k==20
            return hits
    model=RecoverySummaryRetriever(Base(),root,config,Previous(status,hits if has_fallback else []))
    raw=json.dumps(dict(summary='It expires in 2029.',evidence=[dict(passage_id=1,quote=hits[0]['text'])]))
    entry,decision=model.resolve('q',False,lambda request:dict(text=raw))
    assert entry['status']=='valid' and decision['decision']=='recovery'
    assert model.search('q')==entry['hits']


def test_provider_failure_is_not_silently_recovered(setup):
    root,config,hits=setup
    model=RecoverySummaryRetriever(None,root,config,Previous('http_error',hits))
    with pytest.raises(RuntimeError,match='Finish the first-stage'):
        model.resolve('q',False)
