from project_paths import ROOT
import argparse
import json

from dense_retrieval import DenseRetriever
from retrieval import load_corpus
from search_service import EXAMPLE_QUERY


def main():
    parser=argparse.ArgumentParser(description='Prepare pinned local MiniLM weights and dense vectors; no Gemini calls or test evaluation.')
    parser.add_argument('--download',action='store_true')
    args=parser.parse_args()
    config=json.loads((ROOT/'semantic_configs/minilm.json').read_text(encoding='utf-8'))
    if args.download:
        from huggingface_hub import snapshot_download
        folder=ROOT/'cache/model_weights/all-MiniLM-L6-v2'/config['revision']
        snapshot_download(config['model_id'],revision=config['revision'],local_dir=str(folder),max_workers=1,
                          allow_patterns=['*.json','*.txt','model.safetensors','1_Pooling/*'])
    documents,_=load_corpus(ROOT)
    model=DenseRetriever(documents,config,ROOT)
    model.search(EXAMPLE_QUERY)
    print('Pinned MiniLM and example vectors ready. No provider calls or test metrics.')


if __name__=='__main__':main()
