import argparse
from collections import Counter
from pathlib import Path

from improve import read_json, verify_freeze
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
    args = parser.parse_args()
    if args.max_new < 1:
        parser.error('--max-new must be positive.')
    root = Path(__file__).resolve().parent
    verify_freeze(root)
    config = read_json(root / 'llm_configs' / f'{args.config}.json')
    if args.fill and args.config == 'local_phi3':
        parser.error('Local calls are deferred until the hosted experiment is complete.')
    if args.fill and config['provider'] == 'gemini' and not load_gemini_key(root):
        parser.exit(2, 'Gemini key is not configured. See LLM_SETUP.md. No model call was made.\n')
    counts, made = Counter(), 0
    questions = train_questions(root)
    for question in questions:
        try:
            entry, _ = get_rewrite(root, config, question, cache_only=True)
        except CacheMissError:
            if not args.fill or made >= args.max_new:
                counts['missing'] += 1
                continue
            entry, _ = get_rewrite(root, config, question, cache_only=False)
            made += 1
            print(f'New response {made}: {entry["status"]}', flush=True)
            if entry['status'] in ['http_error', 'transport_error']:
                counts[entry['status']] += 1
                print('Stopped after provider failure; cached status contains no key. Check access/quota before retrying.')
                break
        counts[entry['status']] += 1
    print('Provider/model:', config['provider'], config['model'])
    print('Unique train clause questions:', len(questions))
    print('Cache status:', dict(counts))
    print('New model calls:', made)
    print('No test questions or retrieval metrics were evaluated.')


if __name__ == '__main__':
    main()
