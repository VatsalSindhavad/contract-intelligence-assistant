import pytest

from heldout_evaluation import evaluate_test


def test_test_scoring_preserves_split_and_never_passes_labels_to_model():
    class Model:
        def search(self,query,k):
            assert isinstance(query,str)
            return [] if query=='unknown' else [dict(file_path='a',start=0,end=4,text='term')]
    positive=[dict(query_id='p',query='term?',split='test',snippets=[dict(file_path='a',span=[0,4],answer='term')])]
    negative=[dict(query_id='n',query='unknown',split='test',answerable=False)]
    result=evaluate_test(Model(),positive,negative,{'a':'term'})
    assert result['answerable']['metrics'][0]['precision']==1
    assert result['negative']['correct_abstention_rate']==1
    positive[0]['split']='train'
    with pytest.raises(ValueError,match='test answerable'):
        evaluate_test(Model(),positive,negative,{'a':'term'})
