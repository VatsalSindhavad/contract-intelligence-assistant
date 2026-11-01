from project_paths import ROOT as PROJECT_ROOT, source_path
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
from time import perf_counter

import numpy as np


class LocalReranker:
    def __init__(self, config, root):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        torch.set_num_threads(config['torch_threads'])
        path = Path(root)/'cache'/'model_weights'/'ms-marco-MiniLM-L6-v2'/config['revision']
        identity = json.loads((path/'model_identity.json').read_text(encoding='utf-8'))
        if identity['model_id']!=config['model_id'] or identity['revision']!=config['revision']:
            raise ValueError('Local reranker identity mismatch.')
        self.tokenizer = AutoTokenizer.from_pretrained(path,local_files_only=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(path,local_files_only=True,
                                                                       use_safetensors=True).to(config['device'])
        self.model.eval()
        self.config,self.torch = config,torch

    def score(self, query, hits):
        pairs = [(query,hit['text']) for hit in hits]
        lengths = [len(self.tokenizer(q,t,truncation=False)['input_ids']) for q,t in pairs]
        scores = []
        for start in range(0,len(pairs),self.config['batch_size']):
            batch = pairs[start:start+self.config['batch_size']]
            inputs = self.tokenizer([p[0] for p in batch],[p[1] for p in batch],padding=True,
                                    truncation='longest_first',max_length=self.config['max_length'],return_tensors='pt')
            inputs = {key:value.to(self.config['device']) for key,value in inputs.items()}
            with self.torch.inference_mode():
                scores.extend(self.model(**inputs).logits.flatten().cpu().tolist())
        return dict(scores=scores,pair_tokens=lengths)


class RerankRetriever:
    def __init__(self, base, root, config, allow_inference=False, scorer=None):
        self.base,self.root,self.config = base,Path(root),config
        self.allow_inference,self.scorer = allow_inference,scorer
        self.events = []

    def search(self, query, k=5):
        if not 1<=k<=self.config['candidate_pool']:
            raise ValueError('k must be within the reranker candidate pool.')
        started = perf_counter()
        hits = self.base.search(query,self.config['candidate_pool'])
        if not hits:
            self.events.append(dict(query=query,status='upstream_abstention',cached=True,model_ms=0,
                                    pair_count=0,truncated_pairs=0,replay_ms=(perf_counter()-started)*1000))
            return []
        request = dict(config=self.config,query=query,candidates=hits,
                       libraries={p:importlib.metadata.version(p) for p in ['transformers','torch']})
        signature = json.dumps(request,sort_keys=True,ensure_ascii=False)
        key = hashlib.sha256(signature.encode()).hexdigest()
        path = self.root/'cache'/'rerank_scores'/f'{key}.json'
        cached = path.exists()
        if cached:
            entry = json.loads(path.read_text(encoding='utf-8'))
            if entry['request']!=request or entry['result_sha256']!=self.digest(entry['result']):
                raise ValueError('Reranker cache identity/checksum mismatch.')
        else:
            if not self.allow_inference:
                raise RuntimeError('Reranker cache missing; run python evaluate_reranker.py --fill for local inference.')
            if self.scorer is None:
                self.scorer = LocalReranker(self.config,self.root)
            call_started = perf_counter()
            result = self.scorer.score(query,hits)
            self.validate(result,len(hits))
            entry = dict(request=request,result=result,result_sha256=self.digest(result),
                         model_ms=(perf_counter()-call_started)*1000)
            path.parent.mkdir(parents=True,exist_ok=True)
            temp = path.with_suffix('.tmp')
            temp.write_text(json.dumps(entry,ensure_ascii=False),encoding='utf-8')
            temp.replace(path)
        result = entry['result']
        self.validate(result,len(hits))
        order = sorted(range(len(hits)),key=lambda i:(-result['scores'][i],i))
        selected = [dict(hits[i],hybrid_score=hits[i]['score'],score=result['scores'][i]) for i in order[:k]]
        self.events.append(dict(query=query,status='ranked',cached=cached,cache_key=key,model_ms=entry['model_ms'],
                                pair_count=len(hits),truncated_pairs=sum(n>self.config['max_length'] for n in result['pair_tokens']),
                                replay_ms=(perf_counter()-started)*1000))
        return selected

    @staticmethod
    def digest(result):
        return hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()

    @staticmethod
    def validate(result,count):
        if len(result['scores'])!=count or len(result['pair_tokens'])!=count or not np.isfinite(result['scores']).all():
            raise ValueError('Invalid reranker score count or nonfinite score.')
