import hashlib
import json
from pathlib import Path
import re
from time import perf_counter

import faiss
import numpy as np

from dense_retrieval import DenseRetriever, normalized


def context_catalog(text):
    headings = list(re.finditer(r'(?mi)^\s*(?:Section\s+)?(\d+(?:\.\d+)*)(?:[.)]|\s)\s*(?=[A-Z])',text))
    sections = {}
    for i, match in enumerate(headings):
        end = headings[i+1].start() if i+1<len(headings) else len(text)
        sections.setdefault(match.group(1),[]).append((match.start(),min(end,match.start()+1600)))
    definitions = {}
    pattern = r'["“]([^"”\n]{2,70})["”]\s+(?:shall\s+mean|means|has\s+the\s+meaning)\b[^\n]{0,800}'
    for match in re.finditer(pattern,text,re.I):
        definitions.setdefault(match.group(1),[]).append((match.start(),match.end()))
    return sections, definitions


def enrich_chunk(chunk, text, catalog, max_context_chars=900):
    sections, definitions = catalog
    spans = []
    unresolved = []
    for match in re.finditer(r'\bSections?\s+(\d+(?:\.\d+)*)\b',chunk['text'],re.I):
        key = match.group(1)
        targets = sections.get(key,[])
        if len(targets)==1:
            spans.append((*targets[0],'section',key))
        else:
            unresolved.append(key)
    for term, targets in definitions.items():
        if len(targets)==1 and re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',chunk['text'],re.I):
            spans.append((*targets[0],'definition',term))
    selected = []
    used = set()
    remaining = max_context_chars
    for start,end,kind,key in spans:
        if (start,end) in used or (start<chunk['end'] and end>chunk['start']):
            continue
        used.add((start,end))
        if remaining<=0:
            break
        end = min(end,start+remaining)
        selected.append(dict(start=start,end=end,kind=kind,key=key,text=text[start:end]))
        remaining-=end-start
    return dict(context='\n'.join(row['text'] for row in selected),sources=selected,
                unresolved_sections=unresolved)


class EnrichedRetriever:
    def __init__(self, documents, config, root):
        self.config = config
        self.root = Path(root)
        base_config = json.loads((self.root/config['base_config']).read_text())
        self.base = DenseRetriever(documents,base_config,root)
        self.chunks = self.base.chunks
        self.events = []
        catalogs = {name:context_catalog(text) for name,text in documents.items()}
        self.enrichment = [enrich_chunk(c,documents[c['file_path']],catalogs[c['file_path']],
                                       config['max_context_chars']) for c in self.chunks]
        identity = json.dumps(dict(config=config,base_identity=self.base.identity,
                                   chunks=self.chunks,enrichment=self.enrichment),sort_keys=True)
        key = hashlib.sha256(identity.encode()).hexdigest()
        self.cache_dir = self.root/'cache'/'enriched'/key
        self.cache_dir.mkdir(parents=True,exist_ok=True)
        path = self.cache_dir/'vectors.npy'
        meta_path = self.cache_dir/'metadata.json'
        if path.exists() and meta_path.exists():
            self.metadata = json.loads(meta_path.read_text())
            if hashlib.sha256(path.read_bytes()).hexdigest()!=self.metadata['vectors_sha256']:
                raise ValueError('Enriched vector checksum mismatch.')
            vectors = np.load(path,allow_pickle=False)
        else:
            vectors = self.base.index.reconstruct_n(0,len(self.chunks)).copy()
            indices = [i for i,row in enumerate(self.enrichment) if row['context']]
            started = perf_counter()
            lengths = []
            if indices:
                encoder = self.base.get_encoder()
                contexts = [self.enrichment[i]['context'] for i in indices]
                lengths = encoder.token_lengths(contexts)
                contexts = normalized(encoder.encode(contexts))
                vectors[indices] = normalized(vectors[indices]+config['context_weight']*contexts)
            vectors = normalized(vectors)
            np.save(path,vectors,allow_pickle=False)
            self.metadata = dict(chunk_count=len(self.chunks),enriched_chunks=len(indices),
                                 context_inputs_over_token_limit=sum(n>base_config['max_seq_length'] for n in lengths),
                                 context_encode_ms=(perf_counter()-started)*1000,
                                 vectors_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            meta_path.write_text(json.dumps(self.metadata,indent=2))
        self.index = faiss.IndexFlatIP(base_config['dimension'])
        self.index.add(normalized(vectors))

    def search(self, query, k=5):
        if k<1:
            raise ValueError('k must be positive.')
        if not query.strip():
            return []
        vector,metadata,cached = self.base.query_vector(query)
        started = perf_counter()
        scores,indices = self.index.search(vector,min(k,len(self.chunks)))
        hits = [dict(self.chunks[int(i)],score=float(score)) for score,i in zip(scores[0],indices[0])
                if i>=0 and score>0]
        hits.sort(key=lambda h:(-h['score'],h['file_path'],h['start']))
        self.events.append(dict(query=query,query_cached=cached,search_ms=(perf_counter()-started)*1000,
                                original_query_encode_ms=metadata['encode_ms']))
        return hits
