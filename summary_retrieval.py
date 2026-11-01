import hashlib
import json
import re
from datetime import datetime,timezone
from pathlib import Path
from time import perf_counter

import requests

from extractive_retrieval import extraction_request,local_extract,validate_extraction
from llm_rewrite import CacheMissError,canonical


NO_ANSWER='The supplied passages do not answer the question.'


def summary_request(root,config,query,candidates):
    request=extraction_request(root,config,query,candidates)
    request['schema']={'type':'object','properties':{
        'summary':{'type':'string'},
        'evidence':{'type':'array','maxItems':config['max_evidence_quotes'],'items':{
            'type':'object','properties':{'passage_id':{'type':'integer','minimum':1,'maximum':len(candidates)},
                                         'quote':{'type':'string'}},
            'required':['passage_id','quote'],'additionalProperties':False}}},
        'required':['summary','evidence'],'additionalProperties':False}
    request['summary_policy']=dict(max_words=config['max_summary_words'],max_lines=2,
                                   max_quotes=config['max_evidence_quotes'],no_answer=NO_ANSWER)
    request['protocol']=2
    bound=len((request['prompt']+json.dumps(request['input'],ensure_ascii=False)+json.dumps(request['schema'])).encode('utf-8'))+512+config['max_output_tokens']
    if bound>config['context_length']:
        raise ValueError('Summary input exceeds context bound; no passage was silently truncated.')
    return request


def validate_summary(raw,query,candidates,config):
    value=json.loads(raw)
    if not isinstance(value,dict) or set(value)!={'summary','evidence'}:
        raise ValueError('Expected summary and evidence only.')
    summary,evidence=value['summary'],value['evidence']
    if not isinstance(summary,str) or not summary.strip() or len(summary.splitlines())>2 or len(summary.split())>config['max_summary_words']:
        raise ValueError('Summary must be one or two lines and within the word limit.')
    if not isinstance(evidence,list) or len(evidence)>config['max_evidence_quotes']:
        raise ValueError('Invalid evidence list.')
    if not evidence:
        if summary.strip().rstrip('.').casefold()!=NO_ANSWER.rstrip('.').casefold():
            raise ValueError('Empty evidence requires the declared no-answer summary.')
        return summary,[]
    hits=[]
    for item in evidence:
        if not isinstance(item,dict) or set(item)!={'passage_id','quote'} or type(item['passage_id']) is not int or item['passage_id']<1:
            raise ValueError('Invalid evidence citation.')
        hits.extend(validate_extraction(json.dumps(dict(passage_id=item['passage_id'],answer=item['quote'])),candidates))
    known=' '.join([query]+[h['text'] for h in hits])
    if set(re.findall(r'\d+',summary))-set(re.findall(r'\d+',known)):
        raise ValueError('Summary introduces numbers absent from its cited evidence/question.')
    unique=[]
    seen=set()
    for hit in hits:
        key=(hit['file_path'],hit['start'],hit['end'])
        if key not in seen:
            unique.append(hit)
            seen.add(key)
    return summary,unique


def summary_cached(root,config,query,candidates,cache_only=True,caller=local_extract):
    request=summary_request(root,config,query,candidates)
    key=hashlib.sha256(canonical(request).encode('utf-8')).hexdigest()
    path=Path(root)/'cache/local_summaries'/f'{key}.json'
    if path.exists():
        entry=json.loads(path.read_text(encoding='utf-8'))
        if entry['request']!=request or entry['cache_key']!=key:
            raise ValueError('Summary-cache identity mismatch.')
        if entry['status']=='valid':
            summary,hits=validate_summary(entry['raw_text'],query,candidates,config)
            if summary!=entry['summary'] or hits!=entry['hits']:
                raise ValueError('Cached summary/evidence differs from validated output.')
        elif entry['hits']!=candidates or entry['summary'] is not None:
            raise ValueError('Invalid summary fallback record.')
        return entry,True
    if cache_only:
        raise CacheMissError(f'Missing local-summary cache: {key}. No model call was made.')
    started=perf_counter()
    raw,usage,summary,reason,done_reason='',{},None,None,None
    try:
        response=caller(request)
        raw,usage,done_reason=response['text'],response.get('usage',{}),response.get('done_reason')
        try:
            summary,hits=validate_summary(raw,query,candidates,config)
            status='valid'
        except (ValueError,TypeError) as error:
            status='invalid_output'
            hits=candidates
            reason=str(error)
    except requests.RequestException as error:
        status='transport_error'
        hits=candidates
        reason=type(error).__name__
    entry=dict(cache_key=key,request=request,status=status,raw_text=raw,summary=summary,hits=hits,
               validation_error=reason,usage=usage,done_reason=done_reason,
               model_call_ms=(perf_counter()-started)*1000,created_at_utc=datetime.now(timezone.utc).isoformat())
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.part')
    temporary.write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(path)
    return entry,False


class SummaryRetriever:
    def __init__(self,base,root,config):
        self.base,self.root,self.config=base,Path(root),config
        self.events=[]
        self.last_summary=None

    def search(self,query,k=5):
        started=perf_counter()
        candidates=self.base.search(query,k=self.config['candidate_k'])
        entry,_=summary_cached(self.root,self.config,query,candidates,cache_only=True)
        self.last_summary=entry['summary']
        upstream=getattr(self.base,'events',[])
        upstream_ms=upstream[-1].get('original_model_call_ms',0) if upstream else 0
        self.events.append(dict(cache_key=entry['cache_key'],status=entry['status'],
                                validation_error=entry['validation_error'],model_call_ms=entry['model_call_ms'],
                                upstream_rewrite_model_call_ms=upstream_ms,replay_ms=(perf_counter()-started)*1000,
                                summary=entry['summary'],candidate_count=len(candidates),output_count=len(entry['hits']),
                                input_characters=sum(len(h['text']) for h in candidates),
                                output_characters=sum(len(h['text']) for h in entry['hits'])))
        return entry['hits'][:k]
