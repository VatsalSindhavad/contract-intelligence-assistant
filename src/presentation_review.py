import json
from pathlib import Path

from project_paths import ROOT
from search_service import build_model,search


def selection(number):
    return json.loads((ROOT/'evaluation/final_comparison_selection.json').read_text(encoding='utf-8'))['models'][number-1]


def source_record(row):
    records=[]
    for path in (ROOT/'experiments').glob('*log.jsonl'):
        records += [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    return next(r for r in reversed(records) if r['iteration']==row['train_source_iteration'] and r['run_id']==row['train_source_run_id'])


def example_prediction(row):
    record=source_record(row)
    folder=ROOT/record['result_directory']
    iteration=row['train_source_iteration']
    if row['order']==1:
        result=json.loads((folder/'baseline.json').read_text(encoding='utf-8'))
    elif iteration==18:
        result=json.loads((folder/'control_predictions.json').read_text(encoding='utf-8'))['0.55']
    elif iteration==19:
        result=json.loads((folder/'threshold_predictions.json').read_text(encoding='utf-8'))['0.55']
    else:
        result=json.loads((folder/'candidate.json').read_text(encoding='utf-8'))
    return next(r for r in result['answerable']['predictions'] if r['hits'])


def cached_demo(row):
    config=json.loads((ROOT/row['config_path']).read_text(encoding='utf-8'))
    prediction=example_prediction(row)
    return search(build_model(config['name'],ROOT),prediction['query'])
