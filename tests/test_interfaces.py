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
