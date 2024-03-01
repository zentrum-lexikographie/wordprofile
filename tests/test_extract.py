import pytest

import wordprofile.extract as ex
from wordprofile.datatypes import DBToken, DependencyTree


@pytest.fixture
def inverted_relations():
    return {
        "amod": {("NOUN", "ADJ"): "ATTR"},
        ("nmod", "case"): {
            ("NOUN", "NOUN", "ADP"): "PP",
        },
    }


def test_inverting_of_relation_patterns():
    result = ex.get_inverted_relation_patterns()
    assert list(result.keys()) == [
        "advmod",
        "amod",
        ("conj", "cc"),
        "obj",
        "iobj",
        ("nmod", "case"),
        ("obl", "case"),
        "nsubj:pass",
        "compound:prt",
    ]
    assert result["advmod"] == {("VERB", "ADV"): "ADV", ("ADJ", "ADV"): "ADV"}
    assert result[("conj", "cc")] == {
        ("NOUN", "NOUN", "CCONJ"): "KON",
        ("VERB", "VERB", "CCONJ"): "KON",
        ("ADJ", "ADJ", "CCONJ"): "KON",
    }


def test_extract_matches_by_pattern(inverted_relations):
    sentence = [
        DBToken(
            idx=1, surface="eine", lemma="eine", tag="DET", head=3, rel="det", misc=True
        ),
        DBToken(
            idx=2,
            surface="ganze",
            lemma="ganz",
            tag="ADJ",
            head=3,
            rel="amod",
            misc=True,
        ),
        DBToken(
            idx=3,
            surface="Epoche",
            lemma="Epoche",
            tag="NOUN",
            head=0,
            rel="ROOT",
            misc=False,
        ),
    ]
    result = list(ex.extract_matches_by_pattern(inverted_relations, sentence, 13))[0]
    assert (result.head.surface, result.head.tag) == ("Epoche", "NOUN")
    assert (result.dep.surface, result.dep.head, result.dep.rel) == ("ganze", 3, "amod")
    assert (result.relation, result.sid) == ("ATTR", 13)


def test_extract_matches_by_pattern_with_ternary_relation(inverted_relations):
    sentence = [
        DBToken(
            idx=1,
            surface="Haus",
            lemma="Haus",
            tag="NOUN",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        DBToken(
            idx=2,
            surface="am",
            lemma="an",
            tag="ADP",
            head=3,
            rel="case",
            misc=True,
        ),
        DBToken(
            idx=3,
            surface="Meer",
            lemma="Meer",
            tag="NOUN",
            head=1,
            rel="nmod",
            misc=True,
        ),
    ]
    result = list(ex.extract_matches_by_pattern(inverted_relations, sentence, 13))[0]
    assert (result.head.surface, result.dep.surface, result.prep.surface) == (
        "Haus",
        "Meer",
        "am",
    )
    assert result.relation == "PP"


def test_extract_predicatives_noun():
    sentence = [
        DBToken(
            idx=1,
            surface="Maßlosigkeit",
            lemma="Maßlosigkeit",
            tag="NOUN",
            head=4,
            rel="nsubj",
            misc=True,
        ),
        DBToken(
            idx=2,
            surface="war",
            lemma="sein",
            tag="AUX",
            head=4,
            rel="cop",
            misc=True,
        ),
        DBToken(
            idx=3,
            surface="die",
            lemma="d",
            tag="DET",
            head=4,
            rel="det",
            misc=True,
        ),
        DBToken(
            idx=4,
            surface="Folge",
            lemma="Folge",
            tag="NOUN",
            head=0,
            rel="ROOT",
            misc=False,
        ),
    ]
    result = list(ex.extract_predicatives(DependencyTree(sentence), 1))[0]
    assert (result.head.surface, result.dep.surface, result.relation) == (
        "Maßlosigkeit",
        "Folge",
        "PRED",
    )


def test_extract_predicatives_noun_with_prep_phrase():
    sentence = [
        DBToken(
            idx=1,
            surface="Ohne",
            lemma="ohne",
            tag="ADP",
            head=3,
            rel="case",
            misc=True,
        ),
        DBToken(
            idx=2, surface="die", lemma="d", tag="DET", head=3, rel="det", misc=True
        ),
        DBToken(
            idx=3,
            surface="Entwicklung",
            lemma="Entwicklung",
            tag="NOUN",
            head=8,
            rel="obl",
            misc=True,
        ),
        DBToken(
            idx=4, surface="ist", lemma="sein", tag="AUX", head=8, rel="cop", misc=True
        ),
        DBToken(
            idx=5, surface="der", lemma="d", tag="DET", head=8, rel="det", misc=True
        ),
        DBToken(
            idx=6,
            surface="Tag",
            lemma="Tag",
            tag="NOUN",
            head=8,
            rel="nsubj",
            misc=True,
        ),
        DBToken(
            idx=7,
            surface="nicht",
            lemma="nicht",
            tag="PART",
            head=8,
            rel="advmod",
            misc=True,
        ),
        DBToken(
            idx=8,
            surface="denkbar",
            lemma="denkbar",
            tag="ADJ",
            head=0,
            rel="ROOT",
            misc=False,
        ),
    ]
    result = list(ex.extract_predicatives(DependencyTree(sentence), 1))
    assert (result[0].relation, result[0].dep.surface) == ("PRED", "denkbar")


def test_extract_predicatives_verb():
    sentence = [
        DBToken(
            idx=1,
            surface="Sie",
            lemma="sie",
            tag="PRON",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        DBToken(
            idx=2,
            surface="befindet",
            lemma="befinden",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        DBToken(
            idx=3,
            surface="ihn",
            lemma="PRON",
            tag="er",
            head=2,
            rel="obj",
            misc=True,
        ),
        DBToken(
            idx=4,
            surface="für",
            lemma="für",
            tag="ADP",
            head=5,
            rel="case",
            misc=True,
        ),
        DBToken(
            idx=5,
            surface="schuldig",
            lemma="schuldig",
            tag="ADJ",
            head=2,
            rel="obl",
            misc=False,
        ),
    ]
    result = list(ex.extract_predicatives(DependencyTree(sentence), 1))[0]
    assert (result.relation, result.head.surface, result.dep.surface) == (
        "PRED",
        "befindet",
        "schuldig",
    )


def test_extract_genitives():
    sentence = [
        DBToken(
            idx=1, surface="Das", lemma="d", tag="PRON", head=4, rel="nsubj", misc=True
        ),
        DBToken(
            idx=2, surface="ist", lemma="sein", tag="AUX", head=4, rel="cop", misc=True
        ),
        DBToken(
            idx=3, surface="das", lemma="d", tag="DET", head=4, rel="det", misc=True
        ),
        DBToken(
            idx=4,
            surface="Ergebnis",
            lemma="Ergebnis",
            tag="NOUN",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        DBToken(
            idx=5,
            surface="unserer",
            lemma="unsere",
            tag="DET",
            head=7,
            rel="det",
            misc=True,
        ),
        DBToken(
            idx=6,
            surface="gesamteuropäischen",
            lemma="gesamteuropäisch",
            tag="ADJ",
            head=7,
            rel="amod",
            misc=True,
        ),
        DBToken(
            idx=7,
            surface="Geschichte",
            lemma="Geschichte",
            tag="NOUN",
            head=4,
            rel="nmod",
            misc=False,
        ),
    ]
    result = list(ex.extract_genitives(DependencyTree(sentence), 1))[0]
    assert (result.relation, result.head.surface, result.dep.surface) == (
        "GMOD",
        "Ergebnis",
        "Geschichte",
    )


def test_extract_comp():
    sentence = [
        DBToken(
            idx=1,
            surface="Diese",
            lemma="diese",
            tag="DET",
            head=2,
            rel="det",
            misc=True,
        ),
        DBToken(
            idx=2,
            surface="Bilder",
            lemma="Bild",
            tag="NOUN",
            head=3,
            rel="nsubj",
            misc=True,
        ),
        DBToken(
            idx=3,
            surface="wirkten",
            lemma="wirken",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        DBToken(
            idx=4,
            surface="wie",
            lemma="wie",
            tag="CCONJ",
            head=6,
            rel="case",
            misc=True,
        ),
        DBToken(
            idx=5, surface="ein", lemma="eine", tag="DET", head=6, rel="det", misc=True
        ),
        DBToken(
            idx=6,
            surface="Sog",
            lemma="Sog",
            tag="NOUN",
            head=3,
            rel="obl",
            misc=True,
        ),
    ]
    result = list(ex.extract_comparing_groups(sentence, 1))[0]
    assert (result.head.surface, result.relation, result.dep.surface) == (
        "wirkten",
        "KOM",
        "Sog",
    )


def test_extract_active_subjects():
    sentence = [
        DBToken(
            idx=1, surface="eine", lemma="eine", tag="DET", head=3, rel="det", misc=True
        ),
        DBToken(
            idx=2, surface="neue", lemma="neu", tag="ADJ", head=3, rel="amod", misc=True
        ),
        DBToken(
            idx=3,
            surface="Zeit",
            lemma="Zeit",
            tag="NOUN",
            head=4,
            rel="nsubj",
            misc=True,
        ),
        DBToken(
            idx=4,
            surface="begann",
            lemma="beginnen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
    ]
    result = list(ex.extract_active_subjects(DependencyTree(sentence), 1))[0]
    assert (result.relation, result.head.surface, result.dep.surface) == (
        "SUBJA",
        "begann",
        "Zeit",
    )


def test_all_extractions():
    sentences = [
        [
            DBToken(
                idx=1,
                surface="eine",
                lemma="eine",
                tag="DET",
                head=3,
                rel="det",
                misc=True,
            ),
            DBToken(
                idx=2,
                surface="ganze",
                lemma="ganz",
                tag="ADJ",
                head=3,
                rel="amod",
                misc=True,
            ),
            DBToken(
                idx=3,
                surface="Epoche",
                lemma="Epoche",
                tag="NOUN",
                head=0,
                rel="ROOT",
                misc=False,
            ),
        ],
        [
            DBToken(
                idx=1,
                surface="eine",
                lemma="eine",
                tag="DET",
                head=3,
                rel="det",
                misc=True,
            ),
            DBToken(
                idx=2,
                surface="neue",
                lemma="neu",
                tag="ADJ",
                head=3,
                rel="amod",
                misc=True,
            ),
            DBToken(
                idx=3,
                surface="Zeit",
                lemma="Zeit",
                tag="NOUN",
                head=4,
                rel="nsubj",
                misc=True,
            ),
            DBToken(
                idx=4,
                surface="begann",
                lemma="beginnen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
            ),
        ],
    ]
    result = list(ex.extract_matches(sentences))
    assert len(result) == 3
    assert [match.sid for match in result] == [1, 2, 2]
