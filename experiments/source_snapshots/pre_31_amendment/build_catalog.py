from project_paths import ROOT,source_path
from collections import defaultdict
import json
from pathlib import Path

import nbformat as nb


NOTEBOOKS={0:2,1:4,2:5,3:6,4:7,5:8,6:8,7:8,8:9,9:10,10:11,11:12,12:13,13:14,15:15,16:15,17:16,18:17,19:17,20:18,21:19,22:20,23:21}


def notebook_for(iteration):
    number=NOTEBOOKS[iteration]
    return next((ROOT/'notebooks/experiments').glob(f'{number:02d}_*.ipynb')).relative_to(ROOT).as_posix()


def setup_cell():
    return "from pathlib import Path\nimport json,sys\nimport pandas as pd\nROOT=next(p for p in [Path.cwd().resolve(),*Path.cwd().resolve().parents] if (p/'src/retrieval.py').exists())\nsys.path.insert(0,str(ROOT/'src'))\nsys.path.insert(0,str(ROOT/'scripts'))\n"


def make_book(cells,path):
    book=nb.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','language':'python','display_name':'Python 3'}})
    nb.write(book,path)


def main():
    rows=[]
    for path in (ROOT/'experiments').glob('*log.jsonl'):
        rows += [dict(json.loads(line),source_log=path.relative_to(ROOT).as_posix()) for line in path.read_text().splitlines() if line.strip()]
    grouped=defaultdict(list)
    for row in rows:grouped[row['iteration']].append(row)
    summary=json.loads((ROOT/'evaluation/ALL_MODELS_SUMMARY.json').read_text())
    all_models=summary['models']
    selected=json.loads((ROOT/'evaluation/final_comparison_selection.json').read_text())['models']
    index=['# Experiment directory','','Each iteration folder contains its record, configuration snapshot, metrics, file index and a runnable review notebook. Full raw results and shared source remain central to avoid inconsistent copies.','', '| Iteration | Approach | Review |','|---|---|---|']
    for iteration in [0,*sorted(grouped)]:
        record=grouped[10][-1] if iteration==0 else grouped[iteration][-1]
        model_rows=[m for m in all_models if m['iteration']==iteration]
        label='Original BM25 baseline' if iteration==0 else (model_rows[0]['label'] if model_rows else 'Recorded experiment')
        folder=ROOT/'experiments/iterations'/f'{iteration:02d}'
        folder.mkdir(parents=True,exist_ok=True)
        config=record.get('config',record.get('model_config',record.get('candidate_config',record.get('candidate',{}))))
        if iteration==0:config=json.loads((ROOT/'configs/bm25_baseline.json').read_text())
        if iteration==16:config=grouped[15][-1]['config']
        if iteration==18:config=json.loads((ROOT/'configs/dense_minilm_abstention.json').read_text())
        files=dict(notebook=notebook_for(iteration),source_log=record['source_log'],
                   result_directories=list(dict.fromkeys(r['result_directory'] for r in grouped.get(iteration,[record]) if r.get('result_directory'))),
                   shared_source={name:source_path(ROOT,name).relative_to(ROOT).as_posix() for name in record.get('code_sha256',{}) if name.endswith('.py')},
                   prompt=config.get('prompt_file'),note='Keys and personal guides are excluded; cached requests and raw results are shared centrally.')
        for name,value in [('record',record),('config',config),('metrics',model_rows),('files',files)]:
            (folder/f'{name}.json').write_text(json.dumps(value,indent=2),encoding='utf-8')
        lines=[f'# Iteration {iteration:02d}: {label}','',f"Source record: `{record['source_log']}`; run `{record['run_id']}`.",'',
               f"Full walkthrough: [{Path(files['notebook']).name}](../../../{files['notebook']}).",'',
               'Run review.ipynb for the saved metrics; it makes no model calls. config.json is the recorded settings snapshot, record.json retains the objective/decision, and files.json locates all raw runs and shared code.','',
               'Historical reruns remain in the source logs; the latest complete record is the summary, not a new model idea. No test evaluation is performed here.']
        (folder/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        make_book([nb.v4.new_markdown_cell(f'# Iteration {iteration:02d}: {label}\n\nSaved experiment review. Open the linked full walkthrough for implementation details.'),
                   nb.v4.new_code_cell(setup_cell()+f"folder=ROOT/'experiments/iterations/{iteration:02d}'\nrecord=json.loads((folder/'record.json').read_text())\nrecord.get('proposal')"),
                   nb.v4.new_code_cell("json.loads((folder/'config.json').read_text())"),
                   nb.v4.new_code_cell("models=json.loads((folder/'metrics.json').read_text())\nrows=[]\nfor model in models:\n    m=model['metrics']; v=next(v for v in m['retrieval'] if v['k']==5)\n    rows.append(dict(version=model['label'],precision=v['precision'],recall=v['recall'],correct_abstention=m['correct_abstention'],false_abstention=m['false_abstention']))\npd.DataFrame(rows)"),
                   nb.v4.new_code_cell("json.loads((folder/'files.json').read_text())")],folder/'review.ipynb')
        index.append(f'| {iteration:02d} | {label} | [{iteration:02d}](iterations/{iteration:02d}/README.md) |')
    index += ['', 'Reserved iteration 14 was not run: [Kanon preparation](unrun/kanon/README.md).',
              '', 'Historical pre-cleanup source is under source_snapshots/pre_cleanup_20261101/ for provenance. It is not the active runtime.']
    (ROOT/'experiments/README.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
    folder=ROOT/'notebooks/presentation'
    folder.mkdir(exist_ok=True)
    lines=['# Ten presentation versions','','These ten notebooks form the train-history presentation. Only Run 1, Run 2 and baseline are selected for held-out evaluation. Each notebook reads recorded results and a cached example; no provider generation is permitted.','', '| # | Version | Notebook | Full walkthrough |','|---|---|---|---|']
    for model in selected:
        number=model['order'];path=folder/f'{number:02d}_comparison.ipynb'
        make_book([nb.v4.new_markdown_cell(f"# {number}. {model['label']}\n\n{model['selection_reason']}\n\nThis is a recorded full-train comparison, not a new evaluation."),
                   nb.v4.new_code_cell(setup_cell()+f"from presentation_review import selection,cached_demo\nmodel=selection({number})\nmodel['config_snapshot']"),
                   nb.v4.new_code_cell("m=model['train_metrics']\ntable=pd.DataFrame(m['retrieval'])[['k','n_queries','precision','recall','hit']]\ntable"),
                   nb.v4.new_code_cell("print('Correct negative abstention:',m['negative_counts'])\nprint('False answerable abstention:',m['false_abstention'])\nprint('Cached latency:',m['latency_ms'])"),
                   nb.v4.new_markdown_cell('## Cached example\n\nThe question comes from recorded train predictions. Config settings and original source offsets remain visible; the model cannot call a hosted provider here.'),
                   nb.v4.new_code_cell("demo=cached_demo(model)\nprint(demo['query'])\nprint(demo.get('summary') or demo['message'])\npd.DataFrame(demo['hits'])[['file_path','start','end','text']]"),
                   nb.v4.new_markdown_cell(f"Full code walkthrough: ../../experiments/{Path(model['notebook']).name}. Historical acceptance and current preference are separate; see REPORT.md for limitations.")],path)
        lines.append(f"| {number} | {model['label']} | [{path.name}]({path.name}) | [Full notebook](../experiments/{Path(model['notebook']).name}) |")
    (folder/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('Built 23 iteration review folders and ten presentation notebooks without evaluating or calling models.')


if __name__=='__main__':main()
