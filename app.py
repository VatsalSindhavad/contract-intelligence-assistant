import hashlib
import json

import streamlit as st

from llm_rewrite import CacheMissError
from search_service import DEFAULT_CONFIG, EXAMPLE_QUERY, ROOT, available_configs, build_model, config_label, search


st.set_page_config(page_title='Contract clause search', page_icon='📄', layout='wide')
st.title('Contract clause search')
st.write('Find relevant passages and check the original contract evidence.')
st.caption('Development demo: matching passages do not establish that a question is answerable.')

configs = available_configs()
if not configs:
    st.error('No saved configurations found.')
    st.stop()
names = list(configs)
selected = st.selectbox('Retrieval configuration', names, index=names.index(DEFAULT_CONFIG) if DEFAULT_CONFIG in names else 0, format_func=config_label)
st.caption('“Better than baseline” marks accepted train improvements. Held-out test performance is not yet measured.')
if selected.startswith('llm_'):
    st.info('This LLM comparison replays cached rewrites only. An uncached question produces an error and makes no API call.')
with st.form('search_form'):
    question = st.text_area('Question', value=EXAMPLE_QUERY, height=110,
                            help='For a named contract, use: Consider contract description; your question. Plain questions search the whole corpus.')
    k = st.slider('Number of passages', min_value=1, max_value=20, value=5)
    submitted = st.form_submit_button('Search')


@st.cache_resource(show_spinner=False)
def cached_model(name, fingerprint):
    return build_model(name)


if submitted:
    st.session_state.pop('search_result', None)
    if not question.strip():
        st.error('Enter a question.')
    else:
        try:
            manifest = ROOT / 'data/prepared/manifest.json'
            fingerprint = hashlib.sha256(configs[selected].read_bytes() + manifest.read_bytes()).hexdigest()
            with st.spinner('Searching contracts…'):
                model = cached_model(selected, fingerprint)
                st.session_state['search_result'] = search(model, question, k)
        except CacheMissError as error:
            st.error(str(error))
        except (ValueError, OSError, KeyError) as error:
            st.error(f'Unable to search: {error}. Run data preparation notebook 01 if needed.')

result = st.session_state.get('search_result')
if result:
    st.caption(f"Results for: {result['query']} | {result['configuration']} | {result['latency_ms']:.1f} ms")
    if not result['hits']:
        st.info(result['message'])
    for rank, hit in enumerate(result['hits'], 1):
        with st.expander(f"{rank}. {hit['file_path'].removeprefix('cuad/')} · score {hit['score']:.2f}", expanded=rank == 1):
            st.caption(f"Source: {hit['file_path']} | Character offsets [{hit['start']}, {hit['end']})")
            st.text(hit['text'])
    st.download_button('Download these results', data=json.dumps(result, ensure_ascii=False, indent=2),
                       file_name='contract_search.json', mime='application/json')
