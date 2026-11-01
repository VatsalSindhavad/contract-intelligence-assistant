from project_paths import ROOT as PROJECT_ROOT, source_path
import json
from pathlib import Path
from time import perf_counter

from retrieval import BM25Retriever, load_corpus


ROOT = PROJECT_ROOT
DEFAULT_CONFIG = 'bm25_focused_stemmed'
DEMO_DEFAULT_CONFIG = 'llm_hybrid_gemini_broad10'
DEMO_CONFIGS = ('llm_hybrid_gemini_broad10','llm_hybrid_gemini_recovery20_31','bm25_baseline')
EXAMPLE_QUERY = 'Consider the Wireless Content License Agreement between Fox Mobile Entertainment and Glu Mobile; What is the expiration date of this contract?'
BETTER_CONFIGS = frozenset({'bm25_document_then_clause', 'bm25_focused_clause_fallback', 'bm25_focused_stemmed'})


def config_label(name):
    if name=='llm_hybrid_gemini_broad10':
        return f'{name} â€” Run 1: ten passages, cutoff 0.50 Â· Cache only'
    if name=='llm_hybrid_gemini_recovery20_31':
        return f'{name} — Run 2: Gemini 3.1 recovery at 0.45 · Cache only'
    if name=='llm_hybrid_gemini_recovery20':
        return f'{name} â€” Run 2: conditional recovery at 0.45 Â· Cache only'
    if name.startswith('hybrid_'):
        return f'{name} â€” Hybrid comparison'
    if name.startswith('dense_'):
        return f'{name} â€” Pure semantic comparison'
    if name.startswith('llm_'):
        return f'{name} â€” LLM comparison Â· Cache only'
    if name in BETTER_CONFIGS:
        return f'{name} â€” Better than baseline' + (' Â· Current best' if name == DEFAULT_CONFIG else '')
    if name == 'bm25_baseline':
        return f'{name} â€” Baseline'
    if name == 'bm25_b_030':
        return f'{name} â€” Small train gain; below acceptance minimum'
    if name == 'bm25_focused_clause':
        return f'{name} â€” Retrieval gain; failed abstention guardrail'
    return f'{name} â€” Rejected experiment'


def available_configs(root=ROOT):
    root = Path(root)
    configs = {p.stem: p for p in sorted((root / 'configs').glob('*.json'))}
    for path in sorted((root / 'llm_configs').glob('*.json')):
        config = json.loads(path.read_text(encoding='utf-8'))
        if config.get('expose_in_demo', False):
            configs[config['name']] = path
    return configs


def demo_configs(root=ROOT):
    all_configs=available_configs(root)
    return {name:all_configs[name] for name in DEMO_CONFIGS if name in all_configs}


def build_model(config_name=DEFAULT_CONFIG, root=ROOT):
    configs = available_configs(root)
    if config_name not in configs:
        raise ValueError(f'Unknown configuration: {config_name}')
    config = json.loads(configs[config_name].read_text(encoding='utf-8'))
    documents, _ = load_corpus(root)
    if config.get('retriever_type')=='reranked_hybrid':
        from rerank_retrieval import RerankRetriever
        base = build_model(Path(config['base_config']).stem,root)
        return RerankRetriever(base,root,config)
    if config.get('retriever_type')=='hybrid':
        from dense_retrieval import DenseRetriever
        from hybrid_retrieval import HybridRetriever
        lexical_config = json.loads((Path(root)/config['bm25_config']).read_text(encoding='utf-8'))
        dense_config = json.loads((Path(root)/config['dense_config']).read_text(encoding='utf-8'))
        return HybridRetriever(BM25Retriever(documents,lexical_config),
                               DenseRetriever(documents,dense_config,root),config)
    if config.get('retriever_type') in {'dense','enriched_dense'}:
        threshold = config.get('abstention_threshold')
        base_config = {key:value for key,value in config.items() if key!='abstention_threshold'}
        if config['retriever_type']=='enriched_dense':
            from reference_enrichment import EnrichedRetriever
            model = EnrichedRetriever(documents,base_config,root)
        else:
            from dense_retrieval import DenseRetriever
            model = DenseRetriever(documents,base_config,root)
        if threshold is not None:
            from clause_chunking import AbstentionRetriever
            return AbstentionRetriever(model,threshold)
        return model
    if config.get('provider'):
        if config.get('task')=='hybrid_recall_recovery':
            from recall_recovery import make_recovery_model
            return make_recovery_model(root,config)
        if config.get('task')=='hybrid_summary_with_evidence':
            from hosted_summary import HostedHybridSummaryRetriever
            base = build_model(Path(config['retrieval_config']).stem,root)
            return HostedHybridSummaryRetriever(base,root,config)
        if config.get('task')=='summary_with_evidence':
            from summary_retrieval import SummaryRetriever
            rewrite = json.loads((Path(root)/config['retrieval_config']).read_text(encoding='utf-8'))
            base_config = json.loads((Path(root)/rewrite['baseline_config']).read_text(encoding='utf-8'))
            from llm_rewrite import RewriteRetriever
            base = RewriteRetriever(BM25Retriever(documents,base_config),root,rewrite)
            return SummaryRetriever(base,root,config)
        from llm_rewrite import RewriteRetriever
        base_config = json.loads((Path(root) / config['baseline_config']).read_text(encoding='utf-8'))
        return RewriteRetriever(BM25Retriever(documents, base_config), root, config)
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
    result=dict(query=query, configuration=model.config['name'], k=k,
                status='matches' if hits else 'no_matches', latency_ms=elapsed,
                message=f'{len(hits)} passages retrieved.' if hits else 'No relevant passage found.',hits=hits)
    if hasattr(model,'last_summary'):
        result['summary']=model.last_summary
        result['summary_status']=model.events[-1]['status']
    return result
