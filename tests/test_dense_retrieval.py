import numpy as np
import pytest

pytest.importorskip('faiss')
from dense_retrieval import DenseRetriever,normalized


class Encoder:
    def encode(self,texts):
        return np.array([[1,0] if 'apple' in t else [0,1] for t in texts],dtype=np.float32)
    def token_lengths(self,texts):
        return [len(t.split()) for t in texts]


def config():
    return dict(name='dense_test',chunk_size=100,chunk_overlap=0,dimension=2,
                max_seq_length=256,torch_threads=1,min_score=0)


def test_cosine_search_matches_expected_vector_and_original_offsets(tmp_path):
    model=DenseRetriever({'a':'apple licensing','b':'money payment'},config(),tmp_path,Encoder())
    hit=model.search('apple',1)[0]
    assert hit['file_path']=='a'
    assert hit['score']==pytest.approx(1)
    assert hit['text']=='apple licensing'[hit['start']:hit['end']]


def test_vectors_replay_without_loading_any_encoder(tmp_path):
    first=DenseRetriever({'a':'apple','b':'money'},config(),tmp_path,Encoder())
    expected=first.search('apple',2)
    class Fail:
        def encode(self,texts): raise AssertionError('Must use cached vectors.')
        def token_lengths(self,texts): raise AssertionError('Must use cached metadata.')
    replay=DenseRetriever({'a':'apple','b':'money'},config(),tmp_path,Fail())
    assert replay.search('apple',2)==expected
    assert replay.events[0]['query_cached']


def test_cache_identity_changes_with_corpus_and_model_settings(tmp_path):
    a=DenseRetriever({'a':'apple'},config(),tmp_path,Encoder())
    b=DenseRetriever({'a':'apple new'},config(),tmp_path,Encoder())
    c=DenseRetriever({'a':'apple'},dict(config(),revision='different'),tmp_path,Encoder())
    assert len({a.cache_dir,b.cache_dir,c.cache_dir})==3


def test_invalid_vector_and_invalid_k_are_rejected(tmp_path):
    with pytest.raises(ValueError): normalized([[0,0]])
    with pytest.raises(ValueError): normalized([[float('nan'),1]])
    model=DenseRetriever({'a':'apple'},config(),tmp_path,Encoder())
    with pytest.raises(ValueError): model.search('apple',0)
    assert model.search('')==[]


def test_corrupted_document_cache_fails(tmp_path):
    first=DenseRetriever({'a':'apple'},config(),tmp_path,Encoder())
    (first.cache_dir/'documents.npy').write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='checksum'):
        DenseRetriever({'a':'apple'},config(),tmp_path,Encoder())
