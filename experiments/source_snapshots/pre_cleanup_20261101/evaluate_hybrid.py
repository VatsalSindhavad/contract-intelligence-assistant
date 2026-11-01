from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from clause_chunking import AbstentionRetriever
from dense_retrieval import DenseRetriever
from evaluate_clause import at5, measure
from hybrid_retrieval import HybridRetriever
from improve import compact, read_json, verify_freeze
from negative_validation import validate_negatives
from retrieval import BM25Retriever, load_inputs
from run_experiment import diagnose


THRESHOLDS = [.4,.45,.5,.55,.6,.65]


def qualifies(reference, trial, policy):
    before,after = at5(reference),at5(trial)
    return dict(precision=after['precision']>=.95*before['precision'],
                recall=after['recall']>=before['recall']-.02,
                false_abstention=trial['false_abstention']<=policy['maximum_false_answerable_abstention_rate'],
                correct_abstention=trial['correct_abstention']>reference['correct_abstention'])


def select(trials):
    eligible = [t for t in trials if t['accepted']]
    return max(eligible,key=lambda t:(t['metrics']['correct_abstention'],at5(t['metrics'])['recall'],
                                      at5(t['metrics'])['precision'],-t['threshold'])) if eligible else None


def run(root):
    root = Path(root)
    verify_freeze(root)
    train,documents,manifest = load_inputs(root)
    negatives,frozen = validate_negatives(root,documents)
    negatives = [r for r in negatives if r['split']=='train']
    policy = read_json(root/'experiments/abstention_policy_v2.json')
    config = read_json(root/'semantic_configs/hybrid_rrf.json')
    dense = DenseRetriever(documents,read_json(root/config['dense_config']),root)
    lexical = BM25Retriever(documents,read_json(root/config['bm25_config']))
    dense_result = measure(dense,train,negatives)
    reference = measure(lexical,train,negatives)
    dense_metrics,bm25_metrics = compact(dense_result),compact(reference)
    control_trials,control_predictions = [],{}
    for threshold in THRESHOLDS:
        result = measure(AbstentionRetriever(dense,threshold),train,negatives)
        metrics = compact(result)
        checks = qualifies(dense_metrics,metrics,policy)
        control_trials.append(dict(threshold=threshold,metrics=metrics,checks=checks,accepted=all(checks.values())))
        control_predictions[str(threshold)] = result
    control_selected = select(control_trials)
    hybrid = HybridRetriever(lexical,dense,config)
    candidate = measure(hybrid,train,negatives)
    candidate_metrics = compact(candidate)
    before,after = at5(bm25_metrics),at5(candidate_metrics)
    checks = dict(recall_gain=after['recall']>=before['recall']+.01,
                  precision=after['precision']>=before['precision']*.95,
                  false_abstention=candidate_metrics['false_abstention']<=policy['maximum_false_answerable_abstention_rate'],
                  correct_abstention=candidate_metrics['correct_abstention']>=bm25_metrics['correct_abstention'])
    trials,predictions = [],{}
    for threshold in THRESHOLDS:
        model = HybridRetriever(lexical,dense,dict(config,dense_confidence_threshold=threshold))
        result = measure(model,train,negatives)
        metrics = compact(result)
        gate_checks = qualifies(candidate_metrics,metrics,policy)
        trials.append(dict(threshold=threshold,metrics=metrics,checks=gate_checks,accepted=all(gate_checks.values())))
        predictions[str(threshold)] = result
    selected = select(trials)
    for result in [candidate,dense_result]+list(predictions.values()):
        for prediction in result['answerable']['predictions']+result['negative']['predictions']:
            for hit in prediction['hits']:
                assert hit['text']==documents[hit['file_path']][hit['start']:hit['end']]
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = root/'results/iteration_19_hybrid'/run_id
    output.mkdir(parents=True,exist_ok=False)
    common = dict(run_id=run_id,abstention_policy=policy,n_answerable_train=len(train),n_unanswerable_train=len(negatives),
                  test_evaluation_runs=0,dataset_revision=manifest['revision'],frozen_question_sha256=frozen['query_set_sha256'],
                  proposer='User; hybrid stage with same-cutoff dense control',
                  code_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in
                               ['evaluate_hybrid.py','hybrid_retrieval.py','dense_retrieval.py','clause_chunking.py','retrieval.py']},
                  result_directory=output.relative_to(root).as_posix())
    control = dict(common,iteration=18,proposal='Original MiniLM cutoff control',reference=dense_metrics,
                   threshold_trials=control_trials,selected_threshold=control_selected['threshold'] if control_selected else None)
    log = dict(common,iteration=19,proposal='Weighted reciprocal-rank BM25 and MiniLM hybrid',config=config,
               metrics=dict(bm25=bm25_metrics,dense=dense_metrics,candidate=candidate_metrics),
               accepted=all(checks.values()),checks=checks,threshold_trials=trials,
               selected_threshold=selected['threshold'] if selected else None,
               diagnosis_after=diagnose(train,candidate['answerable']['predictions']))
    for name,value in [('candidate',candidate),('bm25',reference),('dense',dense_result),('iteration',log),
                       ('control',control),('control_predictions',control_predictions),('threshold_predictions',predictions)]:
        (output/f'{name}.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
    with (root/'experiments/semantic_log.jsonl').open('a',encoding='utf-8') as handle:
        for entry in [control,log]: handle.write(json.dumps(entry)+'\n')
    print('Dense control threshold:',control['selected_threshold'])
    print('Hybrid checks:',checks)
    print('Hybrid P/R:',after['precision'],after['recall'])
    print('Hybrid threshold:',log['selected_threshold'])
    print('Saved:',log['result_directory'])
    return control,log


if __name__=='__main__':
    run(Path(__file__).resolve().parent)
