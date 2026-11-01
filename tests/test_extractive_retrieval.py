import json

import pytest

from extractive_retrieval import extraction_request,extract_cached,validate_extraction
from run_precision_pilot import precision_decision,select_pilot


def candidates():
    return [dict(file_path='a',start=100,end=143,text='The license ends on 31 December 2027 unless extended.',score=3.0)]


@pytest.fixture
def setup(tmp_path):
    prompt='Answer only what is asked, nothing more and nothing less.\n'
    (tmp_path/'prompt.txt').write_text(prompt,encoding='utf-8')
    config=dict(model='test',model_revision='pinned',runtime='test',prompt_file='prompt.txt',
                temperature=0,seed=42,max_output_tokens=256,context_length=8192,
                invalid_output_policy='return_original_candidates')
    return tmp_path,config,prompt


def test_exact_quote_maps_to_original_source_positions():
    hits=validate_extraction('{"passage_id":1,"answer":"31 December 2027 unless extended"}',candidates())
    assert hits[0]['start']==100+candidates()[0]['text'].index('31 December')
    assert hits[0]['end']-hits[0]['start']==len(hits[0]['text'])


def test_paraphrase_and_ambiguous_quote_are_rejected():
    with pytest.raises(ValueError,match='exact substring'):
        validate_extraction('{"passage_id":1,"answer":"It expires next year"}',candidates())
    repeated=[dict(candidates()[0],text='license license')]
    with pytest.raises(ValueError,match='ambiguous'):
        validate_extraction('{"passage_id":1,"answer":"license"}',repeated)


def test_explicit_no_answer_and_invalid_id():
    assert validate_extraction('{"passage_id":0,"answer":""}',candidates())==[]
    with pytest.raises(ValueError):validate_extraction('{"passage_id":true,"answer":"license"}',candidates())


def test_prompt_sent_exactly_and_input_has_no_gold_metadata(setup):
    root,config,prompt=setup
    request=extraction_request(root,config,'When does it end?',candidates())
    assert request['prompt']==prompt
    assert set(request['input'])=={'question','passages'}
    assert set(request['input']['passages'][0])=={'passage_id','text'}
    assert request['input']['passages'][0]['text']==candidates()[0]['text']


def test_invalid_output_falls_back_and_cache_replay_makes_no_call(setup):
    root,config,_=setup
    entry,_=extract_cached(root,config,'question',candidates(),cache_only=False,
                           caller=lambda request:dict(text='{"passage_id":1,"answer":"made up"}'))
    assert entry['status']=='invalid_output'
    assert entry['hits']==candidates()
    def deny(request):raise AssertionError('No model call allowed.')
    replay,hit=extract_cached(root,config,'question',candidates(),caller=deny)
    assert hit and replay==entry


def test_oversize_context_fails_before_call(setup):
    root,config,_=setup
    with pytest.raises(ValueError,match='context bound'):
        extraction_request(root,dict(config,context_length=10),'question',candidates())


def test_pilot_selection_does_not_depend_on_record_order_and_rejects_test():
    records=[dict(query=q,split='train') for q in ['b','a','c']]
    assert select_pilot(records,2)==select_pilot(list(reversed(records)),2)
    with pytest.raises(ValueError):select_pilot([dict(query='a',split='test')],1)


def test_precision_gain_cannot_hide_recall_collapse():
    def result(p,r):return dict(answerable=dict(metrics=[dict(k=5,precision=p,recall=r)],
                                               answerable_false_abstention_rate=0),
                                negative=dict(correct_abstention_rate=0))
    policy=dict(minimum_precision_gain_absolute=0.01,maximum_recall_drop_absolute=0.02,
                maximum_false_abstention_increase_absolute=0.02,maximum_correct_abstention_drop_absolute=0)
    decision=precision_decision(result(0.08,0.7),result(0.5,0.2),policy)
    assert decision['checks']['precision_gain'] and not decision['quality_pass']
