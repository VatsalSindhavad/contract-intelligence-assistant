from project_paths import ROOT as PROJECT_ROOT, source_path
from time import perf_counter


def reciprocal_rank_fusion(rankings, weights, constant=60):
    if len(rankings)!=len(weights) or constant<=0 or any(w<0 for w in weights):
        raise ValueError('Invalid rank-fusion parameters.')
    merged = {}
    for hits,weight in zip(rankings,weights):
        seen = set()
        for rank,hit in enumerate(hits,1):
            key = (hit['file_path'],hit['start'],hit['end'])
            if key in seen:
                continue
            seen.add(key)
            if key not in merged:
                merged[key] = dict(hit,score=0.0)
            merged[key]['score'] += weight/(constant+rank)
    return sorted(merged.values(),key=lambda h:(-h['score'],h['file_path'],h['start']))


class HybridRetriever:
    def __init__(self, bm25, dense, config):
        self.bm25,self.dense,self.config = bm25,dense,config
        self.events = []

    def search(self, query, k=5):
        if k<1:
            raise ValueError('k must be positive.')
        if not query.strip():
            return []
        started = perf_counter()
        pool = max(k,self.config['candidate_pool'])
        lexical = self.bm25.search(query,pool)
        semantic = self.dense.search(query,pool)
        confidence = semantic[0]['score'] if semantic else -1
        hits = reciprocal_rank_fusion([lexical,semantic],
                                     [self.config['bm25_weight'],1-self.config['bm25_weight']],
                                     self.config['rrf_constant'])[:k]
        threshold = self.config.get('dense_confidence_threshold')
        if threshold is not None and confidence<=threshold:
            hits = []
        self.events.append(dict(query=query,dense_top_score=confidence,
                                lexical_candidates=len(lexical),dense_candidates=len(semantic),
                                replay_ms=(perf_counter()-started)*1000))
        return hits
