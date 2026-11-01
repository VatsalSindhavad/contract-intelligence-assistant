from project_paths import ROOT
import argparse
from datetime import datetime,timezone
import json

from evaluate_clause import measure
from improve import compact,verify_freeze
from negative_validation import validate_negatives
from retrieval import load_inputs
from search_service import build_model


def main():
    parser=argparse.ArgumentParser(description='Evaluate any runnable configuration on train without editing the historical campaign.')
    parser.add_argument('--config',required=True)
    args=parser.parse_args()
    verify_freeze(ROOT)
    train,documents,_=load_inputs(ROOT)
    negatives,_=validate_negatives(ROOT,documents)
    negatives=[r for r in negatives if r['split']=='train']
    model=build_model(args.config,ROOT)
    result=measure(model,train,negatives)
    output=ROOT/'results/manual_train'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True,exist_ok=False)
    (output/'result.json').write_text(json.dumps(dict(config=model.config,summary=compact(result),predictions=result,test_evaluation_runs=0),indent=2),encoding='utf-8')
    print(json.dumps(compact(result),indent=2))
    print('Saved:',output,'; historical campaign unchanged.')


if __name__=='__main__':main()
