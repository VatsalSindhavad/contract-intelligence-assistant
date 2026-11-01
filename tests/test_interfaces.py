import hashlib
import json
from pathlib import Path

import pytest

from cli import main
from search_service import EXAMPLE_QUERY, ROOT, build_model, config_label, search


def test_labels_distinguish_accepted_gains_from_rejected_candidates():
    assert 'Better than baseline' in config_label('bm25_focused_stemmed')
    assert 'Current best' in config_label('bm25_focused_stemmed')
    assert 'Better than baseline' not in config_label('bm25_focused_clause')
    assert 'below acceptance' in config_label('bm25_b_030')


@pytest.fixture
def small_project(tmp_path):
    (tmp_path / 'configs').mkdir()
    (tmp_path / 'data/prepared').mkdir(parents=True)
    (tmp_path / 'data/corpus').mkdir()
    corpus = {'a.txt': 'sublicensing permission license', 'b.txt': 'payment invoice money', 'c.txt': 'governing jurisdiction law'}
    metadata = {}
    for name, text in corpus.items():
        (tmp_path / 'data/corpus' / name).write_text(text, encoding='utf-8')
        metadata[name] = dict(text_sha256=hashlib.sha256(text.encode()).hexdigest())
    (tmp_path / 'data/prepared/manifest.json').write_text(json.dumps(dict(corpus=metadata)), encoding='utf-8')
    config = dict(name='demo', chunk_size=100, chunk_overlap=0, k1=1.5, b=0.75, min_score=0)
    (tmp_path / 'configs/demo.json').write_text(json.dumps(config), encoding='utf-8')
    return tmp_path


def test_inference_loads_no_query_labels_and_keeps_offsets(small_project):
    model = build_model('demo', small_project)
    result = search(model, 'sublicensing', 2)
    assert result['status'] == 'matches'
    hit = result['hits'][0]
    assert hit['file_path'] == 'a.txt'
    original = (small_project / 'data/corpus' / hit['file_path']).read_text(encoding='utf-8')
    assert hit['text'] == original[hit['start']:hit['end']]
    assert not (small_project / 'data/prepared/train.json').exists()


def test_empty_results_and_invalid_inputs(small_project):
    model = build_model('demo', small_project)
    assert search(model, 'unseenword')['status'] == 'no_matches'
    with pytest.raises(ValueError, match='question'):
        search(model, '  ')
    with pytest.raises(ValueError, match='between'):
        search(model, 'sublicensing', 0)
    with pytest.raises(ValueError, match='Unknown'):
        build_model('missing', small_project)


def test_cli_json_matches_shared_service(small_project, monkeypatch, capsys):
    import cli
    model = build_model('demo', small_project)
    monkeypatch.setattr(cli, 'build_model', lambda name: model)
    assert main(['sublicensing', '--json', '--k', '2']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['hits'] == search(model, 'sublicensing', 2)['hits']


def test_cli_handles_bad_config(monkeypatch):
    import cli
    def fail(name):
        raise ValueError('Unknown configuration')
    monkeypatch.setattr(cli, 'build_model', fail)
    with pytest.raises(SystemExit) as error:
        main(['question'])
    assert error.value.code == 2


def test_saved_llm_choice_uses_cache_only(small_project):
    from llm_rewrite import CacheMissError, get_rewrite
    from search_service import available_configs
    (small_project / 'llm_configs').mkdir()
    (small_project / 'prompt.txt').write_text('Return legal keywords.', encoding='utf-8')
    config = dict(name='llm_demo', provider='test', model='fixed', prompt_file='prompt.txt',
                  temperature=0,max_output_tokens=128,baseline_config='configs/demo.json',expose_in_demo=True)
    (small_project / 'llm_configs/demo.json').write_text(json.dumps(config),encoding='utf-8')
    get_rewrite(small_project,config,'sublicensing',cache_only=False,
                caller=lambda request:dict(text='{"search_terms":"license permission"}'))
    assert 'llm_demo' in available_configs(small_project)
    model=build_model('llm_demo',small_project)
    assert search(model,'sublicensing')['hits'][0]['file_path']=='a.txt'
    with pytest.raises(CacheMissError):
        search(model,'uncached question')


@pytest.mark.skipif(not (ROOT / 'data/prepared/manifest.json').exists(), reason='Prepare corpus first.')
def test_web_search_and_empty_state():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(ROOT / 'app.py', default_timeout=60).run()
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception
    expected = search(build_model(), EXAMPLE_QUERY, 5)['hits']
    assert len(app.expander) == len(expected)
    assert app.text[0].value == expected[0]['text']
    app.text_area[0].set_value('zzzznonexistenttokenzzzz')
    app.button[0].click().run()
    assert not app.exception
    assert app.info[0].value == 'No relevant passage found.'
    assert len(app.expander) == 0
    app.text_area[0].set_value(' ')
    app.button[0].click().run()
    assert app.error[0].value == 'Enter a question.'


@pytest.mark.skipif(not (ROOT/'cache/llm_rewrites').exists(), reason='Populate approved Gemini cache first.')
def test_gemini_demo_requires_neither_network_nor_api_key(monkeypatch):
    import llm_rewrite
    import requests
    def deny(*args, **kwargs):
        raise AssertionError('Presentation must not access network or credentials.')
    monkeypatch.setattr(requests,'post',deny)
    monkeypatch.setattr(llm_rewrite,'load_gemini_key',deny)
    model=build_model('llm_gemini_rewrite')
    assert search(model,EXAMPLE_QUERY,3)['hits']
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(ROOT/'app.py',default_timeout=60).run()
    app.selectbox[0].select('llm_gemini_rewrite').run()
    app.button[0].click().run()
    assert not app.exception
    assert len(app.expander)>0
    local=build_model('llm_local_phi3_rewrite')
    assert search(local,EXAMPLE_QUERY,3)['hits']
    app.selectbox[0].select('llm_local_phi3_rewrite').run()
    app.button[0].click().run()
    assert not app.exception
    assert len(app.expander)>0


@pytest.mark.skipif(not (ROOT/'cache/dense').exists(), reason='Build local dense cache first.')
def test_dense_web_and_cli_service_share_cached_evidence(monkeypatch):
    import requests
    def deny(*args,**kwargs):
        raise AssertionError('Cached dense presentation must not call a provider.')
    monkeypatch.setattr(requests,'post',deny)
    model=build_model('dense_minilm_faiss')
    expected=search(model,EXAMPLE_QUERY,5)
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(ROOT/'app.py',default_timeout=60).run()
    app.selectbox[0].select('dense_minilm_faiss').run()
    app.button[0].click().run()
    assert not app.exception
    assert len(app.expander)==len(expected['hits'])
    assert app.text[0].value==expected['hits'][0]['text']
