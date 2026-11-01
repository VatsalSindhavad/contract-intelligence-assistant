from copy import deepcopy

import pytest

from improve import choose_proposal, config_key, resume_state


BASE = dict(name='baseline', chunk_size=1000, chunk_overlap=200, b=0.75)
PROPOSALS = [
    dict(id='small', name='small', trigger='wrong_section', changes=dict(chunk_size=500)),
    dict(id='large', name='large', trigger='partial', changes=dict(chunk_size=1500)),
]


def test_choose_from_dominant_failure():
    proposal, config = choose_proposal(BASE, dict(wrong_section=10, partial=3), PROPOSALS, set(), set())
    assert proposal['id'] == 'small'
    assert config['chunk_size'] == 500
    assert BASE['chunk_size'] == 1000


def test_skip_tried_proposal_and_equivalent_config():
    proposal, _ = choose_proposal(BASE, dict(wrong_section=10), PROPOSALS, {'small'}, set())
    assert proposal['id'] == 'large'
    tried = {config_key(dict(BASE, chunk_size=500, name='different_name'))}
    proposal, _ = choose_proposal(BASE, dict(wrong_section=10), PROPOSALS, set(), tried)
    assert proposal['id'] == 'large'


def test_stop_when_catalog_exhausted():
    assert choose_proposal(BASE, {}, PROPOSALS, {'small', 'large'}, set()) == (None, None)


def test_resume_rejected_then_accepted_candidate():
    first = dict(iteration=1, candidate=dict(BASE, name='stopwords', remove_stopwords=True), selected_config=BASE)
    candidate = dict(BASE, name='small', chunk_size=500)
    second = dict(iteration=2, proposal=dict(id='small'), reference_config=BASE,
                  candidate_config=candidate, selected_config=candidate)
    current, tried_ids, _, iteration = resume_state(BASE, [first], [second])
    assert current == candidate
    assert tried_ids == {'small'}
    assert iteration == 3


def test_rejection_preserves_current_for_next_iteration():
    entry = dict(iteration=1, proposal=dict(id='small'), reference_config=BASE,
                 candidate_config=dict(BASE, chunk_size=500), selected_config=BASE)
    current, _, _, iteration = resume_state(BASE, [], [entry])
    assert current == BASE
    assert iteration == 2


def test_invalid_history_does_not_silently_resume():
    entry = dict(iteration=2, reference_config=BASE)
    with pytest.raises(ValueError, match='inconsistent'):
        resume_state(BASE, [], [entry])


def test_default_stopword_setting_has_same_identity():
    assert config_key(BASE) == config_key(dict(BASE, remove_stopwords=False))


def test_invalid_overlap_candidate_is_skipped():
    proposals = deepcopy(PROPOSALS)
    proposals[0]['changes']['chunk_size'] = 100
    selected, _ = choose_proposal(BASE, dict(wrong_section=10), proposals, set(), set())
    assert selected['id'] == 'large'
