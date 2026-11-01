from time import perf_counter

import numpy as np

from retrieval import character_metrics, benchmark_character_metrics


def evaluate_test(model, answerable, negatives, documents, k_values=(1,3,5,10)):
    if not answerable or any(row['split']!='test' for row in answerable):
        raise ValueError('Held-out evaluator requires test answerable records.')
    if not negatives or any(row['split']!='test' or row['answerable'] is not False for row in negatives):
        raise ValueError('Held-out evaluator requires test negative records.')
    predictions,rows,timings = [],[],[]
    for record in answerable:
        started=perf_counter()
        hits=model.search(record['query'],max(k_values))
        elapsed=(perf_counter()-started)*1000
        timings.append(elapsed)
        for hit in hits:
            if documents[hit['file_path']][hit['start']:hit['end']]!=hit['text']:
                raise ValueError('Returned source evidence does not match its offsets.')
        predictions.append(dict(query_id=record['query_id'],query=record['query'],hits=hits,latency_ms=elapsed))
        for k in k_values:
            rows.append(dict(query_id=record['query_id'],k=k,**character_metrics(hits[:k],record['snippets']),
                             **benchmark_character_metrics(hits[:k],record['snippets'])))
    metrics=[]
    for k in k_values:
        selected=[row for row in rows if row['k']==k]
        metrics.append(dict(k=k,n_queries=len(answerable),**{name:float(np.mean([r[name] for r in selected]))
                            for name in ['precision','recall','hit','benchmark_precision','benchmark_recall']}))
    negative_predictions=[]
    for record in negatives:
        hits=model.search(record['query'],5)
        for hit in hits:
            if documents[hit['file_path']][hit['start']:hit['end']]!=hit['text']:
                raise ValueError('Returned negative-query evidence has invalid offsets.')
        negative_predictions.append(dict(query_id=record['query_id'],query=record['query'],hits=hits,abstained=not hits))
    correct=sum(row['abstained'] for row in negative_predictions)
    return dict(answerable=dict(metrics=metrics,predictions=predictions,per_query=rows,
                               latency_ms=dict(median=float(np.median(timings)),p95=float(np.percentile(timings,95))),
                               answerable_false_abstention_rate=sum(not row['hits'] for row in predictions)/len(answerable)),
                negative=dict(n_queries=len(negatives),correct_abstentions=correct,
                              correct_abstention_rate=correct/len(negatives),false_return_rate=1-correct/len(negatives),
                              predictions=negative_predictions))
