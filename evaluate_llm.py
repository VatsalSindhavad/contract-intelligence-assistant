import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np

from improve import compact, read_json, read_log, verify_freeze
from llm_rewrite import RewriteRetriever, get_rewrite
from negative_validation import evaluate_negative_train, validate_negatives
from prepare_llm import train_questions
from retrieval import BM25Retriever, evaluate_train, load_inputs
from run_experiment import decide, diagnose, evaluate_config


def first_use_decision(reference, candidate, events, objective):
    estimates = [e['original_model_call_ms'] + e['cache_retrieval_ms'] for e in events]
    adjusted = deepcopy(candidate)
    adjusted['answerable']['latency_ms'] = dict(median=float(np.median(estimates)),
                                              p95=float(np.percentile(estimates, 95)))
    return decide(reference, adjusted, objective), adjusted['answerable']['latency_ms']


def run_evaluation(root, config_name):
    root = Path(root).resolve()
    verify_freeze(root)
    model_config = read_json(root / 'llm_configs' / f'{config_name}.json')
    iteration = 9 if config_name == 'gemini' else 10
    if iteration == 10 and not any(r['iteration'] == 9 for r in read_log(root / 'experiments/llm_log.jsonl')):
        raise ValueError('Complete hosted iteration 9 first.')
    entries = [get_rewrite(root, model_config, q, cache_only=True)[0] for q in train_questions(root)]
    train, documents, manifest = load_inputs(root)
    negatives, frozen = validate_negatives(root, documents)
    negatives = [r for r in negatives if r['split'] == 'train']
    base_config = read_json(root / model_config['baseline_config'])
    objective = read_json(root / 'experiments/objective.json')
    reference = evaluate_config(base_config, documents, train, negatives)
    baseline = evaluate_config(read_json(root / 'configs/bm25_baseline.json'), documents, train, negatives)
    wrapper = RewriteRetriever(BM25Retriever(documents, base_config), root, model_config)
    answerable = evaluate_train(wrapper, train, base_config['k_values'])
    answerable_events = list(wrapper.events)
    negative = evaluate_negative_train(wrapper, negatives)
    candidate = dict(config=model_config, answerable=answerable, negative=negative)
    decision, first_use_ms = first_use_decision(reference, candidate, answerable_events, objective)
    replay_decision = decide(reference, candidate, objective)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = root / 'results' / f'iteration_{iteration:02d}' / run_id
    output.mkdir(parents=True, exist_ok=False)
    usage = Counter()
    for entry in entries:
        usage.update({k: v for k, v in entry['usage'].items() if isinstance(v, (int, float))})
    log = dict(iteration=iteration, run_id=run_id, proposal='Fixed-prompt clause query expansion with original query retained',
               proposer='Codex; hosted/local comparison declared before scoring', model_config=model_config,
               reference_config=base_config, objective=objective, decision=decision, replay_decision=replay_decision,
               selected_system=model_config['name'] if decision['accepted'] else base_config['name'],
               metrics={label: compact(value) for label, value in [('baseline', baseline), ('reference', reference), ('candidate', candidate)]},
               estimated_first_use_latency_ms=first_use_ms,
               unique_cached_requests=len(entries), cache_status_counts=dict(Counter(e['status'] for e in entries)),
               generation_total_ms=sum(e['model_call_ms'] for e in entries), aggregate_unique_request_usage=dict(usage),
               model_versions=sorted({e['response_metadata'].get('model_version', model_config['model']) for e in entries}),
               billing_cost=None, billing_note=('Local execution: no hosted inference fee; machine/electricity costs are not estimated.' if model_config['provider']=='ollama' else 'Token usage recorded; actual charge is not inferred without account billing data.'),
               local_runtime_context=({'system_ram_bytes':16873545728,'model_quantization':'Q4_0','device':'Ollama runtime allocation; see saved runtime snapshot'} if model_config['provider']=='ollama' else None),
               diagnosis_before=diagnose(train, reference['answerable']['predictions']),
               diagnosis_after=diagnose(train, candidate['answerable']['predictions']),
               n_answerable_train=len(train), n_unanswerable_train=len(negatives), test_evaluation_runs=0,
               frozen_question_sha256=frozen['query_set_sha256'], dataset_revision=manifest['revision'],
               cache_sha256={e['cache_key']: hashlib.sha256((root/'cache/llm_rewrites'/f"{e['cache_key']}.json").read_bytes()).hexdigest() for e in entries},
               code_sha256={p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ['llm_rewrite.py','evaluate_llm.py','retrieval.py']},
               result_directory=output.relative_to(root).as_posix())
    for name, value in [('baseline', baseline), ('reference', reference), ('candidate', candidate), ('iteration', log), ('rewrite_events', wrapper.events)]:
        (output / f'{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    with (root / 'experiments/llm_log.jsonl').open('a',encoding='utf-8') as handle:
        handle.write(json.dumps(log,ensure_ascii=False)+'\n')
    return log


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate LLM query rewriting using cached train outputs only.')
    parser.add_argument('--config', choices=['gemini','local_phi3'], default='gemini')
    args = parser.parse_args()
    log = run_evaluation(Path(__file__).resolve().parent, args.config)
    print('Iteration:', log['iteration'])
    print('Operational decision:', log['decision'])
    print('Cache-replay decision:', log['replay_decision'])
    print('Saved:', log['result_directory'])
