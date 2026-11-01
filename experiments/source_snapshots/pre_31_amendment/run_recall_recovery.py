from project_paths import ROOT as PROJECT_ROOT, source_path
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from time import monotonic,sleep

import numpy as np

from evaluate_clause import at5,measure
from hosted_summary import api_payload,hosted_request
from improve import compact,read_json,verify_freeze
from llm_rewrite import CacheMissError
from negative_validation import validate_negatives
from recall_recovery import make_recovery_model
from retrieval import load_inputs
from run_experiment import diagnose


def setup(root,stage):
    verify_freeze(root)
    train,documents,manifest = load_inputs(root)
    negatives,frozen = validate_negatives(root,documents)
    negatives = [r for r in negatives if r['split']=='train']
    config = read_json(root/f'llm_configs/hybrid_gemini_{stage}.json')
    return config,make_recovery_model(root,config),train,negatives,documents,manifest,frozen


def prepare(root,stage):
    config,model,train,negatives,*_ = setup(root,stage)
    payloads = []
    reused,skipped = 0,0
    for record in train+negatives:
        if model.previous:
            prior,_ = model.previous.resolve(record['query'])
            if prior['status'] in {'http_error','transport_error'}:
                raise RuntimeError('First-stage provider failure remains unresolved.')
            if prior['status']=='valid' and prior['hits']:
                reused+=1
                continue
        hits = model.base.search(record['query'],config['candidate_k'])
        if not hits:
            skipped+=1
            continue
        payloads.append(dict(query_id=record['query_id'],payload=api_payload(hosted_request(root,config,record['query'],hits))))
    path = root/'personal_notes'/f'GEMINI_RECOVERY_{stage.upper()}_REQUESTS.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(dict(model=config['model'],requests=payloads),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Stage:',stage,'API inputs:',len(payloads),'reused answers:',reused,'upstream rejections:',skipped)
    print('Exact payload manifest:',path.name,'; no API calls made.')


def fill(root,stage,max_new,pause):
    _,model,train,negatives,*_ = setup(root,stage)
    made,last_start = 0,None
    counts = Counter()
    for i,record in enumerate(train+negatives,1):
        try:
            entry,decision = model.resolve(record['query'])
        except CacheMissError:
            if made>=max_new:
                counts['missing']+=1
                continue
            if last_start is not None:
                sleep(max(0,pause-(monotonic()-last_start)))
            last_start = monotonic()
            entry,decision = model.resolve(record['query'],cache_only=False)
            made+=1
            print(f"{stage} request {made}: {entry['status']} (train record {i}/163)",flush=True)
        counts[decision['decision']+':'+entry['status']]+=1
        if entry['status'] in {'http_error','transport_error'}:
            print('Stopped on provider failure:',entry.get('validation_error'),flush=True)
            break
    print('Status:',dict(counts),flush=True)


def evaluate(root,stage):
    config,model,train,negatives,documents,manifest,frozen = setup(root,stage)
    for record in train+negatives:
        entry,_ = model.resolve(record['query'])
        if entry['status'] in {'http_error','transport_error'}:
            raise RuntimeError('Provider failure is not a completed model evaluation.')
    candidate = measure(model,train,negatives)
    metrics = compact(candidate)
    m = at5(metrics)
    history = [json.loads(line) for line in (root/'experiments/llm_log.jsonl').read_text().splitlines()]
    original = next(r for r in reversed(history) if r['iteration']==21)
    before = at5(original['metrics']['candidate'])
    targets = dict(precision=m['precision']>=.5,recall=m['recall']>=.7,
                   correct_abstention=candidate['negative']['correct_abstentions']>=20,
                   false_abstention=sum(not p['hits'] for p in candidate['answerable']['predictions'])<=4)
    checks = dict(precision=m['precision']>=.95*before['precision'],recall=m['recall']>=before['recall']+.01,
                  correct_abstention=candidate['negative']['correct_abstentions']>=20,
                  false_abstention=metrics['false_abstention']<=.05)
    events = model.events
    first = [e['first_stage_model_ms']+e['additional_model_ms']+e['replay_ms'] for e in events[:len(train)]]
    entries = {e['cache_key']:read_json(root/'cache/gemini_hybrid_summaries'/f"{e['cache_key']}.json")
               for e in events if 'cache_key' in e}
    additional_keys = {e['cache_key'] for e in events if e['decision']!='reuse_supported_answer' and 'cache_key' in e}
    for prediction in candidate['answerable']['predictions']+candidate['negative']['predictions']:
        for hit in prediction['hits']:
            assert hit['text']==documents[hit['file_path']][hit['start']:hit['end']]
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    iteration = 22 if stage=='broad10' else 23
    output = root/f'results/iteration_{iteration}_{stage}'/run_id
    output.mkdir(parents=True,exist_ok=False)
    log = dict(iteration=iteration,run_id=run_id,proposal='Broader evidence and lower cutoff' if iteration==22 else 'Conditional expanded-context recovery',
               proposer='User; two recall-recovery experiments declared before generation',config=config,
               metrics=dict(reference=original['metrics']['candidate'],candidate=metrics),
               target_checks=targets,target_success=all(targets.values()),checks=checks,quality_accepted=all(checks.values()),
               status_counts=dict(Counter(e['status'] for e in events)),decision_counts=dict(Counter(e['decision'] for e in events)),
               validation_errors=dict(Counter(e['validation_error'] for e in entries.values() if e['status']!='valid')),
               additional_api_requests=len(additional_keys),
               additional_token_usage={key:sum(entries[k]['response_metadata'].get('usage',{}).get(key,0) for k in additional_keys)
                                       for key in ['promptTokenCount','candidatesTokenCount','totalTokenCount']},
               model_versions=dict(Counter(str(e['response_metadata'].get('model_version')) for e in entries.values())),
               estimated_first_use_latency_ms=dict(median=float(np.median(first)),p95=float(np.percentile(first,95))),
               diagnosis_after=diagnose(train,candidate['answerable']['predictions']),
               n_answerable_train=len(train),n_unanswerable_train=len(negatives),test_evaluation_runs=0,
               dataset_revision=manifest['revision'],frozen_question_sha256=frozen['query_set_sha256'],
               prompt_sha256=hashlib.sha256((root/config['prompt_file']).read_bytes()).hexdigest(),
               code_sha256={name:hashlib.sha256(source_path(root,name).read_bytes()).hexdigest() for name in
                            ['recall_recovery.py','run_recall_recovery.py','hosted_summary.py','hybrid_retrieval.py']},
               result_directory=output.relative_to(root).as_posix())
    for name,value in [('candidate',candidate),('iteration',log),('events',events)]:
        (output/f'{name}.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
    with (root/'experiments/llm_log.jsonl').open('a',encoding='utf-8') as handle:
        handle.write(json.dumps(log)+'\n')
    print('Stage:',stage,'P/R:',m['precision'],m['recall'])
    print('Abstention:',metrics['negative_counts'],metrics['false_abstention'])
    print('Target checks:',targets,'Guardrail checks:',checks)
    print('Saved:',log['result_directory'])
    return log


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage',choices=['broad10','recovery20'],required=True)
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--fill',action='store_true')
    parser.add_argument('--max-new',type=int,default=163)
    parser.add_argument('--pause',type=float,default=5)
    args = parser.parse_args()
    if args.max_new<1 or not 5<=args.pause<=60: parser.error('Use positive max-new and a pause from 5 to 60 seconds.')
    root = PROJECT_ROOT
    if args.prepare: prepare(root,args.stage)
    elif args.fill: fill(root,args.stage,args.max_new,args.pause)
    else: evaluate(root,args.stage)
