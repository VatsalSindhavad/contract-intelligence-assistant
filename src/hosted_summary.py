from project_paths import ROOT as PROJECT_ROOT, source_path
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from time import perf_counter

import requests

from llm_rewrite import CacheMissError, canonical, load_gemini_key
from summary_retrieval import NO_ANSWER, summary_request, validate_summary


def hosted_request(root, config, query, hits):
    request = summary_request(root,config,query,hits)
    request['provider'] = 'gemini'
    request['thinking_level'] = config['thinking_level']
    request['hosted_protocol'] = 1
    return request


def api_payload(request):
    return dict(systemInstruction={'parts':[{'text':request['prompt']}]},
                contents=[{'role':'user','parts':[{'text':json.dumps(request['input'],ensure_ascii=False)}]}],
                generationConfig=dict(temperature=request['settings']['temperature'],
                                      maxOutputTokens=request['settings']['max_output_tokens'],
                                      responseMimeType='application/json',responseJsonSchema=request['schema'],
                                      thinkingConfig=dict(thinkingLevel=request['thinking_level'])))


def call_gemini(root, request):
    key = load_gemini_key(root)
    if not key:
        raise RuntimeError('Gemini key is not configured.')
    model = request['settings']['model']
    if not re.fullmatch(r'[A-Za-z0-9._-]+',model):
        raise ValueError('Invalid model identifier.')
    response = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
                             headers={'x-goog-api-key':key},json=api_payload(request),timeout=120)
    if not response.ok:
        return dict(http_status=response.status_code)
    data = response.json()
    candidates = data.get('candidates',[])
    text = ''.join(part.get('text','') for part in candidates[0].get('content',{}).get('parts',[])
                   if not part.get('thought')) if candidates else ''
    return dict(text=text,usage=data.get('usageMetadata',{}),
                model_version=data.get('modelVersion'),
                finish_reason=candidates[0].get('finishReason') if candidates else None,
                safety_ratings=candidates[0].get('safetyRatings',[]) if candidates else [],
                prompt_feedback=data.get('promptFeedback'))


def cached_gemini_summary(root, config, query, hits, cache_only=True, caller=None):
    request = hosted_request(root,config,query,hits)
    key = hashlib.sha256(canonical(request).encode()).hexdigest()
    path = Path(root)/'cache'/'gemini_hybrid_summaries'/f'{key}.json'
    if path.exists():
        entry = json.loads(path.read_text(encoding='utf-8'))
        if entry['request']!=request or entry['cache_key']!=key:
            raise ValueError('Hosted summary cache identity mismatch.')
        if entry['status']=='valid':
            summary,evidence = validate_summary(entry['raw_text'],query,hits,config)
            if summary!=entry['summary'] or evidence!=entry['hits']:
                raise ValueError('Hosted summary evidence differs from validated source.')
        elif entry['summary'] is not None or entry['hits']!=hits:
            raise ValueError('Invalid hosted fallback record.')
        return entry,True
    if cache_only:
        raise CacheMissError('Hosted summary cache missing; no API call was made.')
    started = perf_counter()
    raw,summary,metadata,error = '',None,{},None
    try:
        metadata = (caller(request) if caller else call_gemini(root,request))
        if metadata.get('http_status'):
            status,evidence,error = 'http_error',hits,f"HTTP {metadata['http_status']}"
        else:
            raw = metadata.get('text','')
            try:
                summary,evidence = validate_summary(raw,query,hits,config)
                status = 'valid'
            except (ValueError,TypeError,KeyError) as exc:
                status,summary,evidence,error = 'invalid_output',None,hits,str(exc)
    except requests.RequestException as exc:
        status,evidence,error = 'transport_error',hits,type(exc).__name__
    entry = dict(cache_key=key,request=request,status=status,raw_text=raw,summary=summary,hits=evidence,
                 validation_error=error,response_metadata={k:v for k,v in metadata.items() if k!='text'},
                 model_call_ms=(perf_counter()-started)*1000,created_at_utc=datetime.now(timezone.utc).isoformat())
    path.parent.mkdir(parents=True,exist_ok=True)
    temp = path.with_suffix('.part')
    temp.write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(path)
    return entry,False


class HostedHybridSummaryRetriever:
    def __init__(self, base, root, config):
        self.base,self.root,self.config = base,Path(root),config
        self.events = []
        self.last_summary = None

    def search(self, query, k=5):
        started = perf_counter()
        hits = self.base.search(query,self.config['candidate_k'])
        if not hits:
            self.last_summary = NO_ANSWER
            self.events.append(dict(query=query,status='upstream_abstention',model_call_ms=0,
                                    replay_ms=(perf_counter()-started)*1000))
            return []
        entry,_ = cached_gemini_summary(self.root,self.config,query,hits)
        self.last_summary = entry['summary']
        self.events.append(dict(query=query,status=entry['status'],cache_key=entry['cache_key'],
                                validation_error=entry['validation_error'],model_call_ms=entry['model_call_ms'],
                                replay_ms=(perf_counter()-started)*1000))
        return entry['hits'][:k]
