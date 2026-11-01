from project_paths import ROOT as PROJECT_ROOT, source_path
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

from dense_retrieval import DenseRetriever
from evaluate_clause import at5, measure
from hybrid_retrieval import HybridRetriever
from improve import compact, read_json, verify_freeze
from negative_validation import validate_negatives
from rerank_retrieval import RerankRetriever
from retrieval import BM25Retriever, load_inputs
from run_experiment import diagnose


def run(root, fill=False):
    root = Path(root)
    verify_freeze(root)
    train,documents,manifest = load_inputs(root)
    negatives,frozen = validate_negatives(root,documents)
    negatives = [r for r in negatives if r['split']=='train']
    config = read_json(root/'semantic_configs/hybrid_reranked.json')
    hybrid_config = read_json(root/config['base_config'])
    base = HybridRetriever(BM25Retriever(documents,read_json(root/hybrid_config['bm25_config'])),
                           DenseRetriever(documents,read_json(root/hybrid_config['dense_config']),root),hybrid_config)
    if fill:
        preparation = RerankRetriever(base,root,config,allow_inference=True)
        for i,record in enumerate(train+negatives,1):
            preparation.search(record['query'])
            if i%20==0 or i==len(train+negatives):
                print(f'Local reranker prepared {i}/{len(train+negatives)}',flush=True)
    reference = measure(base,train,negatives)
    model = RerankRetriever(base,root,config)
    candidate = measure(model,train,negatives)
    reference_metrics,candidate_metrics = compact(reference),compact(candidate)
    before,after = at5(reference_metrics),at5(candidate_metrics)
    policy = read_json(root/'experiments/abstention_policy_v2.json')
    checks = dict(recall_gain=after['recall']>=before['recall']+.01,
                  precision=after['precision']>=before['precision']*.95,
                  false_abstention=candidate_metrics['false_abstention']<=policy['maximum_false_answerable_abstention_rate'],
                  correct_abstention=candidate_metrics['correct_abstention']>=reference_metrics['correct_abstention'])
    events = model.events[:len(train)]
    first = [e['model_ms']+e['replay_ms'] for e in events]
    first_latency = dict(median=float(np.median(first)),p95=float(np.percentile(first,95)))
    latency_pass = first_latency['p95']<=max(50,2*reference_metrics['latency_ms']['p95'])
    for prediction in candidate['answerable']['predictions']+candidate['negative']['predictions']:
        for hit in prediction['hits']:
            assert hit['text']==documents[hit['file_path']][hit['start']:hit['end']]
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = root/'results/iteration_20_reranker'/run_id
    output.mkdir(parents=True,exist_ok=False)
    log = dict(iteration=20,run_id=run_id,proposal='Local MiniLM cross-encoder reranks hybrid top 20; unchanged 0.55 gate',
               proposer='User; local reranker declared before measurement',config=config,
               metrics=dict(reference=reference_metrics,candidate=candidate_metrics),checks=checks,
               quality_accepted=all(checks.values()),operational_accepted=all(checks.values()) and latency_pass,
               latency_pass=latency_pass,estimated_first_use_latency_ms=first_latency,
               timing_excludes='One-time model/index load and initial public model download',
               pair_count=sum(e['pair_count'] for e in model.events),
               truncated_pairs=sum(e['truncated_pairs'] for e in model.events),
               abstention_policy=policy,diagnosis_after=diagnose(train,candidate['answerable']['predictions']),
               n_answerable_train=len(train),n_unanswerable_train=len(negatives),test_evaluation_runs=0,
               dataset_revision=manifest['revision'],frozen_question_sha256=frozen['query_set_sha256'],
               code_sha256={name:hashlib.sha256(source_path(root,name).read_bytes()).hexdigest() for name in
                            ['rerank_retrieval.py','evaluate_reranker.py','hybrid_retrieval.py','retrieval.py']},
               result_directory=output.relative_to(root).as_posix())
    for name,value in [('reference',reference),('candidate',candidate),('iteration',log),('events',model.events)]:
        (output/f'{name}.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
    with (root/'experiments/semantic_log.jsonl').open('a',encoding='utf-8') as handle:
        handle.write(json.dumps(log)+'\n')
    print('Reference P/R:',before['precision'],before['recall'])
    print('Reranked P/R:',after['precision'],after['recall'])
    print('Quality checks:',checks)
    print('Saved:',log['result_directory'])
    return log


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fill',action='store_true',help='Permit local reranker inference for missing score caches.')
    args = parser.parse_args()
    run(PROJECT_ROOT,args.fill)
