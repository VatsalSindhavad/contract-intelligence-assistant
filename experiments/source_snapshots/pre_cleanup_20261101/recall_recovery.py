import json
from pathlib import Path
from time import perf_counter

from hosted_summary import cached_gemini_summary
from summary_retrieval import NO_ANSWER


class RecoverySummaryRetriever:
    def __init__(self, base, root, config, previous=None):
        self.base,self.root,self.config,self.previous = base,Path(root),config,previous
        self.events = []
        self.last_summary = None

    def resolve(self, query, cache_only=True, caller=None):
        previous_ms = 0
        if self.previous is not None:
            prior,_ = self.previous.resolve(query,cache_only=True)
            previous_ms = prior.get('model_call_ms',0)
            if prior['status'] in {'http_error','transport_error'}:
                raise RuntimeError('Finish the first-stage cache before recovery.')
            if prior['status']=='valid' and prior['hits']:
                return prior,dict(decision='reuse_supported_answer',first_stage_model_ms=previous_ms,
                                  additional_model_ms=0)
        hits = self.base.search(query,self.config['candidate_k'])
        if not hits:
            return dict(status='upstream_abstention',hits=[],summary=NO_ANSWER,model_call_ms=0),dict(
                decision='upstream_abstention',first_stage_model_ms=previous_ms,additional_model_ms=0)
        entry,_ = cached_gemini_summary(self.root,self.config,query,hits,cache_only=cache_only,caller=caller)
        return entry,dict(decision='recovery' if self.previous else 'first_stage',
                          first_stage_model_ms=previous_ms,additional_model_ms=entry['model_call_ms'])

    def search(self, query, k=5):
        started = perf_counter()
        entry,decision = self.resolve(query)
        self.last_summary = entry['summary']
        event = dict(query=query,status=entry['status'],summary=entry['summary'],**decision,
                     replay_ms=(perf_counter()-started)*1000)
        if 'cache_key' in entry:
            event['cache_key'] = entry['cache_key']
        self.events.append(event)
        return entry['hits'][:k]


def make_recovery_model(root, config):
    from search_service import build_model
    root = Path(root)
    previous = None
    if config.get('previous_config'):
        previous = make_recovery_model(root,json.loads((root/config['previous_config']).read_text()))
    return RecoverySummaryRetriever(build_model(Path(config['retrieval_config']).stem,root),root,config,previous)
