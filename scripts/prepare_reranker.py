from project_paths import ROOT as PROJECT_ROOT, source_path
import argparse
import hashlib
import json
from pathlib import Path


def prepare(root, download=False):
    root = Path(root)
    config = json.loads((root/'semantic_configs/hybrid_reranked.json').read_text(encoding='utf-8'))
    folder = root/'cache'/'model_weights'/'ms-marco-MiniLM-L6-v2'/config['revision']
    if download:
        from huggingface_hub import snapshot_download
        snapshot_download(config['model_id'],revision=config['revision'],local_dir=str(folder),max_workers=1,
                          allow_patterns=['config.json','model.safetensors','tokenizer.json','tokenizer_config.json',
                                          'special_tokens_map.json','vocab.txt','README.md'])
        identity = dict(model_id=config['model_id'],revision=config['revision'],
                        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in folder.iterdir() if p.is_file() and p.name!='model_identity.json'})
        (folder/'model_identity.json').write_text(json.dumps(identity,indent=2))
    identity = json.loads((folder/'model_identity.json').read_text(encoding='utf-8'))
    if identity['model_id']!=config['model_id'] or identity['revision']!=config['revision']:
        raise ValueError('Unexpected reranker model identity.')
    for name,digest in identity.get('files',{}).items():
        if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Reranker model file checksum mismatch.')
    print('Pinned local reranker is available:',folder)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--download',action='store_true',help='Download public weights; no user data is sent.')
    args=parser.parse_args()
    prepare(PROJECT_ROOT,args.download)
