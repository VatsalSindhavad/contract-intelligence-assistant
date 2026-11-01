from project_paths import ROOT as PROJECT_ROOT, source_path
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import requests

from improve import compact,read_json,verify_freeze
from llm_rewrite import CacheMissError,RewriteRetriever
from negative_validation import evaluate_negative_train,validate_negatives
from retrieval import BM25Retriever,evaluate_train,load_inputs
from run_experiment import diagnose,evaluate_config
from summary_retrieval import SummaryRetriever,summary_cached,summary_request


def setup(root):
    verify_freeze(root)
    config=read_json(root/'llm_configs/local_phi3_summary.json')
    train,documents,manifest=load_inputs(root)
    negatives,frozen=validate_negatives(root,documents)
    negatives=[r for r in negatives if r['split']=='train']
    rewrite=read_json(root/config['retrieval_config'])
    base_config=read_json(root/rewrite['baseline_config'])
    base=RewriteRetriever(BM25Retriever(documents,base_config),root,rewrite)
    return config,train,negatives,base,documents,manifest,frozen,base_config


def quality_decision(reference,candidate,policy):
    before=next(m for m in reference['answerable']['metrics'] if m['k']==5)
    after=next(m for m in candidate['answerable']['metrics'] if m['k']==5)
    checks=dict(precision_gain=after['precision']>=before['precision']+policy['minimum_precision_gain_absolute'],
                recall=after['recall']>=before['recall']-policy['maximum_recall_drop_absolute'],
                answerable_abstention=candidate['answerable']['answerable_false_abstention_rate']<=reference['answerable']['answerable_false_abstention_rate']+policy['maximum_false_abstention_increase_absolute'],
                negative_abstention=candidate['negative']['correct_abstention_rate']>=reference['negative']['correct_abstention_rate']-policy['maximum_correct_abstention_drop_absolute'])
    return dict(quality_pass=all(checks.values()),checks=checks)


def fill(root,max_new):
    config,train,negatives,base,*_=setup(root)
    tags=requests.get('http://127.0.0.1:11434/api/tags',timeout=10).json()['models']
    version=requests.get('http://127.0.0.1:11434/api/version',timeout=10).json()['version']
    if not any(m['name']==config['model'] and m['digest']==config['model_revision'] for m in tags) or config['runtime']!='ollama-'+version:
        raise ValueError('Local model/runtime does not match the declared summary configuration.')
    inputs=[]
    for record in train+negatives:
        candidates=base.search(record['query'],config['candidate_k'])
        summary_request(root,config,record['query'],candidates)
        inputs.append((record['query'],candidates))
    print(f'Full train set: {len(train)} answerable + {len(negatives)} negative; all inputs fit the context bound.',flush=True)
    made=0
    counts=Counter()
    for query,candidates in inputs:
        try:
            entry,_=summary_cached(root,config,query,candidates,cache_only=True)
        except CacheMissError:
            if made>=max_new:
                counts['missing']+=1
                continue
            entry,_=summary_cached(root,config,query,candidates,cache_only=False)
            made+=1
            print(f"Local summary {made}: {entry['status']}; evidence passages {len(entry['hits'])}",flush=True)
        counts[entry['status']]+=1
        if entry['status']=='transport_error':
            print('Stopped after local transport failure; fallback and failure are preserved.',flush=True)
            break
    print('Cache status:',dict(counts))


def evaluate(root):
    config,train,negatives,base,documents,manifest,frozen,base_config=setup(root)
    policy=read_json(root/'experiments/summary_objective.json')
    for record in train+negatives:
        summary_cached(root,config,record['query'],base.search(record['query'],config['candidate_k']),cache_only=True)
    start=len(base.events)
    reference=dict(answerable=evaluate_train(base,train,[1,3,5,10]),negative=evaluate_negative_train(base,negatives))
    ref_events=base.events[start:start+len(train)]
    model=SummaryRetriever(base,root,config)
    answerable=evaluate_train(model,train,[1,3,5,10])
    answer_events=list(model.events)
    negative=evaluate_negative_train(model,negatives)
    for prediction in answerable['predictions']+negative['predictions']:
        for hit in prediction['hits']:
            if documents[hit['file_path']][hit['start']:hit['end']]!=hit['text']:
                raise ValueError('Returned summary evidence does not match the original source offsets.')
    candidate=dict(answerable=answerable,negative=negative)
    first=[e['model_call_ms']+e['upstream_rewrite_model_call_ms']+e['replay_ms'] for e in answer_events]
    ref_first=[e['original_model_call_ms']+p['latency_ms'] for e,p in zip(ref_events,reference['answerable']['predictions'])]
    first_use=dict(median=float(np.median(first)),p95=float(np.percentile(first,95)))
    decision=quality_decision(reference,candidate,policy)
    latency_pass=first_use['p95']<=max(policy['latency_p95_floor_ms'],reference['answerable']['latency_ms']['p95']*policy['latency_p95_multiplier'])
    best=evaluate_config(base_config,documents,train,negatives)
    baseline=evaluate_config(read_json(root/'configs/bm25_baseline.json'),documents,train,negatives)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output=root/'results/iteration_13_phi3_summary'/run_id
    output.mkdir(parents=True,exist_ok=False)
    entries=[read_json(root/'cache/local_summaries'/f"{e['cache_key']}.json") for e in model.events]
    log=dict(iteration=13,scope='full train: 140 answerable and 23 negative queries',run_id=run_id,
             proposer='User: one-shot 1–2 line summary containing supported answer; exact evidence added for valid retrieval scoring',
             model_config=config,policy=policy,quality_decision=decision,
             operational_accepted=decision['quality_pass'] and latency_pass,latency_pass=latency_pass,
             estimated_first_use_latency_ms=first_use,
             reference_estimated_first_use_latency_ms=dict(median=float(np.median(ref_first)),p95=float(np.percentile(ref_first,95))),
             metrics={label:compact(value) for label,value in [('baseline',baseline),('best_bm25',best),('reference',reference),('candidate',candidate)]},
             diagnosis_before=diagnose(train,reference['answerable']['predictions']),diagnosis_after=diagnose(train,answerable['predictions']),
             status_counts=dict(Counter(e['status'] for e in model.events)),
             validation_errors=dict(Counter(e['validation_error'] for e in entries if e['status']!='valid')),
             output_truncation_count=sum(e['done_reason']=='length' for e in entries),
             mean_input_characters=float(np.mean([e['input_characters'] for e in answer_events])),
             mean_output_characters=float(np.mean([e['output_characters'] for e in answer_events])),
             record_ids=dict(answerable=[r['query_id'] for r in train],negative=[r['query_id'] for r in negatives]),
             n_answerable_train=len(train),n_negative_train=len(negatives),test_evaluation_runs=0,
             dataset_revision=manifest['revision'],frozen_question_sha256=frozen['query_set_sha256'],
             prompt_sha256=hashlib.sha256((root/config['prompt_file']).read_bytes()).hexdigest(),
             cache_sha256={e['cache_key']:hashlib.sha256((root/'cache/local_summaries'/f"{e['cache_key']}.json").read_bytes()).hexdigest() for e in entries},
             code_sha256={p:hashlib.sha256(source_path(root,p).read_bytes()).hexdigest() for p in ['summary_retrieval.py','run_summary_experiment.py']},
             result_directory=output.relative_to(root).as_posix())
    for name,value in [('baseline',baseline),('best_bm25',best),('reference',reference),('candidate',candidate),('events',model.events),('iteration',log)]:
        (output/f'{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    with (root/'experiments/summary_log.jsonl').open('a',encoding='utf-8') as handle:
        handle.write(json.dumps(log,ensure_ascii=False)+'\n')
    return log


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Populate or replay the full-train local one-shot summary experiment.')
    parser.add_argument('--fill',action='store_true')
    parser.add_argument('--max-new',type=int,default=163)
    args=parser.parse_args()
    if args.max_new<1:parser.error('--max-new must be positive.')
    root=PROJECT_ROOT
    if args.fill:
        fill(root,args.max_new)
    else:
        log=evaluate(root)
        print('Full-train quality decision:',log['quality_decision'])
        print('Operational accepted:',log['operational_accepted'])
        print('Saved:',log['result_directory'])
