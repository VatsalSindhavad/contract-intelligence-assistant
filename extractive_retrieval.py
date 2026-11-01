import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from time import perf_counter

import requests

from llm_rewrite import CacheMissError,canonical


def extraction_request(root,config,query,candidates):
    prompt=(Path(root)/config['prompt_file']).read_text(encoding='utf-8')
    schema={'type':'object','properties':{'passage_id':{'type':'integer','minimum':0,'maximum':len(candidates)},
                                         'answer':{'type':'string'}},
            'required':['passage_id','answer'],'additionalProperties':False}
    model_input=dict(question=query,passages=[dict(passage_id=i,text=h['text']) for i,h in enumerate(candidates,1)])
    settings={k:config[k] for k in ['model','model_revision','runtime','temperature','seed','max_output_tokens','context_length']}
    request=dict(prompt=prompt,input=model_input,schema=schema,settings=settings,candidates=candidates,
                 protocol=1,invalid_output_policy=config['invalid_output_policy'])
    conservative_bound=len((prompt+json.dumps(model_input,ensure_ascii=False)+json.dumps(schema)).encode('utf-8'))+512+config['max_output_tokens']
    if conservative_bound>config['context_length']:
        raise ValueError('Input exceeds conservative context bound; no passages were silently truncated.')
    return request


def validate_extraction(raw,candidates):
    value=json.loads(raw)
    if not isinstance(value,dict) or set(value)!={'passage_id','answer'}:
        raise ValueError('Expected passage_id and answer only.')
    identifier,answer=value['passage_id'],value['answer']
    if type(identifier) is not int or not isinstance(answer,str):
        raise ValueError('Invalid output types.')
    if identifier==0 and answer=='':
        return []
    if not 1<=identifier<=len(candidates) or not answer.strip():
        raise ValueError('Invalid passage ID or empty answer.')
    passage=candidates[identifier-1]
    if passage['end']-passage['start']!=len(passage['text']):
        raise ValueError('Candidate source offsets do not match its text length.')
    position=passage['text'].find(answer)
    if position<0:
        raise ValueError('Answer is not an exact substring of the cited passage.')
    if passage['text'].find(answer,position+1)>=0:
        raise ValueError('Answer occurs more than once; source offset is ambiguous.')
    start=passage['start']+position
    return [dict(file_path=passage['file_path'],start=start,end=start+len(answer),text=answer,
                 score=passage['score'])]


def local_extract(request):
    s=request['settings']
    payload=dict(model=s['model'],system=request['prompt'],
                 prompt=json.dumps(request['input'],ensure_ascii=False),format=request['schema'],
                 stream=False,keep_alive='10m',options=dict(temperature=s['temperature'],seed=s['seed'],
                                                         num_predict=s['max_output_tokens'],num_ctx=s['context_length']))
    response=requests.post('http://127.0.0.1:11434/api/generate',json=payload,timeout=240)
    response.raise_for_status()
    data=response.json()
    return dict(text=data.get('response',''),usage={k:data.get(k) for k in
                ['prompt_eval_count','eval_count','total_duration','load_duration','eval_duration']},
                done_reason=data.get('done_reason'))


def extract_cached(root,config,query,candidates,cache_only=True,caller=local_extract):
    request=extraction_request(root,config,query,candidates)
    key=hashlib.sha256(canonical(request).encode('utf-8')).hexdigest()
    path=Path(root)/'cache/local_extractions'/f'{key}.json'
    if path.exists():
        entry=json.loads(path.read_text(encoding='utf-8'))
        if entry['request']!=request or entry['cache_key']!=key:
            raise ValueError('Extraction-cache identity mismatch.')
        if entry['status']=='valid':
            expected=validate_extraction(entry['raw_text'],candidates)
        else:
            expected=candidates
        if expected!=entry['hits']:
            raise ValueError('Cached source extraction does not match validated evidence.')
        return entry,True
    if cache_only:
        raise CacheMissError(f'Missing local-extraction cache: {key}. No model call was made.')
    started=perf_counter()
    raw,usage,done_reason='',{},None
    try:
        result=caller(request)
        raw,usage,done_reason=result['text'],result.get('usage',{}),result.get('done_reason')
        try:
            hits=validate_extraction(raw,candidates)
            status='valid'
            reason=None
        except (ValueError,TypeError) as error:
            status='invalid_output'
            hits=candidates
            reason=str(error)
    except requests.RequestException as error:
        status='transport_error'
        hits=candidates
        reason=type(error).__name__
    entry=dict(cache_key=key,request=request,status=status,raw_text=raw,hits=hits,
               validation_error=reason,usage=usage,done_reason=done_reason,
               model_call_ms=(perf_counter()-started)*1000,created_at_utc=datetime.now(timezone.utc).isoformat())
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.part')
    temporary.write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf-8')
    temporary.replace(path)
    return entry,False


class ExtractiveRetriever:
    def __init__(self,base,root,config):
        self.base,self.root,self.config=base,Path(root),config
        self.events=[]

    def search(self,query,k=5):
        started=perf_counter()
        candidates=self.base.search(query,k=self.config['candidate_k'])
        upstream=getattr(self.base,'events',[])
        upstream_ms=upstream[-1].get('original_model_call_ms',0) if upstream else 0
        entry,_=extract_cached(self.root,self.config,query,candidates,cache_only=True)
        self.events.append(dict(cache_key=entry['cache_key'],status=entry['status'],
                                validation_error=entry['validation_error'],model_call_ms=entry['model_call_ms'],
                                upstream_rewrite_model_call_ms=upstream_ms,
                                replay_ms=(perf_counter()-started)*1000,
                                input_characters=sum(len(h['text']) for h in candidates),
                                output_characters=sum(len(h['text']) for h in entry['hits']),
                                candidate_count=len(candidates),output_count=len(entry['hits'])))
        return entry['hits'][:k]
