import pytest

import wordprofile.formatter as form
from wordprofile.datatypes import Coocc
from wordprofile.wpse.wpse_spec import WpSeSpec


@pytest.fixture
def description_handler():
    return WpSeSpec()


def test_relation_not_modified_if_not_inverse(description_handler):
    collocation = Coocc(
        id=1,
        rel="GMOD",
        lemma1="",
        lemma2="",
        form1="",
        form2="",
        tag1="",
        tag2="",
        freq=10,
        score=3.0,
        inverse=0,
        has_mwe=0,
        num_concords=10,
    )
    result = form.format_relations([collocation], description_handler)[0]
    assert result["Relation"] == "GMOD"


def test_relation_retrieved_correctly_if_inverse(description_handler):
    collocation = Coocc(
        id=1,
        rel="GMOD",
        lemma1="",
        lemma2="",
        form1="",
        form2="",
        tag1="",
        tag2="",
        freq=10,
        score=3.0,
        inverse=1,
        has_mwe=0,
        num_concords=10,
    )
    result = form.format_relations([collocation], description_handler)[0]
    assert result["Relation"] == "~GMOD"


def test_correct_description_retrieved_if_not_inverse(description_handler):
    collocation = Coocc(
        id=1,
        rel="ATTR",
        lemma1="",
        lemma2="",
        form1="",
        form2="",
        tag1="",
        tag2="",
        freq=10,
        score=3.0,
        inverse=0,
        has_mwe=0,
        num_concords=10,
    )
    result = form.format_relations([collocation], description_handler)[0]
    assert result["RelationDescription"] == "hat Adjektivattribut"


def test_description_retrieved_correctly_if_inverse(description_handler):
    collocation = Coocc(
        id=1,
        rel="ATTR",
        lemma1="",
        lemma2="",
        form1="",
        form2="",
        tag1="",
        tag2="",
        freq=10,
        score=3.0,
        inverse=1,
        has_mwe=0,
        num_concords=10,
    )
    result = form.format_relations([collocation], description_handler)[0]
    assert result["RelationDescription"] == "ist Adjektivattribut von"


def test_default_coocc_id_in_comparison():
    input_diffs = [
        {
            "coocc_1": Coocc(
                id=-1,
                rel="OBJ",
                lemma1="Gesetz",
                lemma2="verabschieden",
                form1="Gesetz",
                form2="verabschiedet",
                tag1="NOUN",
                tag2="VERB",
                freq=29,
                score=10.3,
                inverse=1,
                has_mwe=0,
                num_concords=29,
            ),
            "rank_1": 0,
            "pos": "NOUN",
            "score": 10.3,
        },
        {
            "coocc_2": Coocc(
                id=-2,
                rel="OBJ",
                lemma1="Recht",
                lemma2="einfordern",
                form1="Recht",
                form2="einfordern",
                tag1="NOUN",
                tag2="VERB",
                freq=7,
                score=8.1,
                inverse=1,
                has_mwe=0,
                num_concords=7,
            ),
            "rank_2": 16,
            "pos": "NOUN",
            "score": -8.1,
        },
    ]
    formatted = form.format_comparison(input_diffs)
    result = [(diff["ConcordId1"], diff["ConcordId2"]) for diff in formatted]
    assert result == [(-1, None), (None, -2)]
