from project_paths import ROOT
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
import numpy as np
from pathlib import Path
from time import monotonic,sleep

from heldout_evaluation import evaluate_test
from hosted_summary import api_payload,hosted_request
from improve import compact,read_json,verify_freeze
from llm_rewrite import CacheMissError
from negative_validation import validate_negatives
from recall_recovery import make_recovery_model
from retrieval import load_corpus
from search_service import build_model


MODEL_PATHS={'broad10':'llm_configs/hybrid_gemini_broad10.json',
             'recovery20':'llm_configs/hybrid_gemini_recovery20_31.json','baseline':'configs/bm25_baseline.json'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependency_files(root):
    files=set(root.glob('*.py'))|set((root/'src').glob('*.py'))|set((root/'scripts').glob('*.py'))
    pending=[root/p for p in MODEL_PATHS.values()]
    while pending:
        path=pending.pop()
        if path in files:continue
        files.add(path)
        value=read_json(path)
        for key,item in value.items():
            if isinstance(item,str) and (key.endswith('_config') or key=='prompt_file'):
                target=root/item
                if target.suffix=='.json':pending.append(target)
                elif target.exists():files.add(target)
    files.update(root/p for p in ['evaluation/final_test_selection.json','evaluation/unanswerable.json',
                                  'evaluation/frozen_manifest.json','data/prepared/manifest.json'])
    return {p.relative_to(root).as_posix():digest(p) for p in sorted(files)}


def freeze(root):
    verify_freeze(root)
    path=root/'evaluation/execution_freeze.json'
    if path.exists():raise RuntimeError('Execution freeze already exists; inspect it rather than silently replacing it.')
    record=dict(created_at_utc=datetime.now(timezone.utc).isoformat(),files=dependency_files(root),
                selection=read_json(root/'evaluation/final_test_selection.json'),test_evaluation_runs=0)
    path.write_text(json.dumps(record,indent=2),encoding='utf-8')
    print('Execution frozen. No test questions read, no evaluation or API calls.')


def verify_execution(root):
    frozen=read_json(root/'evaluation/execution_freeze.json')
    current=dependency_files(root)
    if current!=frozen['files']:
        changed=sorted(set(current)^set(frozen['files'])|{p for p in current if current[p]!=frozen['files'].get(p)})
        raise RuntimeError('Execution changed after freeze: '+', '.join(changed))
    verify_freeze(root)


def test_records(root):
    verify_execution(root)
    documents,manifest=load_corpus(root)
    path=root/'data/prepared/test.json'
    if digest(path)!=manifest['prepared_sha256']['test']:raise ValueError('Test file hash mismatch.')
    answerable=read_json(path)
    negatives,_=validate_negatives(root,documents)
    negatives=[r for r in negatives if r['split']=='test']
    if len(answerable)!=54 or len(negatives)!=7:raise ValueError('Unexpected frozen test counts.')
    return answerable,negatives,documents


def model_for(root,name):
    config=read_json(root/MODEL_PATHS[name])
    return build_model('bm25_baseline',root) if name=='baseline' else make_recovery_model(root,config)


def pending_payloads(root,name):
    answerable,negatives,_=test_records(root)
    if name=='baseline':raise ValueError('Baseline needs no API calls.')
    model=model_for(root,name)
    payloads=[]
    for record in answerable+negatives:
        if model.previous:
            previous,_=model.previous.resolve(record['query'])
            if previous['status'] in {'http_error','transport_error'}:raise RuntimeError('First-stage provider error remains unresolved.')
            if previous['status']=='valid' and previous['hits']:continue
        hits=model.base.search(record['query'],model.config['candidate_k'])
        if hits:payloads.append(dict(query_id=record['query_id'],payload=api_payload(hosted_request(root,model.config,record['query'],hits))))
    path=root/'personal_notes'/f'FINAL_TEST_{name.upper()}_REQUESTS.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(dict(model=model.config['model'],requests=payloads),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Prepared exact public test-input payloads:',len(payloads),'; no gold labels sent, no evaluation or API calls.')


def fill(root,name,max_new,pause):
    answerable,negatives,_=test_records(root)
    if name=='baseline':raise ValueError('Baseline needs no API generation.')
    model=model_for(root,name)
    made,last=0,None
    for record in answerable+negatives:
        try:entry,_=model.resolve(record['query'])
        except CacheMissError:
            if made>=max_new:raise RuntimeError('Call cap reached; completed responses are preserved.')
            if last is not None:sleep(max(0,pause-(monotonic()-last)))
            last=monotonic()
            entry,_=model.resolve(record['query'],cache_only=False)
            made+=1
            print(f"{name}: new test-input response {made}, {entry['status']}",flush=True)
        if entry['status'] in {'http_error','transport_error'}:
            raise RuntimeError('Stopped on provider failure; cache preserved, no automatic retry.')
    print('Test response preparation complete; retrieval metrics were not calculated.')


def evaluate(root,names,allow_repeat=False):
    answerable,negatives,documents=test_records(root)
    ledger=root/'evaluation/test_runs.jsonl'
    history=[json.loads(line) for line in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
    for name in names:
        if any(r['model']==name and r['status']=='started' for r in history) and not allow_repeat:
            raise RuntimeError('This model was already evaluated/attempted. Read saved results; explicit --allow-repeat records an additional attempt.')
        model=model_for(root,name)
        if name!='baseline':
            for record in answerable+negatives:
                entry,_=model.resolve(record['query'])
                if entry['status'] in {'http_error','transport_error'}:raise RuntimeError('Provider error is not a completed model run.')
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output=root/'results/final_test'/run_id
    output.mkdir(parents=True,exist_ok=False)
    summaries=[]
    for name in names:
        event=dict(run_id=run_id,model=name,status='started',at_utc=datetime.now(timezone.utc).isoformat())
        with ledger.open('a') as handle:handle.write(json.dumps(event)+'\n')
        model=model_for(root,name)
        result=evaluate_test(model,answerable,negatives,documents)
        summary=compact(result)
        events=getattr(model,'events',[])
        first=[e.get('first_stage_model_ms',0)+e.get('additional_model_ms',0)+e['replay_ms'] for e in events[:len(answerable)]]
        keys={e[key] for e in events for key in ['cache_key','first_stage_cache_key'] if e.get(key)}
        responses=[read_json(root/'cache/gemini_hybrid_summaries'/f'{key}.json') for key in keys]
        metadata=dict(model=name,config_path=MODEL_PATHS[name],test_metrics=summary,
                      config=read_json(root/MODEL_PATHS[name]),events=events,
                      evaluation_attempts=1+sum(r['model']==name and r['status']=='started' for r in history),
                      estimated_first_use_latency_ms=dict(median=float(np.median(first)),p95=float(np.percentile(first,95))) if first else summary['latency_ms'],
                      unique_api_responses=len(responses),status_counts=dict(Counter(e.get('status') for e in events)),
                      model_versions=dict(Counter(str(e['response_metadata'].get('model_version')) for e in responses)),
                      api_usage={key:sum(e['response_metadata'].get('usage',{}).get(key,0) for e in responses)
                                 for key in ['promptTokenCount','candidatesTokenCount','totalTokenCount']},
                      freeze_sha256=digest(root/'evaluation/execution_freeze.json'))
        (output/f'{name}.json').write_text(json.dumps(dict(metadata=metadata,predictions=result),indent=2),encoding='utf-8')
        summaries.append(metadata)
        with ledger.open('a') as handle:handle.write(json.dumps(dict(event,status='complete',result_file=(output/f'{name}.json').relative_to(root).as_posix()))+'\n')
    (output/'summary.json').write_text(json.dumps(summaries,indent=2),encoding='utf-8')
    lines=['# Final held-out results','','Only the frozen baseline and two train-selected candidates were evaluated. No test tuning.','',
           '| Model | k | Queries | Precision | Recall | Benchmark precision | Benchmark recall | Hit rate | Correct abstention | False abstention | Cached p50/p95 ms | Test attempts |',
           '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|']
    for record in summaries:
        m=record['test_metrics']
        for v in m['retrieval']:
            lines.append(f"| {record['model']} | {v['k']} | {v['n_queries']} | {v['precision']:.2%} | {v['recall']:.2%} | {v['benchmark_precision']:.2%} | {v['benchmark_recall']:.2%} | {v['hit']:.2%} | {m['negative_counts']['correct']}/7 | {round(m['false_abstention']*54)}/54 | {m['latency_ms']['median']:.2f}/{m['latency_ms']['p95']:.2f} | {record['evaluation_attempts']} |")
    (root/'evaluation/FINAL_TEST_RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    report=root/'REPORT.md'
    if report.exists():
        text=report.read_text(encoding='utf-8')
        start,end='<!-- FINAL_TEST_RESULTS_START -->','<!-- FINAL_TEST_RESULTS_END -->'
        if start in text and end in text:
            prefix=text.split(start)[0]
            suffix=text.split(end,1)[1]
            report.write_text(prefix+start+'\n\n'+'\n'.join(lines[2:])+'\n\n'+end+suffix,encoding='utf-8')
    print('Saved test results:',output)
    print('The ledger records every evaluation attempt; do not tune and rerun silently.')


def main():
    parser=argparse.ArgumentParser(description='Freeze, prepare or evaluate exactly three final candidates. No action by default.')
    actions=parser.add_mutually_exclusive_group()
    actions.add_argument('--freeze',action='store_true')
    actions.add_argument('--prepare',action='store_true')
    actions.add_argument('--fill',action='store_true')
    actions.add_argument('--evaluate',action='store_true')
    parser.add_argument('--model',choices=['all',*MODEL_PATHS],default='all')
    parser.add_argument('--max-new',type=int,default=61)
    parser.add_argument('--pause',type=float,default=5)
    parser.add_argument('--allow-repeat',action='store_true')
    args=parser.parse_args()
    if args.max_new<1 or not 5<=args.pause<=60:parser.error('Use positive max-new and a pause of 5â€“60 seconds.')
    if args.freeze:freeze(ROOT)
    elif args.prepare or args.fill:
        if args.model=='all':parser.error('Prepare/fill one hosted model at a time, broad10 before recovery20.')
        if args.prepare:pending_payloads(ROOT,args.model)
        else:fill(ROOT,args.model,args.max_new,args.pause)
    elif args.evaluate:evaluate(ROOT,list(MODEL_PATHS) if args.model=='all' else [args.model],args.allow_repeat)
    else:
        print('Selected test configurations: Run 1, Run 2, baseline. Test execution is deferred.')
        print('Actions: --freeze; --prepare/--fill --model broad10|recovery20; --evaluate --model all')


if __name__=='__main__':
    main()
