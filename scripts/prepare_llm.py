from project_paths import ROOT as PROJECT_ROOT, source_path
import argparse
from collections import Counter
from pathlib import Path
from time import sleep

from improve import read_json, read_log, verify_freeze
from llm_rewrite import CacheMissError, get_rewrite, load_gemini_key
from negative_validation import validate_negatives
from retrieval import clause_question, load_inputs


def train_questions(root):
    records, documents, _ = load_inputs(root)
    negatives, _ = validate_negatives(root, documents)
    records += [r for r in negatives if r['split'] == 'train']
    return sorted({clause_question(r['query']) or r['query'] for r in records})


def main():
    parser = argparse.ArgumentParser(description='Inspect or populate train-only LLM rewrite caches. No evaluation is performed.')
    parser.add_argument('--config', choices=['gemini', 'local_phi3'], default='gemini')
    parser.add_argument('--fill', action='store_true', help='Explicitly allow model calls for missing entries.')
    parser.add_argument('--max-new', type=int, default=1, help='Maximum new calls; default one for a connection check.')
    parser.add_argument('--retry-failed', action='store_true', help='Retry failed transport/HTTP attempts, retaining their history.')
    parser.add_argument('--pause', type=float, default=4, help='Seconds between new requests, default 4.')
    args = parser.parse_args()
    if args.max_new < 1:
        parser.error('--max-new must be positive.')
    root = PROJECT_ROOT
    verify_freeze(root)
    config = read_json(root / 'llm_configs' / f'{args.config}.json')
    if args.fill and args.config == 'local_phi3':
        if not any(r['iteration']==9 for r in read_log(root/'experiments/llm_log.jsonl')):
            parser.error('Complete hosted iteration 9 before local generation.')
        import requests
        tags=requests.get('http://127.0.0.1:11434/api/tags',timeout=10).json()
        models=[m for m in tags['models'] if m['name']==config['model']]
        version=requests.get('http://127.0.0.1:11434/api/version',timeout=10).json()['version']
        if not models or models[0]['digest']!=config['model_revision'] or config['runtime']!='ollama-'+version:
            parser.error('Local model/runtime differs from the recorded configuration.')
    if args.fill and config['provider'] == 'gemini' and not load_gemini_key(root):
        parser.exit(2, 'Gemini key is not configured. See LLM_SETUP.md. No model call was made.\n')
    counts, made = Counter(), 0
    questions = train_questions(root)
    for question in questions:
        entry = None
        try:
            entry, _ = get_rewrite(root, config, question, cache_only=True)
        except CacheMissError:
            pass
        needs_call = entry is None or (args.retry_failed and entry['status'] in ['http_error', 'transport_error'])
        if needs_call and args.fill and made < args.max_new:
            if made and args.pause > 0:
                sleep(min(args.pause, 60))
            entry, _ = get_rewrite(root, config, question, cache_only=False, retry_failed=args.retry_failed)
            made += 1
            print(f'New response {made}: {entry["status"]}', flush=True)
            if entry['status'] in ['http_error', 'transport_error']:
                counts[entry['status']] += 1
                print('Stopped after provider failure; cached status contains no key. Check access/quota before retrying.')
                break
        counts[entry['status'] if entry else 'missing'] += 1
    print('Provider/model:', config['provider'], config['model'])
    print('Unique train clause questions:', len(questions))
    print('Cache status:', dict(counts))
    print('New model calls:', made)
    print('No test questions or retrieval metrics were evaluated.')


if __name__ == '__main__':
    main()
