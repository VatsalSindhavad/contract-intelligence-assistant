import json

import pytest

from hosted_summary import HostedHybridSummaryRetriever, api_payload, cached_gemini_summary, hosted_request
from llm_rewrite import CacheMissError


@pytest.fixture
def setup(tmp_path):
    (tmp_path/'prompt.txt').write_text('Use only supplied passages.')
    config=dict(model='gemini-test',model_revision='alias',runtime='test',prompt_file='prompt.txt',temperature=0,
                seed=None,max_output_tokens=1536,context_length=100000,thinking_level='minimal',
                max_evidence_quotes=3,max_summary_words=45,invalid_output_policy='return_original_candidates',candidate_k=5)
    text='The agreement expires in 2029.'
    hits=[dict(file_path='public-contract',start=10,end=10+len(text),text=text,score=.01)]
    return tmp_path,config,hits


def test_payload_has_retrieved_text_but_no_offsets_or_labels(setup):
    root,config,hits=setup
    payload=api_payload(hosted_request(root,config,'When does it expire?',hits))
    data=json.loads(payload['contents'][0]['parts'][0]['text'])
    assert data==dict(question='When does it expire?',passages=[dict(passage_id=1,text=hits[0]['text'])])
    assert 'key' not in json.dumps(payload)


def test_api_output_cached_and_replayed_without_caller(setup):
    root,config,hits=setup
    raw=json.dumps(dict(summary='It expires in 2029.',evidence=[dict(passage_id=1,quote=hits[0]['text'])]))
    entry,_=cached_gemini_summary(root,config,'q',hits,False,lambda request:dict(text=raw,model_version='recorded'))
    assert entry['status']=='valid'
    def forbidden(request): pytest.fail('API called during replay.')
    replay,cached=cached_gemini_summary(root,config,'q',hits,caller=forbidden)
    assert cached and replay==entry
    with pytest.raises(CacheMissError): cached_gemini_summary(root,config,'new',hits,caller=forbidden)


def test_upstream_abstention_makes_no_api_call(setup):
    root,config,_=setup
    class Base:
        def search(self,query,k): return []
    model=HostedHybridSummaryRetriever(Base(),root,config)
    assert model.search('unsupported')==[]
    assert model.events[-1]['status']=='upstream_abstention'
    assert not (root/'cache').exists()


def test_invalid_output_and_http_failure_preserve_candidates(setup):
    root,config,hits=setup
    entry,_=cached_gemini_summary(root,config,'invalid',hits,False,lambda request:dict(text='bad JSON'))
    assert entry['status']=='invalid_output' and entry['hits']==hits
    entry,_=cached_gemini_summary(root,config,'rate_limited',hits,False,lambda request:dict(http_status=429))
    assert entry['status']=='http_error' and entry['hits']==hits
