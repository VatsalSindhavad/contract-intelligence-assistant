from reference_enrichment import context_catalog, enrich_chunk


def test_only_same_document_context_and_original_offsets():
    text='Section 1. Term.\n"Licensed Content" means the listed films.\nSection 2. Rights.\nLicensed Content may be used subject to Section 1.\n'
    start=text.index('Licensed Content may')
    chunk=dict(text=text[start:],start=start,end=len(text))
    enriched=enrich_chunk(chunk,text,context_catalog(text))
    assert enriched['sources']
    assert all(s['text']==text[s['start']:s['end']] for s in enriched['sources'])
    assert chunk['text']==text[start:]


def test_ambiguous_or_missing_sections_are_not_guessed():
    text='Section 1. First\nSection 1. Duplicate\nSection 3. Next\nRefer to Section 1 and Section 9.'
    start=text.index('Refer')
    enriched=enrich_chunk(dict(text=text[start:],start=start,end=len(text)),text,context_catalog(text))
    assert enriched['context']==''
    assert set(enriched['unresolved_sections'])=={'1','9'}


def test_context_budget_and_no_self_expansion():
    text='Section 1. Definition.\n'+('A long sentence. '*100)+'\nSection 2. Application.\nSee Section 1.'
    start=text.index('See Section')
    enriched=enrich_chunk(dict(text=text[start:],start=start,end=len(text)),text,context_catalog(text),80)
    assert sum(s['end']-s['start'] for s in enriched['sources'])<=80
    assert all(s['end']<=start for s in enriched['sources'])
