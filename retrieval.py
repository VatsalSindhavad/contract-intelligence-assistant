import hashlib
import json
import re
from pathlib import Path
from time import perf_counter

import numpy as np
from rank_bm25 import BM25Okapi

STOPWORDS = frozenset('a an and are as at be been being by do does for from had has have how i if in into is it its of on or that the their them there these they this those to was were what when where which who will with would'.split())

def load_inputs(root):
    root = Path(root)
    prepared = root / 'data' / 'prepared'
    manifest = json.loads((prepared / 'manifest.json').read_text(encoding='utf-8'))
    train_path = prepared / 'train.json'
    assert hashlib.sha256(train_path.read_bytes()).hexdigest() == manifest['prepared_sha256']['train']
    train = json.loads(train_path.read_text(encoding='utf-8'))
    assert all(r['split'] == 'train' for r in train)
    documents = {}
    for file_path, hashes in manifest['corpus'].items():
        text = (root / 'data' / 'corpus' / file_path).read_text(encoding='utf-8')
        assert hashlib.sha256(text.encode('utf-8')).hexdigest() == hashes['text_sha256']
        documents[file_path] = text
    return train, documents, manifest


def make_chunks(documents, size=1000, overlap=200):
    if not 0 <= overlap < size:
        raise ValueError('Require 0 <= overlap < size.')
    chunks = []
    for file_path, text in sorted(documents.items()):
        for start in range(0, len(text), size - overlap):
            end = min(start + size, len(text))
            chunks.append(dict(file_path=file_path, start=start, end=end, text=text[start:end]))
            if end == len(text):
                break
    return chunks


def tokenize(text, remove_stopwords=False):
    tokens = re.findall(r'\b\w+\b', text.lower())
    return [token for token in tokens if token not in STOPWORDS] if remove_stopwords else tokens


class BM25Retriever:
    def __init__(self, documents, config):
        self.config = dict(config)
        self.chunks = make_chunks(documents, config['chunk_size'], config['chunk_overlap'])
        if not self.chunks:
            raise ValueError('The corpus is empty.')
        self.remove_stopwords = config.get('remove_stopwords', False)
        tokens = [tokenize(c['text'], self.remove_stopwords) for c in self.chunks]
        if not any(tokens):
            raise ValueError('The corpus has no searchable tokens.')
        self.index = BM25Okapi(tokens, k1=config['k1'], b=config['b'])

    def search(self, query, k=5):
        if k < 1:
            raise ValueError('k must be positive.')
        tokens = tokenize(query, self.remove_stopwords)
        if not tokens:
            return []
        scores = self.index.get_scores(tokens)
        order = np.argsort(-scores, kind='stable')[:k]
        return [dict(self.chunks[i], score=float(scores[i])) for i in order
                if scores[i] > self.config['min_score']]


def merged_spans(items):
    grouped = {}
    for item in items:
        start, end = item['span'] if 'span' in item else (item['start'], item['end'])
        grouped.setdefault(item['file_path'], []).append((start, end))
    result = {}
    for path, spans in grouped.items():
        merged = []
        for start, end in sorted(spans):
            if merged and start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
            else:
                merged.append((start, end))
        result[path] = merged
    return result


def character_metrics(predicted, gold):
    retrieved, relevant = merged_spans(predicted), merged_spans(gold)
    retrieved_count = sum(b - a for spans in retrieved.values() for a, b in spans)
    relevant_count = sum(b - a for spans in relevant.values() for a, b in spans)
    intersection = sum(max(0, min(b, d) - max(a, c))
                       for path, spans in retrieved.items() for a, b in spans
                       for c, d in relevant.get(path, []))
    return {
        'precision': intersection / retrieved_count if retrieved_count else 0.0,
        'recall': intersection / relevant_count if relevant_count else 0.0,
        'hit': int(intersection > 0),
    }


def benchmark_character_metrics(predicted, gold):
    retrieved_length = sum(p['end'] - p['start'] for p in predicted)
    gold_length = sum(g['span'][1] - g['span'][0] for g in gold)
    overlap = sum(max(0, min(p['end'], g['span'][1]) - max(p['start'], g['span'][0]))
                  for p in predicted for g in gold if p['file_path'] == g['file_path'])
    return dict(benchmark_precision=overlap / retrieved_length if retrieved_length else 0.0,
                benchmark_recall=overlap / gold_length if gold_length else 0.0)


def evaluate_train(retriever, records, k_values):
    if not records or any(r['split'] != 'train' for r in records):
        raise ValueError('This development evaluator accepts train records only.')
    predictions, rows, timings = [], [], []
    for record in records:
        started = perf_counter()
        hits = retriever.search(record['query'], max(k_values))
        elapsed = (perf_counter() - started) * 1000
        timings.append(elapsed)
        predictions.append(dict(query_id=record['query_id'], query=record['query'],
                                latency_ms=elapsed, hits=hits))
        for k in k_values:
            rows.append(dict(query_id=record['query_id'], k=k,
                             **character_metrics(hits[:k], record['snippets']),
                             **benchmark_character_metrics(hits[:k], record['snippets'])))
    summary = []
    for k in k_values:
        subset = [r for r in rows if r['k'] == k]
        summary.append(dict(k=k, n_queries=len(records),
                            **{metric: float(np.mean([r[metric] for r in subset]))
                               for metric in ['precision', 'recall', 'hit', 'benchmark_precision', 'benchmark_recall']}))
    return dict(metrics=summary, predictions=predictions, per_query=rows,
                latency_ms={'median': float(np.median(timings)),
                            'p95': float(np.percentile(timings, 95))},
                answerable_false_abstention_rate=sum(not p['hits'] for p in predictions) / len(records),
                unanswerable_correct_abstention_rate=None)
