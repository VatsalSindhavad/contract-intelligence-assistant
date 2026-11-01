from project_paths import ROOT as PROJECT_ROOT


def main():
    if (PROJECT_ROOT/'data/prepared/manifest.json').exists():
        from retrieval import load_inputs
        rows,docs,_=load_inputs(PROJECT_ROOT)
        print('Existing prepared data verified:',len(rows),'train questions,',len(docs),'contracts. No test evaluation.')
        return
    from pathlib import Path
    import hashlib
    import json
    import random
    import sys
    from urllib.parse import quote
    import requests

    ROOT = PROJECT_ROOT
    if ROOT.name == 'notebooks':
        ROOT = ROOT.parent
    assert (ROOT / 'requirements.txt').exists(), 'Run from the project or notebooks directory.'
    DATA = ROOT / 'data'
    REVISION = '2b9c248bc8179ef0908fd6ba01d50b156facd48b'
    BASE_URL = f'https://huggingface.co/datasets/awinml/legalbench-rag/resolve/{REVISION}'

    def download(relative_path):
        destination = DATA / relative_path
        if not destination.exists():
            response = requests.get(f'{BASE_URL}/{quote(relative_path, safe="/")}', timeout=90)
            response.raise_for_status()
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(destination.suffix + '.part')
            temporary.write_bytes(response.content)
            temporary.replace(destination)
        return destination

    print('Python:', sys.version.split()[0])
    print('Dataset revision:', REVISION)

    def mini(tests, n=194):
        if len(tests) <= n:
            return tests
        def key(test):
            random.seed(test['snippets'][0]['file_path'])
            return random.random()
        return sorted(tests, key=key)[:n]

    def assign_split(query):
        value = int(hashlib.sha256(query.strip().encode('utf-8')).hexdigest(), 16)
        return 'test' if value % 10 < 3 else 'train'

    benchmark_path = download('benchmarks/cuad.json')
    tests = json.loads(benchmark_path.read_text(encoding='utf-8'))['tests']
    selected = mini(tests)
    assert len(selected) == 194
    records = [dict(test, query_id=hashlib.sha256(test['query'].strip().encode('utf-8')).hexdigest(),
                    split=assign_split(test['query'])) for test in selected]
    assert len({r['query_id'] for r in records}) == len(records), 'Duplicate selected questions.'
    paths = sorted({s['file_path'] for r in records for s in r['snippets']})
    assert all(p.startswith('cuad/') and '..' not in Path(p).parts for p in paths)
    print('Full CUAD questions:', len(tests))
    print('Selected questions:', len(records))
    print('Referenced contracts:', len(paths))
    print('Split counts:', {split: sum(r['split'] == split for r in records) for split in ['train', 'test']})

    documents = {}
    for file_path in paths:
        local_path = download('corpus/' + file_path)
        # Default text mode translates CRLF to LF, preserving benchmark offsets.
        with local_path.open('r', encoding='utf-8') as handle:
            documents[file_path] = handle.read()

    checked = 0
    for record in records:
        for snippet in record['snippets']:
            text = documents[snippet['file_path']]
            start, end = snippet['span']
            assert 0 <= start < end <= len(text), (record['query_id'], 'Invalid bounds')
            assert text[start:end] == snippet['answer'], (record['query_id'], 'Answer mismatch')
            checked += 1
    print(f'Validated {checked} answer spans across {len(documents)} contracts.')

    prepared = DATA / 'prepared'
    prepared.mkdir(parents=True, exist_ok=True)
    for split in ['train', 'test']:
        output = prepared / f'{split}.json'
        output.write_text(json.dumps([r for r in records if r['split'] == split],
                                     ensure_ascii=False, indent=2), encoding='utf-8')

    digest = lambda value: hashlib.sha256(value).hexdigest()
    manifest = {
        'dataset': 'awinml/legalbench-rag', 'revision': REVISION,
        'selection': 'prescribed mini function, n=194',
        'split': 'sha256(query.strip()) modulo 10 < 3 => test',
        'question_count': len(records), 'contract_count': len(documents),
        'validated_spans': checked,
        'split_counts': {s: sum(r['split'] == s for r in records) for s in ['train', 'test']},
        'benchmark_sha256': digest(benchmark_path.read_bytes()),
        'corpus': {p: {'raw_sha256': digest((DATA / 'corpus' / p).read_bytes()),
                       'text_sha256': digest(documents[p].encode('utf-8'))} for p in paths},
        'prepared_sha256': {s: digest((prepared / f'{s}.json').read_bytes()) for s in ['train', 'test']},
        'test_evaluation_runs': 0,
    }
    (prepared / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Prepared files saved under:', prepared)
    print('Test evaluation runs: 0')


if __name__=='__main__':
    main()
