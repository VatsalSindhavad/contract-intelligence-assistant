from project_paths import ROOT as PROJECT_ROOT, source_path
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import requests

from extractive_retrieval import ExtractiveRetriever,extract_cached,extraction_request
from improve import compact,read_json,verify_freeze
from llm_rewrite import RewriteRetriever
from negative_validation import evaluate_negative_train,validate_negatives
from retrieval import BM25Retriever,evaluate_train,load_inputs
from run_experiment import diagnose


def select_pilot(records,n):
    if any(r['split']!='train' for r in records):
        raise ValueError('Pilot selection accepts train only.')
    return sorted(records,key=lambda r:hashlib.sha256(r['query'].strip().encode('utf-8')).hexdigest())[:n]


def precision_decision(reference,candidate,policy):
    before=next(m for m in reference['answerable']['metrics'] if m['k']==5)
    after=next(m for m in candidate['answerable']['metrics'] if m['k']==5)
    checks=dict(precision_gain=after['precision']>=before['precision']+policy['minimum_precision_gain_absolute'],
                recall=after['recall']>=before['recall']-policy['maximum_recall_drop_absolute'],
                answerable_abstention=candidate['answerable']['answerable_false_abstention_rate']<=reference['answerable']['answerable_false_abstention_rate']+policy['maximum_false_abstention_increase_absolute'],
                negative_abstention=candidate['negative']['correct_abstention_rate']>=reference['negative']['correct_abstention_rate']-policy['maximum_correct_abstention_drop_absolute'])
    return dict(quality_pass=all(checks.values()),checks=checks)


def setup(root):
    verify_freeze(root)
    config=read_json(root/'llm_configs/local_phi3_extract.json')
    train,documents,_=load_inputs(root)
    negatives,_=validate_negatives(root,documents)
    positives=select_pilot(train,config['pilot_answerable_count'])
    negatives=select_pilot([r for r in negatives if r['split']=='train'],config['pilot_negative_count'])
    rewrite=read_json(root/config['retrieval_config'])
    base=RewriteRetriever(BM25Retriever(documents,read_json(root/rewrite['baseline_config'])),root,rewrite)
    return config,positives,negatives,base,documents


def fill(root,max_new):
    config,positives,negatives,base,_=setup(root)
    tags=requests.get('http://127.0.0.1:11434/api/tags',timeout=10).json()['models']
    version=requests.get('http://127.0.0.1:11434/api/version',timeout=10).json()['version']
    if not any(m['name']==config['model'] and m['digest']==config['model_revision'] for m in tags) or config['runtime']!='ollama-'+version:
        raise ValueError('Local model/runtime differs from the declared extraction setup.')
    records=positives+negatives
    requests_to_make=[]
    for record in records:
        candidates=base.search(record['query'],config['candidate_k'])
        extraction_request(root,config,record['query'],candidates)
        requests_to_make.append((record['query'],candidates))
    print('All pilot inputs fit the conservative context bound; no example or gold answer is included.',flush=True)
    made=0
    statuses=Counter()
    for query,candidates in requests_to_make:
        from llm_rewrite import CacheMissError
        try:
            entry,_=extract_cached(root,config,query,candidates,cache_only=True)
        except CacheMissError:
            if made>=max_new:
                statuses['missing']+=1
                continue
            entry,_=extract_cached(root,config,query,candidates,cache_only=False)
            made+=1
            print(f"New local extraction {made}: {entry['status']}; returned passages {len(entry['hits'])}",flush=True)
        statuses[entry['status']]+=1
        if entry['status']=='transport_error':
            print('Stopped after transport failure; original-candidate fallback is cached.',flush=True)
            break
    print('Pilot cache status:',dict(statuses))


def evaluate(root):
    config,positives,negatives,base,documents=setup(root)
    policy=read_json(root/'experiments/precision_objective.json')
    for record in positives+negatives:
        extract_cached(root,config,record['query'],base.search(record['query'],config['candidate_k']),cache_only=True)
    reference_start=len(base.events)
    reference=dict(answerable=evaluate_train(base,positives,[1,3,5,10]),
                   negative=evaluate_negative_train(base,negatives))
    reference_events=base.events[reference_start:reference_start+len(positives)]
    reference_first=[e['original_model_call_ms']+p['latency_ms'] for e,p in zip(reference_events,reference['answerable']['predictions'])]
    model=ExtractiveRetriever(base,root,config)
    answerable=evaluate_train(model,positives,[1,3,5,10])
    answer_events=list(model.events)
    negative=evaluate_negative_train(model,negatives)
    for prediction in answerable['predictions']+negative['predictions']:
        for hit in prediction['hits']:
            if documents[hit['file_path']][hit['start']:hit['end']]!=hit['text']:
                raise ValueError('Returned excerpt does not match its source offsets.')
    candidate=dict(answerable=answerable,negative=negative)
    decision=precision_decision(reference,candidate,policy)
    first=[e['model_call_ms']+e['upstream_rewrite_model_call_ms']+e['replay_ms'] for e in answer_events]
    first_use=dict(median=float(np.median(first)),p95=float(np.percentile(first,95)))
    latency_pass=first_use['p95']<=max(policy['latency_p95_floor_ms'],reference['answerable']['latency_ms']['p95']*policy['latency_p95_multiplier'])
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output=root/'results/iteration_12_precision_pilot'/run_id
    output.mkdir(parents=True,exist_ok=False)
    log=dict(iteration=12,scope='pilot only; not comparable with full-train aggregates',run_id=run_id,
             proposer='User instruction: exact one-line answer; local instruction-only prompt, no example',
             model_config=config,policy=policy,quality_decision=decision,
             operational_accepted=decision['quality_pass'] and latency_pass,latency_pass=latency_pass,
             estimated_first_use_latency_ms=first_use,
             reference_estimated_first_use_latency_ms=dict(median=float(np.median(reference_first)),p95=float(np.percentile(reference_first,95))),
             timing_note='Candidate first-use estimate includes upstream rewrite and extraction generation plus replay retrieval; quality gates are unchanged.',
             metrics={label:compact(value) for label,value in [('reference',reference),('candidate',candidate)]},
             diagnosis_before=diagnose(positives,reference['answerable']['predictions']),
             diagnosis_after=diagnose(positives,answerable['predictions']),
             pilot_ids=dict(answerable=[r['query_id'] for r in positives],negative=[r['query_id'] for r in negatives]),
             status_counts=dict(Counter(e['status'] for e in model.events)),
             mean_input_characters=float(np.mean([e['input_characters'] for e in answer_events])),
             mean_output_characters=float(np.mean([e['output_characters'] for e in answer_events])),
             n_answerable_train=len(positives),n_negative_train=len(negatives),test_evaluation_runs=0,
             prompt_sha256=hashlib.sha256((root/config['prompt_file']).read_bytes()).hexdigest(),
             code_sha256={p:hashlib.sha256(source_path(root,p).read_bytes()).hexdigest() for p in ['extractive_retrieval.py','run_precision_pilot.py']},
             result_directory=output.relative_to(root).as_posix())
    for name,value in [('reference',reference),('candidate',candidate),('events',model.events),('iteration',log)]:
        (output/f'{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    with (root/'experiments/precision_log.jsonl').open('a',encoding='utf-8') as handle:
        handle.write(json.dumps(log,ensure_ascii=False)+'\n')
    return log


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Prepare or score the fixed local exact-excerpt pilot.')
    parser.add_argument('--fill',action='store_true')
    parser.add_argument('--max-new',type=int,default=1)
    args=parser.parse_args()
    root=PROJECT_ROOT
    if args.fill:
        if args.max_new<1:parser.error('--max-new must be positive.')
        fill(root,args.max_new)
    else:
        log=evaluate(root)
        print('Pilot quality decision:',log['quality_decision'])
        print('Operational accepted:',log['operational_accepted'])
        print('Saved:',log['result_directory'])
