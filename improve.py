import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from negative_validation import validate_negatives
from retrieval import load_inputs
from run_experiment import decide, diagnose, evaluate_config


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def read_log(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def config_key(config):
    settings = {k: v for k, v in config.items() if k != 'name'}
    settings.setdefault('remove_stopwords', False)
    return json.dumps(settings, sort_keys=True)


def resume_state(baseline, historical, loop_history):
    current = dict(baseline)
    tried_ids, tried_configs = set(), set()
    for entry in historical:
        tried_configs.add(config_key(entry['candidate']))
        current = entry['selected_config']
    next_iteration = max((entry['iteration'] for entry in historical), default=0) + 1
    for entry in loop_history:
        if entry['iteration'] != next_iteration or config_key(entry['reference_config']) != config_key(current):
            raise ValueError('Loop history is inconsistent; inspect the log before resuming.')
        tried_ids.add(entry['proposal']['id'])
        tried_configs.add(config_key(entry['candidate_config']))
        current = entry['selected_config']
        next_iteration += 1
    return current, tried_ids, tried_configs, next_iteration


def choose_proposal(current, diagnosis, proposals, tried_ids, tried_configs):
    ranked = sorted(enumerate(proposals), key=lambda pair: (-diagnosis.get(pair[1]['trigger'], 0), pair[0]))
    for _, proposal in ranked:
        candidate = dict(current, **proposal['changes'], name=proposal['name'])
        if proposal['id'] in tried_ids or config_key(candidate) in tried_configs or config_key(candidate) == config_key(current):
            continue
        if not 0 <= candidate['chunk_overlap'] < candidate['chunk_size']:
            continue
        return proposal, candidate
    return None, None


def compact(result):
    return dict(retrieval=result['answerable']['metrics'],
                false_abstention=result['answerable']['answerable_false_abstention_rate'],
                correct_abstention=result['negative']['correct_abstention_rate'],
                negative_counts=dict(n=result['negative']['n_queries'], correct=result['negative']['correct_abstentions']),
                latency_ms=result['answerable']['latency_ms'])


def verify_freeze(root):
    for relative in ['evaluation/unanswerable.json', 'evaluation/frozen_manifest.json']:
        committed = subprocess.check_output(['git', '-C', str(root), 'show', f'HEAD:{relative}'])
        if committed != (root / relative).read_bytes():
            raise ValueError(f'Frozen set differs from its committed version: {relative}')


def run_step(root):
    root = Path(root).resolve()
    verify_freeze(root)
    baseline_config = read_json(root / 'configs/bm25_baseline.json')
    historical = read_log(root / 'experiments/log.jsonl')
    history = read_log(root / 'experiments/loop_log.jsonl')
    current, tried_ids, tried_configs, iteration = resume_state(baseline_config, historical, history)
    objective = read_json(root / 'experiments/objective.json')
    if history and objective != history[-1]['objective']:
        raise ValueError('Objective changed during the loop; document a new experiment phase first.')
    train, documents, manifest = load_inputs(root)
    negatives, frozen = validate_negatives(root, documents)
    negatives = [r for r in negatives if r['split'] == 'train']
    reference = evaluate_config(current, documents, train, negatives)
    diagnosis = diagnose(train, reference['answerable']['predictions'])
    diagnosis['false_returns'] = reference['negative']['n_queries'] - reference['negative']['correct_abstentions']
    proposals = read_json(root / 'experiments/proposals.json')
    proposal, candidate_config = choose_proposal(current, diagnosis, proposals, tried_ids, tried_configs)
    if proposal is None:
        return None
    candidate = evaluate_config(candidate_config, documents, train, negatives)
    baseline = reference if config_key(current) == config_key(baseline_config) else evaluate_config(baseline_config, documents, train, negatives)
    decision = decide(reference, candidate, objective)
    selected = candidate_config if decision['accepted'] else current
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = root / 'results' / f'iteration_{iteration:02d}' / run_id
    output.mkdir(parents=True, exist_ok=False)
    log = dict(iteration=iteration, run_id=run_id, proposal=proposal,
               proposer='deterministic diagnostic rule; proposal catalog authored by Codex',
               selection_rule='Largest matching failure count first, catalog order breaks ties; skip tried proposals.',
               diagnosis_before=diagnosis, diagnosis_after=diagnose(train, candidate['answerable']['predictions']),
               changes={k: dict(before=current.get(k), after=v) for k, v in proposal['changes'].items()},
               reference_config=current, candidate_config=candidate_config, selected_config=selected,
               objective=objective, decision=decision,
               metrics={label: compact(value) for label, value in [('baseline', baseline), ('reference', reference), ('candidate', candidate)]},
               n_answerable_train=len(train), n_unanswerable_train=len(negatives), test_evaluation_runs=0,
               dataset_revision=manifest['revision'], frozen_question_sha256=frozen['query_set_sha256'],
               source_commit=subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD']).decode().strip(),
               code_sha256={p: hashlib.sha256((root / p).read_bytes()).hexdigest()
                            for p in ['improve.py', 'run_experiment.py', 'retrieval.py', 'negative_validation.py', 'experiments/proposals.json']},
               result_directory=output.relative_to(root).as_posix())
    for name, value in [('baseline', baseline), ('reference', reference), ('candidate', candidate), ('iteration', log), ('selected_config', selected)]:
        (output / f'{name}.json').write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    with (root / 'experiments/loop_log.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(log, ensure_ascii=False) + '\n')
    return log


def main():
    parser = argparse.ArgumentParser(description='Run train-only, diagnostic-driven retrieval improvements.')
    parser.add_argument('--steps', type=int, default=1, choices=range(1, 6))
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    lock = root / 'experiments/.loop.lock'
    try:
        with lock.open('x', encoding='utf-8') as handle:
            handle.write(datetime.now(timezone.utc).isoformat())
    except FileExistsError:
        parser.error('Another loop run may be active; inspect experiments/.loop.lock.')
    try:
        for _ in range(args.steps):
            log = run_step(root)
            if log is None:
                print('No untried proposals remain. No iteration recorded.')
                break
            print(f"Iteration {log['iteration']}: {log['proposal']['id']}")
            print('Accepted:', log['decision']['accepted'])
            print('Checks:', log['decision']['checks'])
            print('Selected:', log['selected_config']['name'])
            print('Saved:', log['result_directory'])
    finally:
        lock.unlink()


if __name__ == '__main__':
    main()
