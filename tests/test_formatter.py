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
