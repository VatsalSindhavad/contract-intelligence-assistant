import hashlib
import importlib.metadata
import json
import platform
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from negative_validation import evaluate_negative_train, validate_negatives
from retrieval import BM25Retriever, character_metrics, evaluate_train, load_inputs


def diagnose(records, predictions, k=5):
    gold = {r['query_id']: r['snippets'] for r in records}
    counts = Counter()
    for prediction in predictions:
        hits = prediction['hits'][:k]
        snippets = gold[prediction['query_id']]
        recall = character_metrics(hits, snippets)['recall']
        if not hits:
            category = 'incorrect_abstention'
        elif not any(h['file_path'] in {s['file_path'] for s in snippets} for h in hits):
            category = 'wrong_document'
        elif recall == 0:
            category = 'right_document_wrong_section'
        elif recall < 1:
            category = 'partial_coverage'
        else:
            category = 'complete_coverage'
        counts[category] += 1
    return dict(counts)


def decide(reference, candidate, objective):
    def at5(result):
        return next(m for m in result['answerable']['metrics'] if m['k'] == 5)
    before, after = at5(reference), at5(candidate)
    checks = {
        'recall_gain': after['recall'] >= before['recall'] + objective['minimum_recall_gain_absolute'],
        'precision': after['precision'] >= before['precision'] * objective['minimum_precision_ratio'],
        'answerable_abstention': candidate['answerable']['answerable_false_abstention_rate'] <= reference['answerable']['answerable_false_abstention_rate'] + objective['maximum_false_abstention_increase_absolute'],
        'unanswerable_abstention': candidate['negative']['correct_abstention_rate'] >= reference['negative']['correct_abstention_rate'] - objective['maximum_correct_abstention_drop_absolute'],
        'latency': candidate['answerable']['latency_ms']['p95'] <= max(objective['latency_p95_floor_ms'], reference['answerable']['latency_ms']['p95'] * objective['latency_p95_multiplier']),
    }
    return dict(accepted=all(checks.values()), checks=checks)


def evaluate_config(config, documents, train, negatives):
    started = perf_counter()
    retriever = BM25Retriever(documents, config)
    build_seconds = perf_counter() - started
    return dict(config=config, build_seconds=build_seconds,
                answerable=evaluate_train(retriever, train, config['k_values']),
                negative=evaluate_negative_train(retriever, negatives),
                chunk_count=len(retriever.chunks))


def run_iteration(root):
    root = Path(root)
    train, documents, manifest = load_inputs(root)
    negatives, frozen = validate_negatives(root, documents)
    negatives = [r for r in negatives if r['split'] == 'train']
    objective = json.loads((root / 'experiments/objective.json').read_text(encoding='utf-8'))
    configs = [json.loads((root / 'configs' / f'{name}.json').read_text(encoding='utf-8'))
               for name in ['bm25_baseline', 'bm25_stopwords']]
    reference = evaluate_config(configs[0], documents, train, negatives)
    diagnosis = diagnose(train, reference['answerable']['predictions'])
    candidate = evaluate_config(configs[1], documents, train, negatives)
    decision = decide(reference, candidate, objective)
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = root / 'results' / 'iteration_01' / run_id
    output.mkdir(parents=True, exist_ok=False)
    log = dict(iteration=1, run_id=run_id, proposer='Codex, based on train failure diagnosis',
               proposal='Remove fixed common function words from query and document tokens.',
               reason='Reduce common-word noise when ranking passages within the correct document.',
               changed={'remove_stopwords': {'before': False, 'after': True}},
               objective=objective, diagnosis_before=diagnosis,
               diagnosis_after=diagnose(train, candidate['answerable']['predictions']),
               decision=decision, reference=configs[0], candidate=configs[1],
               selected_config=configs[1] if decision['accepted'] else configs[0],
               n_answerable_train=len(train), n_unanswerable_train=len(negatives),
               test_evaluation_runs=0, dataset_revision=manifest['revision'],
               frozen_question_sha256=frozen['query_set_sha256'], python=platform.python_version(),
               packages={p: importlib.metadata.version(p) for p in ['rank-bm25', 'numpy', 'pandas']},
               metric_convention='unique-character objective; benchmark pairwise scores also reported',
               metrics={label: dict(retrieval=result['answerable']['metrics'],
                                    false_abstention=result['answerable']['answerable_false_abstention_rate'],
                                    correct_abstention=result['negative']['correct_abstention_rate'],
                                    latency_ms=result['answerable']['latency_ms'])
                        for label, result in [('reference', reference), ('candidate', candidate)]},
               code_sha256={name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                            for name in ['retrieval.py', 'negative_validation.py', 'run_experiment.py']})
    for name, result in [('reference', reference), ('candidate', candidate), ('iteration', log)]:
        (output / f'{name}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    with (root / 'experiments/log.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(dict(log, result_directory=str(output.relative_to(root)))) + '\n')
    return output, reference, candidate, log


if __name__ == '__main__':
    output, _, _, log = run_iteration(Path(__file__).resolve().parent)
    print('Accepted:', log['decision']['accepted'])
    print('Checks:', log['decision']['checks'])
    print('Saved:', output)
