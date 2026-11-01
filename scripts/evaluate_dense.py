from project_paths import ROOT as PROJECT_ROOT, source_path
from collections import Counter
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from dense_retrieval import DenseRetriever
from improve import compact,read_json,read_log,verify_freeze
from negative_validation import evaluate_negative_train,validate_negatives
from retrieval import evaluate_train,load_inputs
from run_experiment import decide,diagnose,evaluate_config


def run(root):
    root=Path(root).resolve()
    verify_freeze(root)
    if not any(r['iteration']==10 for r in read_log(root/'experiments/llm_log.jsonl')):
        raise ValueError('Complete the recorded BM25/LLM phase first.')
    config=read_json(root/'semantic_configs/minilm.json')
    train,documents,manifest=load_inputs(root)
    negatives,frozen=validate_negatives(root,documents)
    negatives=[r for r in negatives if r['split']=='train']
    started=perf_counter()
    model=DenseRetriever(documents,config,root)
    build_seconds=perf_counter()-started
    answerable=evaluate_train(model,train,config['k_values'])
    answerable_events=list(model.events)
    negative=evaluate_negative_train(model,negatives)
    candidate=dict(config=config,answerable=answerable,negative=negative,build_seconds=build_seconds,
                   document_embedding_metadata=model.metadata,events=model.events)
    reference_config=read_json(root/'configs/bm25_focused_stemmed.json')
    reference=evaluate_config(reference_config,documents,train,negatives)
    baseline=evaluate_config(read_json(root/'configs/bm25_baseline.json'),documents,train,negatives)
    objective=read_json(root/'experiments/objective.json')
    adjusted=deepcopy(candidate)
    first=[e['estimated_first_use_ms'] for e in answerable_events]
    adjusted['answerable']['latency_ms']=dict(median=float(np.median(first)),p95=float(np.percentile(first,95)))
    decision=decide(reference,adjusted,objective)
    run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output=root/'results/iteration_11'/run_id
    output.mkdir(parents=True,exist_ok=False)
    log=dict(iteration=11,run_id=run_id,proposal='Pure local MiniLM embeddings plus exact FAISS search',
             proposer='Codex; basic semantic comparison declared before measurement',
             reference_config=reference_config,candidate_config=config,objective=objective,decision=decision,
             selected_config=config if decision['accepted'] else reference_config,
             observed_timing_decision=decide(reference,candidate,objective),
             metrics={label:compact(result) for label,result in [('baseline',baseline),('reference',reference),('candidate',candidate)]},
             estimated_first_use_latency_ms=adjusted['answerable']['latency_ms'],
             document_inputs_over_token_limit=model.metadata['inputs_over_token_limit'],
             query_inputs_over_token_limit=sum(e['input_tokens']>config['max_seq_length'] for e in model.events),
             cache_hits=dict(Counter('hit' if e['query_cached'] else 'miss' for e in model.events)),
             build_seconds=build_seconds,vector_cache_directory=model.cache_dir.relative_to(root).as_posix(),
             diagnosis_before=diagnose(train,reference['answerable']['predictions']),
             diagnosis_after=diagnose(train,answerable['predictions']),
             n_answerable_train=len(train),n_unanswerable_train=len(negatives),test_evaluation_runs=0,
             dataset_revision=manifest['revision'],frozen_question_sha256=frozen['query_set_sha256'],
             packages={p:importlib.metadata.version(p) for p in ['faiss-cpu','sentence-transformers','transformers','torch']},
             code_sha256={p:hashlib.sha256(source_path(root,p).read_bytes()).hexdigest() for p in ['dense_retrieval.py','evaluate_dense.py','retrieval.py']},
             result_directory=output.relative_to(root).as_posix())
    for name,value in [('baseline',baseline),('reference',reference),('candidate',candidate),('iteration',log)]:
        (output/f'{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    with (root/'experiments/semantic_log.jsonl').open('a',encoding='utf-8') as handle:
        handle.write(json.dumps(log,ensure_ascii=False)+'\n')
    return log


if __name__=='__main__':
    log=run(PROJECT_ROOT)
    print('Iteration:',log['iteration'])
    print('Decision:',log['decision'])
    print('Truncated document/query inputs:',log['document_inputs_over_token_limit'],log['query_inputs_over_token_limit'])
    print('Saved:',log['result_directory'])
