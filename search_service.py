import json
from pathlib import Path
from time import perf_counter

from retrieval import BM25Retriever, load_corpus


ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = 'bm25_focused_stemmed'
EXAMPLE_QUERY = 'Consider the Wireless Content License Agreement between Fox Mobile Entertainment and Glu Mobile; What is the expiration date of this contract?'
BETTER_CONFIGS = frozenset({'bm25_document_then_clause', 'bm25_focused_clause_fallback', 'bm25_focused_stemmed'})


def config_label(name):
    if name in BETTER_CONFIGS:
        return f'{name} — Better than baseline' + (' · Current best' if name == DEFAULT_CONFIG else '')
    if name == 'bm25_baseline':
        return f'{name} — Baseline'
    if name == 'bm25_b_030':
        return f'{name} — Small train gain; below acceptance minimum'
    if name == 'bm25_focused_clause':
        return f'{name} — Retrieval gain; failed abstention guardrail'
    return f'{name} — Rejected experiment'


def available_configs(root=ROOT):
    return {p.stem: p for p in sorted((Path(root) / 'configs').glob('*.json'))}


def build_model(config_name=DEFAULT_CONFIG, root=ROOT):
    configs = available_configs(root)
    if config_name not in configs:
        raise ValueError(f'Unknown configuration: {config_name}')
    config = json.loads(configs[config_name].read_text(encoding='utf-8'))
    documents, _ = load_corpus(root)
    return BM25Retriever(documents, config)


def search(model, query, k=5):
    query = query.strip()
    if not query:
        raise ValueError('Enter a question.')
    if not 1 <= k <= 20:
        raise ValueError('Number of passages must be between 1 and 20.')
    started = perf_counter()
    hits = model.search(query, k=k)
    elapsed = (perf_counter() - started) * 1000
    return dict(query=query, configuration=model.config['name'], k=k,
                status='matches' if hits else 'no_matches', latency_ms=elapsed,
                message=f'{len(hits)} passages retrieved.' if hits else 'No relevant passage found.',
                hits=hits)
