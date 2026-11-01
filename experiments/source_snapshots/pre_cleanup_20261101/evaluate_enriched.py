import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from clause_chunking import AbstentionRetriever
from evaluate_clause import at5, measure
from improve import compact, read_json, verify_freeze
from negative_validation import validate_negatives
from reference_enrichment import EnrichedRetriever
from retrieval import load_inputs
from run_experiment import diagnose


def run(root):
    root = Path(root)
    verify_freeze(root)
    train,documents,manifest = load_inputs(root)
    negatives,frozen = validate_negatives(root,documents)
    negatives = [r for r in negatives if r['split']=='train']
    config = read_json(root/'semantic_configs/minilm_enriched.json')
    policy = read_json(root/'experiments/abstention_policy_v2.json')
    started = perf_counter()
    model = EnrichedRetriever(documents,config,root)
    build_seconds = perf_counter()-started
    candidate = measure(model,train,negatives)
    metrics = compact(candidate)
    rows = [json.loads(line) for line in (root/'experiments/semantic_log.jsonl').read_text().splitlines()]
    reference = next(r for r in reversed(rows) if r['iteration']==11)['metrics']['candidate']
    before,after = at5(reference),at5(metrics)
    checks = dict(gain=after['precision']>=before['precision']+.005 or after['recall']>=before['recall']+.01,
                  precision=after['precision']>=before['precision']-.02,
                  recall=after['recall']>=before['recall']-.02,
                  false_abstention=metrics['false_abstention']<=policy['maximum_false_answerable_abstention_rate'],
                  correct_abstention=metrics['correct_abstention']>=reference['correct_abstention'])
    trials = []
    predictions = {}
    for threshold in [.4,.45,.5,.55,.6,.65]:
        result = measure(AbstentionRetriever(model,threshold),train,negatives)
        m = compact(result)
        p = at5(m)
        guardrails = dict(precision=p['precision']>=.95*after['precision'],
                          recall=p['recall']>=after['recall']-.02,
                          false_abstention=m['false_abstention']<=policy['maximum_false_answerable_abstention_rate'],
                          correct_abstention=m['correct_abstention']>metrics['correct_abstention'])
        trials.append(dict(threshold=threshold,metrics=m,checks=guardrails,accepted=all(guardrails.values())))
        predictions[str(threshold)] = result
    eligible = [t for t in trials if t['accepted']]
    selected = max(eligible,key=lambda t:(t['metrics']['correct_abstention'],at5(t['metrics'])['recall'],
                                          at5(t['metrics'])['precision'],-t['threshold'])) if eligible else None
    for prediction in candidate['answerable']['predictions']+candidate['negative']['predictions']:
        for hit in prediction['hits']:
            assert hit['text']==documents[hit['file_path']][hit['start']:hit['end']]
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = root/'results/iteration_17_enriched'/run_id
    output.mkdir(parents=True,exist_ok=False)
    log = dict(iteration=17,run_id=run_id,proposal='Same-contract definition and numbered-section context vectors',
               proposer='User; corpus-only indexing enrichment declared before evaluation',config=config,
               metrics=dict(reference=reference,candidate=metrics),accepted=all(checks.values()),checks=checks,
               abstention_policy=policy,threshold_trials=trials,
               selected_threshold=selected['threshold'] if selected else None,
               threshold_accepted=selected is not None,build_seconds=build_seconds,
               embedding_metadata=model.metadata,vector_cache_directory=model.cache_dir.relative_to(root).as_posix(),
               resolved_context_spans=sum(len(e['sources']) for e in model.enrichment),
               unresolved_or_ambiguous_references=sum(len(e['unresolved_sections']) for e in model.enrichment),
               diagnosis_after=diagnose(train,candidate['answerable']['predictions']),
               n_answerable_train=len(train),n_unanswerable_train=len(negatives),test_evaluation_runs=0,
               dataset_revision=manifest['revision'],frozen_question_sha256=frozen['query_set_sha256'],
               code_sha256={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in
                            ['reference_enrichment.py','evaluate_enriched.py','dense_retrieval.py','clause_chunking.py']},
               result_directory=output.relative_to(root).as_posix())
    for name,value in [('candidate',candidate),('iteration',log),('threshold_predictions',predictions),
                       ('enrichment',model.enrichment),('events',model.events)]:
        (output/f'{name}.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
    with (root/'experiments/semantic_log.jsonl').open('a',encoding='utf-8') as handle:
        handle.write(json.dumps(log)+'\n')
    print(json.dumps(dict(metrics=metrics,checks=checks,metadata=model.metadata,
                          selected_threshold=log['selected_threshold'],
                          trials=[dict(threshold=t['threshold'],at5=at5(t['metrics']),
                                       false_abstention=t['metrics']['false_abstention'],
                                       correct_abstention=t['metrics']['correct_abstention'],accepted=t['accepted']) for t in trials]),indent=2))
    return log


if __name__=='__main__':
    run(Path(__file__).resolve().parent)
