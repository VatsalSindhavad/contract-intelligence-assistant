import json

import pytest

from summary_retrieval import NO_ANSWER,summary_cached,summary_request,validate_summary


@pytest.fixture
def setup(tmp_path):
    prompt='Summarise in 1-2 lines.\nONE SYNTHETIC EXAMPLE\nExample input and output.\n'
    (tmp_path/'prompt.txt').write_text(prompt,encoding='utf-8')
    config=dict(model='test',model_revision='pinned',runtime='test',prompt_file='prompt.txt',temperature=0,
                seed=42,max_output_tokens=768,context_length=12288,invalid_output_policy='return_original_candidates',
                max_evidence_quotes=3,max_summary_words=45)
    text='The term ends in 2029. Notice must be given 60 days before termination.'
    hits=[dict(file_path='a',start=100,end=100+len(text),text=text,score=2)]
    return tmp_path,config,hits,prompt


def test_summary_text_is_not_scored_as_source_evidence(setup):
    root,config,hits,_=setup
    raw=json.dumps(dict(summary='The agreement expires in 2029.',
                        evidence=[dict(passage_id=1,quote='The term ends in 2029.')]))
    summary,evidence=validate_summary(raw,'When does it end?',hits,config)
    assert summary=='The agreement expires in 2029.'
    assert evidence[0]['text']=='The term ends in 2029.'
    assert evidence[0]['start']==100


def test_summary_cannot_import_example_numbers(setup):
    _,config,hits,_=setup
    raw=json.dumps(dict(summary='It ends in 2030.',evidence=[dict(passage_id=1,quote='The term ends in 2029.')]))
    with pytest.raises(ValueError,match='introduces numbers'):
        validate_summary(raw,'When does it end?',hits,config)


def test_empty_evidence_requires_explicit_no_answer(setup):
    _,config,hits,_=setup
    assert validate_summary(json.dumps(dict(summary=NO_ANSWER,evidence=[])),'question',hits,config)==(NO_ANSWER,[])
    with pytest.raises(ValueError):
        validate_summary(json.dumps(dict(summary='Yes, it permits sublicensing.',evidence=[])),'question',hits,config)


def test_real_input_has_no_gold_or_hidden_example(setup):
    root,config,hits,prompt=setup
    request=summary_request(root,config,'question',hits)
    assert request['prompt']==prompt and request['prompt'].count('ONE SYNTHETIC EXAMPLE')==1
    assert set(request['input'])=={'question','passages'}
    assert set(request['input']['passages'][0])=={'passage_id','text'}


def test_invalid_quote_falls_back_and_replays_without_model(setup):
    root,config,hits,_=setup
    raw=json.dumps(dict(summary='It ends in 2029.',evidence=[dict(passage_id=1,quote='Invented quotation')]))
    entry,_=summary_cached(root,config,'question',hits,cache_only=False,caller=lambda request:dict(text=raw))
    assert entry['status']=='invalid_output' and entry['hits']==hits and entry['summary'] is None
    def deny(request):raise AssertionError('No model call allowed.')
    replay,cached=summary_cached(root,config,'question',hits,caller=deny)
    assert cached and replay==entry


def test_summary_word_and_line_limits(setup):
    _,config,hits,_=setup
    raw=json.dumps(dict(summary='one\ntwo\nthree',evidence=[]))
    with pytest.raises(ValueError,match='one or two lines'):
        validate_summary(raw,'question',hits,config)
