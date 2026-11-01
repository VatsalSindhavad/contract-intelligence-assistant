import json

import pytest

from llm_rewrite import CacheMissError, RewriteRetriever, get_rewrite, load_gemini_key, validate_output


@pytest.fixture
def rewrite_setup(tmp_path):
    (tmp_path / 'prompt.txt').write_text('Return legal keywords as JSON.', encoding='utf-8')
    config = dict(provider='test', model='fixed', prompt_file='prompt.txt', temperature=0, max_output_tokens=128)
    return tmp_path, config


def test_cache_only_never_calls_provider(rewrite_setup):
    root, config = rewrite_setup
    def fail(request):
        raise AssertionError('Provider must not be called.')
    with pytest.raises(CacheMissError):
        get_rewrite(root, config, 'term?', cache_only=True, caller=fail)


def test_saved_response_replays_and_settings_change_key(rewrite_setup):
    root, config = rewrite_setup
    calls = []
    def caller(request):
        calls.append(request)
        return dict(text='{"search_terms":"expiration renewal term"}', usage=dict(tokens=3))
    entry, hit = get_rewrite(root, config, 'term?', cache_only=False, caller=caller)
    assert not hit and entry['status'] == 'valid'
    replay, hit = get_rewrite(root, config, 'term?', caller=caller)
    assert hit and replay == entry and len(calls) == 1
    with pytest.raises(CacheMissError):
        get_rewrite(root, dict(config, temperature=0.5), 'term?')


def test_invalid_output_is_cached_as_explicit_fallback(rewrite_setup):
    root, config = rewrite_setup
    caller = lambda request: dict(text='{"search_terms":"term ends in 2099"}')
    entry, _ = get_rewrite(root, config, 'When does the term end?', cache_only=False, caller=caller)
    assert entry['status'] == 'invalid_output' and entry['search_terms'] is None
    assert get_rewrite(root, config, 'When does the term end?')[0] == entry


def test_cache_tampering_fails(rewrite_setup):
    root, config = rewrite_setup
    entry, _ = get_rewrite(root, config, 'term?', cache_only=False,
                           caller=lambda request: dict(text='{"search_terms":"expiration"}'))
    path = root / 'cache/llm_rewrites' / (entry['cache_key'] + '.json')
    entry['search_terms'] = 'changed'
    path.write_text(json.dumps(entry), encoding='utf-8')
    with pytest.raises(ValueError, match='differs'):
        get_rewrite(root, config, 'term?')


def test_wrapper_keeps_original_query_for_document_routing(rewrite_setup):
    root, config = rewrite_setup
    get_rewrite(root, config, 'term?', cache_only=False,
                caller=lambda request: dict(text='{"search_terms":"expiration"}'))
    class Base:
        def search(self, query, k, clause_override):
            assert query == 'Consider A; term?'
            assert clause_override == 'term? expiration'
            return []
    wrapper = RewriteRetriever(Base(), root, config)
    assert wrapper.search('Consider A; term?') == []
    assert wrapper.events[0]['status'] == 'valid'


def test_output_requires_exact_schema():
    with pytest.raises(ValueError):
        validate_output('{"answer":"yes"}', 'question')


def test_local_key_file_is_not_added_to_cache_identity(rewrite_setup, monkeypatch):
    root, config = rewrite_setup
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    monkeypatch.delenv('GOOGLE_API_KEY', raising=False)
    (root / 'secrets').mkdir()
    (root / 'secrets/gemini_api_key.txt').write_text('fake-test-secret', encoding='utf-8')
    assert load_gemini_key(root) == 'fake-test-secret'
    entry, _ = get_rewrite(root, config, 'term?', cache_only=False,
                           caller=lambda request: dict(text='{"search_terms":"expiration"}'))
    assert 'fake-test-secret' not in json.dumps(entry)


def test_retry_preserves_failed_attempt_without_recalling_valid_outputs(rewrite_setup):
    import requests
    root, config = rewrite_setup
    def failed(request):
        raise requests.ConnectionError('do not serialize request secrets')
    entry, _ = get_rewrite(root,config,'term?',cache_only=False,caller=failed)
    assert entry['status']=='transport_error'
    entry, _ = get_rewrite(root,config,'term?',cache_only=False,retry_failed=True,
                           caller=lambda request:dict(text='{"search_terms":"expiration"}'))
    assert entry['status']=='valid'
    assert len(list((root/'cache/llm_rewrites/failed_attempts').glob('*.json')))==1
