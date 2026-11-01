import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from time import monotonic, sleep

import numpy as np

from evaluate_clause import at5, measure
from hosted_summary import HostedHybridSummaryRetriever, api_payload, cached_gemini_summary, hosted_request
from improve import compact, read_json, verify_freeze
from llm_rewrite import CacheMissError, load_gemini_key
from negative_validation import validate_negatives
from retrieval import load_inputs
from run_experiment import diagnose
from search_service import build_model


def setup(root):
    verify_freeze(root)
    train,documents,manifest = load_inputs(root)
    negatives,frozen = validate_negatives(root,documents)
    negatives = [r for r in negatives if r['split']=='train']
    config = read_json(root/'llm_configs/hybrid_gemini_summary.json')
    base = build_model(Path(config['retrieval_config']).stem,root)
    return config,base,train,negatives,documents,manifest,frozen


def prepare(root):
    config,base,train,negatives,*_ = setup(root)
    entries = []
    skipped = 0
    for record in train+negatives:
        hits = base.search(record['query'],config['candidate_k'])
        if not hits:
            skipped+=1
            continue
        request = hosted_request(root,config,record['query'],hits)
        entries.append(dict(query_id=record['query_id'],payload=api_payload(request)))
    folder = root/'personal_notes'
    folder.mkdir(exist_ok=True)
    (folder/'GEMINI_HYBRID_REQUESTS.json').write_text(json.dumps(dict(model=config['model'],requests=entries),
                                                                  ensure_ascii=False,indent=2),encoding='utf-8')
    print('Train records:',len(train)+len(negatives),'API inputs:',len(entries),'upstream abstentions:',skipped)
    print('Gemini key configured:',bool(load_gemini_key(root)))
    print('Exact payload manifest saved locally; no API calls made.')


def fill(root, max_new, pause):
    config,base,train,negatives,*_ = setup(root)
    if not load_gemini_key(root):
        raise RuntimeError('Gemini key is not configured.')
    made,last_start = 0,None
    counts = Counter()
    for i,record in enumerate(train+negatives,1):
        hits = base.search(record['query'],config['candidate_k'])
        if not hits:
            counts['upstream_abstention']+=1
            continue
        try:
            entry,_ = cached_gemini_summary(root,config,record['query'],hits)
        except CacheMissError:
            if made>=max_new:
                counts['missing']+=1
                continue
            if last_start is not None:
                sleep(max(0,pause-(monotonic()-last_start)))
            last_start = monotonic()
            entry,_ = cached_gemini_summary(root,config,record['query'],hits,cache_only=False)
            made+=1
            print(f"Gemini request {made}: {entry['status']} (train record {i}/163)",flush=True)
        counts[entry['status']]+=1
        if entry['status'] in {'http_error','transport_error'}:
            print('Stopped on provider/transport failure:',entry['validation_error'],flush=True)
            break
    print('Cache status:',dict(counts),flush=True)


def evaluate(root):
    config,base,train,negatives,documents,manifest,frozen = setup(root)
    for record in train+negatives:
        hits = base.search(record['query'],config['candidate_k'])
        if hits:
            cached_gemini_summary(root,config,record['query'],hits)
    reference = measure(base,train,negatives)
    model = HostedHybridSummaryRetriever(base,root,config)
    candidate = measure(model,train,negatives)
    reference_metrics,candidate_metrics = compact(reference),compact(candidate)
    before,after = at5(reference_metrics),at5(candidate_metrics)
    policy = read_json(root/'experiments/abstention_policy_v2.json')
    checks = dict(precision_gain=after['precision']>=before['precision']+.01,
                  recall=after['recall']>=before['recall']-.02,
                  false_abstention=candidate_metrics['false_abstention']<=policy['maximum_false_answerable_abstention_rate'],
                  correct_abstention=candidate_metrics['correct_abstention']>=reference_metrics['correct_abstention'])
    first = [event['model_call_ms']+event['replay_ms'] for event in model.events[:len(train)]]
    first_latency = dict(median=float(np.median(first)),p95=float(np.percentile(first,95)))
    latency_pass = first_latency['p95']<=max(50,2*reference_metrics['latency_ms']['p95'])
    entries = [read_json(root/'cache/gemini_hybrid_summaries'/f"{e['cache_key']}.json")
               for e in model.events if 'cache_key' in e]
    for prediction in candidate['answerable']['predictions']+candidate['negative']['predictions']:
        for hit in prediction['hits']:
            assert hit['text']==documents[hit['file_path']][hit['start']:hit['end']]
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = root/'results/iteration_21_hybrid_gemini'/run_id
    output.mkdir(parents=True,exist_ok=False)
    log = dict(iteration=21,run_id=run_id,proposal='Selected hybrid with cutoff plus Gemini summary and source evidence',
               proposer='User; final hosted LLM experiment',config=config,
               metrics=dict(reference=reference_metrics,candidate=candidate_metrics),checks=checks,
               quality_accepted=all(checks.values()),latency_pass=latency_pass,
               operational_accepted=all(checks.values()) and latency_pass,
               estimated_first_use_latency_ms=first_latency,status_counts=dict(Counter(e['status'] for e in model.events)),
               validation_errors=dict(Counter(e['validation_error'] for e in entries if e['status']!='valid')),
               model_versions=dict(Counter(str(e['response_metadata'].get('model_version')) for e in entries)),
               total_usage={key:sum(e['response_metadata'].get('usage',{}).get(key,0) for e in entries)
                            for key in ['promptTokenCount','candidatesTokenCount','totalTokenCount']},
               prompt_sha256=hashlib.sha256((root/config['prompt_file']).read_bytes()).hexdigest(),
               abstention_policy=policy,diagnosis_after=diagnose(train,candidate['answerable']['predictions']),
               n_answerable_train=len(train),n_unanswerable_train=len(negatives),test_evaluation_runs=0,
               dataset_revision=manifest['revision'],frozen_question_sha256=frozen['query_set_sha256'],
               code_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in
                            ['run_hybrid_gemini.py','hosted_summary.py','summary_retrieval.py','hybrid_retrieval.py','retrieval.py']},
               result_directory=output.relative_to(root).as_posix())
    for name,value in [('reference',reference),('candidate',candidate),('iteration',log),('events',model.events)]:
        (output/f'{name}.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
    with (root/'experiments/llm_log.jsonl').open('a',encoding='utf-8') as handle:
        handle.write(json.dumps(log)+'\n')
    print('Reference P/R:',before['precision'],before['recall'])
    print('Gemini P/R:',after['precision'],after['recall'])
    print('Quality checks:',checks)
    print('Saved:',log['result_directory'])
    return log


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepare',action='store_true',help='Save exact API payload manifest without calling Gemini.')
    parser.add_argument('--fill',action='store_true',help='Permit API calls for missing train caches.')
    parser.add_argument('--max-new',type=int,default=153)
    parser.add_argument('--pause',type=float,default=5)
    args = parser.parse_args()
    if args.max_new<1 or not 5<=args.pause<=60:
        parser.error('max-new must be positive and pause must be 5–60 seconds.')
    root = Path(__file__).resolve().parent
    if args.prepare: prepare(root)
    elif args.fill: fill(root,args.max_new,args.pause)
    else: evaluate(root)
