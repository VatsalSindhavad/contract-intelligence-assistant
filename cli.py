import argparse
import json
import sys

from llm_rewrite import CacheMissError
from search_service import DEFAULT_CONFIG, available_configs, build_model, config_label, search


def main(argv=None):
    parser = argparse.ArgumentParser(description='Search indexed contracts for relevant passages.')
    parser.add_argument('question', nargs='?', help='Natural-language question, quoted as one argument.')
    parser.add_argument('--config', default=DEFAULT_CONFIG, help='Saved configuration name.')
    parser.add_argument('--k', type=int, default=5, help='Number of passages, 1–20.')
    parser.add_argument('--json', action='store_true', dest='as_json', help='Print a machine-readable response.')
    parser.add_argument('--list-configs', action='store_true')
    args = parser.parse_args(argv)
    if args.list_configs:
        print('\n'.join(config_label(name) for name in available_configs()))
        return 0
    if not args.question:
        parser.error('Provide a quoted question or use --list-configs.')
    try:
        result = search(build_model(args.config), args.question, args.k)
    except CacheMissError as error:
        parser.exit(2, f'Error: {error}\nPrepare the approved rewrite cache separately. This CLI makes no model calls.\n')
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, f'Error: {error}\nRun notebook 01 first if prepared data is missing.\n')
    if args.as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Configuration: {result['configuration']}")
        print(f"{result['message']} Search: {result['latency_ms']:.1f} ms")
        for rank, hit in enumerate(result['hits'], 1):
            print(f"\n{rank}. {hit['file_path']}\nOffsets: [{hit['start']}, {hit['end']}) | Score: {hit['score']:.3f}")
            print(hit['text'])
        if result['hits']:
            print('\nMatches require review; this model is not calibrated to detect unavailable answers.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raise SystemExit(main())
