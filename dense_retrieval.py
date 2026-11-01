import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter
import uuid
import atexit

import faiss
import numpy as np

from retrieval import make_chunks


def normalized(vectors):
    vectors = np.ascontiguousarray(vectors, dtype=np.float32)
    if vectors.ndim != 2 or not np.all(np.isfinite(vectors)):
        raise ValueError('Expected a finite embedding matrix.')
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if np.any(norms <= 0):
        raise ValueError('Zero-length embeddings are not searchable.')
    return np.ascontiguousarray(vectors / norms, dtype=np.float32)


class LocalEncoder:
    def __init__(self, config):
        self.worker = None
        if 'ipykernel' in sys.modules or 'streamlit' in sys.modules:
            self.worker = EncoderWorker(config)
            return
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'
        from huggingface_hub import snapshot_download
        from sentence_transformers import SentenceTransformer
        import torch
        torch.set_num_threads(config['torch_threads'])
        snapshot = snapshot_download(config['model_id'], revision=config['revision'], local_files_only=True)
        self.model = SentenceTransformer(snapshot, device=config['device'], local_files_only=True)
        self.model.max_seq_length = config['max_seq_length']
        self.config = config

    def encode(self, texts):
        if self.worker:
            return np.asarray(self.worker.request('encode',texts),dtype=np.float32)
        return self.model.encode(texts, batch_size=self.config['batch_size'],
                                 normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)

    def token_lengths(self, texts):
        if self.worker:
            return self.worker.request('lengths',texts)
        return [len(ids) for ids in self.model.tokenizer(texts, truncation=False, padding=False, verbose=False)['input_ids']]


class EncoderWorker:
    def __init__(self,config):
        folder=Path(__file__).resolve().parent/'cache/worker_logs'
        folder.mkdir(parents=True,exist_ok=True)
        self.log=(folder/f'{uuid.uuid4().hex}.log').open('w',encoding='utf-8')
        self.process=subprocess.Popen([sys.executable,str(Path(__file__).with_name('embedding_worker.py')),json.dumps(config)],
                                      stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,encoding='utf-8')
        atexit.register(self.close)
        reply=self.process.stdout.readline()
        if not reply or not json.loads(reply).get('ready'):
            self.close()
            raise RuntimeError('Local embedding worker could not start; inspect cache/worker_logs/.')

    def request(self,operation,texts):
        self.process.stdin.write(json.dumps(dict(operation=operation,texts=texts),ensure_ascii=False)+'\n')
        self.process.stdin.flush()
        line=self.process.stdout.readline()
        if not line:
            raise RuntimeError('Local embedding worker stopped unexpectedly.')
        reply=json.loads(line)
        if 'error' in reply:
            raise RuntimeError(reply['error'])
        return reply['result']

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=10)
        self.log.close()


class DenseRetriever:
    def __init__(self, documents, config, root, encoder=None):
        self.config = dict(config)
        self.root = Path(root)
        self.encoder = encoder
        self.events = []
        self.chunks = make_chunks(documents, config['chunk_size'], config['chunk_overlap'])
        if not self.chunks:
            raise ValueError('The corpus is empty.')
        self.identity = dict(config={k:v for k,v in config.items() if k != 'name'},
                             libraries={p:importlib.metadata.version(p) for p in ['sentence-transformers','transformers','torch','faiss-cpu']},
                             embedding_protocol=1)
        text_hash = hashlib.sha256(json.dumps(self.chunks,ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()
        signature = json.dumps(dict(identity=self.identity,corpus_hash=text_hash),sort_keys=True)
        key = hashlib.sha256(signature.encode('utf-8')).hexdigest()
        self.cache_dir = self.root/'cache'/'dense'/key
        self.cache_dir.mkdir(parents=True,exist_ok=True)
        vectors_path, metadata_path = self.cache_dir/'documents.npy', self.cache_dir/'documents.json'
        if vectors_path.exists() and metadata_path.exists():
            self.metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            if self.metadata['signature'] != signature or hashlib.sha256(vectors_path.read_bytes()).hexdigest() != self.metadata['vectors_sha256']:
                raise ValueError('Document-vector cache identity/checksum mismatch.')
            vectors = np.load(vectors_path,allow_pickle=False)
        else:
            texts = [c['text'] for c in self.chunks]
            encoder = self.get_encoder()
            lengths = encoder.token_lengths(texts)
            started = perf_counter()
            vectors = normalized(encoder.encode(texts))
            encode_ms = (perf_counter()-started)*1000
            np.save(vectors_path,vectors,allow_pickle=False)
            self.metadata = dict(signature=signature,vectors_sha256=hashlib.sha256(vectors_path.read_bytes()).hexdigest(),
                                 chunk_count=len(texts),encode_ms=encode_ms,
                                 inputs_over_token_limit=sum(n>config['max_seq_length'] for n in lengths),
                                 max_input_tokens=max(lengths),max_seq_length=config['max_seq_length'])
            metadata_path.write_text(json.dumps(self.metadata,indent=2),encoding='utf-8')
        if vectors.shape != (len(self.chunks),config['dimension']):
            raise ValueError('Unexpected document-vector dimensions.')
        vectors = normalized(vectors)
        faiss.omp_set_num_threads(config['torch_threads'])
        self.index = faiss.IndexFlatIP(config['dimension'])
        self.index.add(vectors)

    def get_encoder(self):
        if self.encoder is None:
            self.encoder = LocalEncoder(self.config)
        return self.encoder

    def query_vector(self, query):
        signature = json.dumps(dict(identity=self.identity,query=query),ensure_ascii=False,sort_keys=True)
        key = hashlib.sha256(signature.encode('utf-8')).hexdigest()
        folder = self.cache_dir/'queries'
        folder.mkdir(exist_ok=True)
        path, metadata_path = folder/f'{key}.npy', folder/f'{key}.json'
        if path.exists() and metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            if metadata['signature'] != signature or hashlib.sha256(path.read_bytes()).hexdigest() != metadata['vectors_sha256']:
                raise ValueError('Query-vector cache identity/checksum mismatch.')
            vector = np.load(path,allow_pickle=False)
            cached = True
        else:
            encoder = self.get_encoder()
            length = encoder.token_lengths([query])[0]
            started = perf_counter()
            vector = normalized(encoder.encode([query]))
            encode_ms = (perf_counter()-started)*1000
            np.save(path,vector,allow_pickle=False)
            metadata = dict(signature=signature,encode_ms=encode_ms,input_tokens=length,
                            vectors_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            metadata_path.write_text(json.dumps(metadata,indent=2),encoding='utf-8')
            cached = False
        if vector.shape != (1,self.config['dimension']):
            raise ValueError('Unexpected query-vector dimensions.')
        return normalized(vector), metadata, cached

    def search(self, query, k=5):
        if k < 1:
            raise ValueError('k must be positive.')
        if not query.strip():
            return []
        vector, metadata, cached = self.query_vector(query)
        started = perf_counter()
        scores, ids = self.index.search(vector,min(k,len(self.chunks)))
        hits = [dict(self.chunks[int(i)],score=float(score)) for score,i in zip(scores[0],ids[0])
                if i>=0 and score>self.config['min_score']]
        hits.sort(key=lambda h:(-h['score'],h['file_path'],h['start']))
        retrieval_ms = (perf_counter()-started)*1000
        self.events.append(dict(query=query,query_cached=cached,first_encode_ms=metadata['encode_ms'],
                                input_tokens=metadata['input_tokens'],retrieval_ms=retrieval_ms,
                                estimated_first_use_ms=metadata['encode_ms']+retrieval_ms))
        return hits
