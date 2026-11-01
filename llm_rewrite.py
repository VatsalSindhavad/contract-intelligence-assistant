import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import requests

from retrieval import clause_question


SCHEMA = {'type': 'object', 'properties': {'search_terms': {'type': 'string'}},
          'required': ['search_terms'], 'additionalProperties': False}


class CacheMissError(RuntimeError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def make_request(root, config, question):
    prompt = (Path(root) / config['prompt_file']).read_text(encoding='utf-8')
    return dict(provider=config['provider'], model=config['model'],
                model_revision=config.get('model_revision'), runtime=config.get('runtime'),
                prompt=prompt, question=question, schema=SCHEMA,
                temperature=config['temperature'], max_output_tokens=config['max_output_tokens'],
                seed=config.get('seed'), context_length=config.get('context_length'),
                thinking_level=config.get('thinking_level'),
                protocol_version=1)


def load_gemini_key(root=None):
    key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
    if key:
        return key.strip()
    root = Path(root) if root is not None else Path(__file__).resolve().parent
    key_path = root / 'secrets/gemini_api_key.txt'
    return key_path.read_text(encoding='utf-8-sig').strip() if key_path.exists() else ''


def validate_output(raw, question):
    value = json.loads(raw)
    if not isinstance(value, dict) or set(value) != {'search_terms'}:
        raise ValueError('Expected the search_terms object.')
    terms = value['search_terms']
    if not isinstance(terms, str) or not terms.strip() or len(terms) > 400 or len(terms.split()) > 24:
        raise ValueError('Invalid search term length.')
    if set(re.findall(r'\d+', terms)) - set(re.findall(r'\d+', question)):
        raise ValueError('Output introduced numeric facts.')
    return terms.strip()


def call_model(request):
    user = 'Question as JSON data: ' + json.dumps(request['question'], ensure_ascii=False)
    if request['provider'] == 'ollama':
        payload = dict(model=request['model'], system=request['prompt'], prompt=user,
                       stream=False, format=request['schema'], keep_alive='10m',
                       options=dict(temperature=request['temperature'], seed=request['seed'],
                                    num_predict=request['max_output_tokens'], num_ctx=request['context_length']))
        response = requests.post('http://127.0.0.1:11434/api/generate', json=payload, timeout=180)
        response.raise_for_status()
        data = response.json()
        return dict(text=data.get('response', ''), usage={k: data.get(k) for k in
                    ['prompt_eval_count', 'eval_count', 'total_duration', 'load_duration', 'eval_duration']},
                    response_metadata={'model': data.get('model'), 'done_reason': data.get('done_reason')})
    if request['provider'] == 'gemini':
        key = load_gemini_key()
        if not key:
            raise RuntimeError('Missing Gemini API key in environment.')
        if not re.fullmatch(r'[A-Za-z0-9._-]+', request['model']):
            raise ValueError('Invalid model identifier.')
        payload = dict(systemInstruction={'parts': [{'text': request['prompt']}]},
                       contents=[{'role': 'user', 'parts': [{'text': user}]}],
                       generationConfig=dict(temperature=request['temperature'],
                                             maxOutputTokens=request['max_output_tokens'],
                                             responseMimeType='application/json', responseJsonSchema=request['schema']))
        if request.get('thinking_level'):
            payload['generationConfig']['thinkingConfig'] = {'thinkingLevel': request['thinking_level']}
        response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{request['model']}:generateContent",
                                 headers={'x-goog-api-key': key}, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        candidates = data.get('candidates', [])
        text = ''.join(p.get('text', '') for p in candidates[0].get('content', {}).get('parts', [])) if candidates else ''
        return dict(text=text, usage=data.get('usageMetadata', {}),
                    response_metadata={'model_version': data.get('modelVersion'),
                                       'finish_reason': candidates[0].get('finishReason') if candidates else None})
    raise ValueError('Unsupported hosted provider; select and implement it before calling.')


def get_rewrite(root, config, question, cache_only=True, caller=call_model, retry_failed=False):
    request = make_request(root, config, question)
    key = hashlib.sha256(canonical(request).encode('utf-8')).hexdigest()
    cache = Path(root) / 'cache' / 'llm_rewrites' / f'{key}.json'
    if cache.exists():
        entry = json.loads(cache.read_text(encoding='utf-8'))
        if entry['request'] != request or entry['cache_key'] != key:
            raise ValueError('Cache identity mismatch.')
        if entry['status'] == 'valid':
            if validate_output(entry['raw_text'], question) != entry['search_terms']:
                raise ValueError('Cached output differs from validated text.')
        elif entry['search_terms'] is not None:
            raise ValueError('Invalid cache fallback entry.')
        if not cache_only and retry_failed and entry['status'] in ['http_error', 'transport_error']:
            history = cache.parent / 'failed_attempts'
            history.mkdir(exist_ok=True)
            suffix = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            (history / f'{key}_{suffix}.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf-8')
        else:
            return entry, True
    if cache_only:
        raise CacheMissError(f'Missing rewrite cache: {key}. No model call was made.')
    started = perf_counter()
    raw_text, usage, metadata, terms = '', {}, {}, None
    try:
        result = caller(request)
        raw_text, usage, metadata = result['text'], result.get('usage', {}), result.get('response_metadata', {})
        try:
            terms = validate_output(raw_text, question)
            status = 'valid'
        except (ValueError, TypeError):
            status = 'invalid_output'
    except requests.HTTPError as error:
        status = 'http_error'
        metadata = {'http_status': error.response.status_code if error.response is not None else None}
        if error.response is not None:
            metadata['retry_after'] = error.response.headers.get('Retry-After')
            try:
                detail = error.response.json().get('error', {})
                metadata['provider_status'] = detail.get('status')
                metadata['quota_ids'] = [v.get('quotaId') for d in detail.get('details', [])
                                        for v in d.get('violations', []) if v.get('quotaId')]
            except ValueError:
                pass
    except requests.RequestException:
        status = 'transport_error'
    entry = dict(cache_key=key, request=request, status=status, search_terms=terms,
                 raw_text=raw_text, usage=usage, response_metadata=metadata,
                 model_call_ms=(perf_counter() - started) * 1000,
                 created_at_utc=datetime.now(timezone.utc).isoformat())
    cache.parent.mkdir(parents=True, exist_ok=True)
    temporary = cache.with_suffix('.part')
    temporary.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(cache)
    return entry, False


class RewriteRetriever:
    def __init__(self, base, root, config):
        self.base, self.root, self.config = base, Path(root), config
        self.events = []

    def search(self, query, k=5):
        question = clause_question(query) or query
        started = perf_counter()
        entry, _ = get_rewrite(self.root, self.config, question, cache_only=True)
        terms = entry['search_terms']
        override = f'{question} {terms}' if terms else None
        hits = self.base.search(query, k=k, clause_override=override)
        self.events.append(dict(cache_key=entry['cache_key'], status=entry['status'],
                                original_model_call_ms=entry['model_call_ms'],
                                cache_retrieval_ms=(perf_counter() - started) * 1000))
        return hits
