from project_paths import ROOT as PROJECT_ROOT, source_path
import json
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from time import perf_counter

from clause_chunking import AbstentionRetriever
from dense_retrieval import DenseRetriever
from improve import compact, read_json, verify_freeze
from negative_validation import evaluate_negative_train, validate_negatives
from retrieval import evaluate_train, load_inputs


THRESHOLDS = [.2,.3,.4,.5,.6,.7,.8]


def measure(model, train, negatives):
    return dict(answerable=evaluate_train(model,train,[1,3,5,10]),
                negative=evaluate_negative_train(model,negatives))


def at5(metrics):
    return next(row for row in metrics['retrieval'] if row['k']==5)


def run(root):
    root = Path(root)
    verify_freeze(root)
    train, documents, manifest = load_inputs(root)
    negatives, frozen = validate_negatives(root,documents)
    negatives = [row for row in negatives if row['split']=='train']
    config = read_json(root/'semantic_configs/minilm_clause.json')
    started = perf_counter()
    model = DenseRetriever(documents,config,root)
    build_seconds = perf_counter()-started
    candidate = measure(model,train,negatives)
    metrics = compact(candidate)
    history = [json.loads(line) for line in (root/'experiments/semantic_log.jsonl').read_text(encoding='utf-8').splitlines()]
    minilm = next(row for row in reversed(history) if row['iteration']==11)
    reference = minilm['metrics']['candidate']
    before, after = at5(reference), at5(metrics)
    checks = dict(precision_gain=after['precision']>=before['precision']+.01,
                  recall=after['recall']>=before['recall']-.02,
                  false_abstention=metrics['false_abstention']<=.02,
                  correct_abstention=metrics['correct_abstention']>=reference['correct_abstention'])
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = root/'results/iteration_15_clause'/run_id
    output.mkdir(parents=True,exist_ok=False)
    common = dict(run_id=run_id, n_answerable_train=len(train),n_unanswerable_train=len(negatives),
                  test_evaluation_runs=0,dataset_revision=manifest['revision'],
                  frozen_question_sha256=frozen['query_set_sha256'],
                  proposer='User; deterministic clause chunking followed by abstention threshold search',
                  code_sha256={name:hashlib.sha256(source_path(root,name).read_bytes()).hexdigest()
                               for name in ['clause_chunking.py','dense_retrieval.py','evaluate_clause.py']},
                  result_directory=output.relative_to(root).as_posix())
    log = dict(common,iteration=15,proposal='Clause-aware MiniLM + FAISS',config=config,
               metrics=dict(reference=reference,candidate=metrics),checks=checks,accepted=all(checks.values()),
               build_seconds=build_seconds,chunk_count=len(model.chunks),embedding_metadata=model.metadata,
               vector_cache_directory=model.cache_dir.relative_to(root).as_posix())
    trials = []
    trial_results = {}
    for threshold in THRESHOLDS:
        result = measure(AbstentionRetriever(model,threshold),train,negatives)
        trial = compact(result)
        m = at5(trial)
        guardrails = dict(precision=m['precision']>=after['precision'],recall=m['recall']>=after['recall']-.02,
                          false_abstention=trial['false_abstention']<=.02,
                          correct_abstention=trial['correct_abstention']>metrics['correct_abstention'])
        trials.append(dict(threshold=threshold,metrics=trial,checks=guardrails,accepted=all(guardrails.values())))
        trial_results[str(threshold)] = result
    eligible = [trial for trial in trials if trial['accepted']]
    selected = max(eligible,key=lambda t:(t['metrics']['correct_abstention'],at5(t['metrics'])['precision'],
                                          at5(t['metrics'])['recall'],-t['threshold'])) if eligible else None
    gate_log = dict(common,iteration=16,proposal='Top-score abstention threshold on clause-aware dense retrieval',
                    reference=metrics,trials=trials,selected_threshold=selected['threshold'] if selected else None,
                    accepted=selected is not None,limitation='Thresholds selected and measured on train; not held-out estimates.')
    for name,value in [('candidate',candidate),('iteration',log),('abstention',gate_log),('threshold_predictions',trial_results)]:
        (output/f'{name}.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
    with (root/'experiments/semantic_log.jsonl').open('a',encoding='utf-8') as handle:
        for entry in [log,gate_log]:
            handle.write(json.dumps(entry)+'\n')
    print(json.dumps(dict(clause=metrics,clause_checks=checks,chunk_count=len(model.chunks),
                          selected_threshold=gate_log['selected_threshold'],
                          trials=[dict(threshold=t['threshold'],precision=at5(t['metrics'])['precision'],
                                       recall=at5(t['metrics'])['recall'],false_abstention=t['metrics']['false_abstention'],
                                       correct_abstention=t['metrics']['correct_abstention'],accepted=t['accepted']) for t in trials]),indent=2))
    return log,gate_log


if __name__=='__main__':
    run(PROJECT_ROOT)
