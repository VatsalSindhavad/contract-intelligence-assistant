from project_paths import ROOT as PROJECT_ROOT, source_path
import hashlib
import json
from collections import Counter
from pathlib import Path


def assign_split(query):
    value = int(hashlib.sha256(query.strip().encode('utf-8')).hexdigest(), 16)
    return 'test' if value % 10 < 3 else 'train'


def validate_negatives(root, documents):
    root = Path(root)
    query_path = root / 'evaluation' / 'unanswerable.json'
    frozen = json.loads((root / 'evaluation' / 'frozen_manifest.json').read_text(encoding='utf-8'))
    if hashlib.sha256(query_path.read_bytes()).hexdigest() != frozen['query_set_sha256']:
        raise ValueError('Frozen negative questions were modified.')
    actual_hashes = {p: hashlib.sha256(text.encode('utf-8')).hexdigest()
                     for p, text in documents.items()}
    if actual_hashes != frozen['corpus_text_sha256']:
        raise ValueError('Corpus differs from the frozen labeling corpus.')
    records = json.loads(query_path.read_text(encoding='utf-8'))
    if len(records) < 30 or len(records) != frozen['question_count']:
        raise ValueError('At least 30 frozen questions are required.')
    if len({r['query'].strip().lower() for r in records}) != len(records):
        raise ValueError('Duplicate negative questions.')
    for record in records:
        query_id = hashlib.sha256(record['query'].strip().encode('utf-8')).hexdigest()
        if record['query_id'] != query_id or record['split'] != assign_split(record['query']):
            raise ValueError('Question identity or split mismatch.')
        if record['answerable'] is not False or record['snippets'] or not record['reason']:
            raise ValueError('Missing negative label or rationale.')
        source = record['source_document']
        if source is not None and source not in documents:
            raise ValueError('Unknown source document.')
        if not record['absent_anchors']:
            raise ValueError('Missing supporting absence checks.')
        for anchor in record['absent_anchors']:
            if any(anchor.casefold() in text.casefold() for text in documents.values()):
                raise ValueError(f'Absence check failed: {anchor}')
    if dict(Counter(r['split'] for r in records)) != frozen['split_counts']:
        raise ValueError('Frozen split counts differ.')
    return records, frozen


def evaluate_negative_train(retriever, records, k=5):
    if not records or any(r['split'] != 'train' or r['answerable'] is not False for r in records):
        raise ValueError('Only train negatives may enter this development evaluator.')
    predictions = []
    for record in records:
        hits = retriever.search(record['query'], k=k)
        predictions.append(dict(query_id=record['query_id'], category=record['category'],
                                query=record['query'], abstained=not hits, hits=hits))
    correct = sum(p['abstained'] for p in predictions)
    return dict(n_queries=len(records), correct_abstentions=correct,
                correct_abstention_rate=correct / len(records),
                false_return_rate=1 - correct / len(records), predictions=predictions)
