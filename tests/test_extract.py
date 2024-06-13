import pytest

import wordprofile.extract as ex
from wordprofile.datatypes import DependencyTree, Match, WPToken


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
        "iobj",
        ("nmod", "case"),
        ("obl", "case"),
        ("obj", "case"),
        "nsubj:pass",
    ]
    assert result["advmod"] == {
        ("VERB", "ADV"): "ADV",
        ("ADJ", "ADV"): "ADV",
        ("VERB", "ADJ"): "ADV",
        ("ADJ", "ADJ"): "ADV",
    }
    assert result[("conj", "cc")] == {
        ("NOUN", "NOUN", "CCONJ"): "KON",
        ("VERB", "VERB", "CCONJ"): "KON",
        ("ADJ", "ADJ", "CCONJ"): "KON",
    }


def test_extract_matches_by_pattern(inverted_relations):
    sentence = [
        WPToken(
            idx=1, surface="eine", lemma="eine", tag="DET", head=3, rel="det", misc=True
        ),
        WPToken(
            idx=2,
            surface="ganze",
            lemma="ganz",
            tag="ADJ",
            head=3,
            rel="amod",
            misc=True,
        ),
        WPToken(
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
        WPToken(
            idx=1,
            surface="Haus",
            lemma="Haus",
            tag="NOUN",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="am",
            lemma="an",
            tag="ADP",
            head=3,
            rel="case",
            misc=True,
        ),
        WPToken(
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
        WPToken(
            idx=1,
            surface="Maßlosigkeit",
            lemma="Maßlosigkeit",
            tag="NOUN",
            head=4,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="war",
            lemma="sein",
            tag="AUX",
            head=4,
            rel="cop",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="die",
            lemma="d",
            tag="DET",
            head=4,
            rel="det",
            misc=True,
        ),
        WPToken(
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
        WPToken(
            idx=1,
            surface="Ohne",
            lemma="ohne",
            tag="ADP",
            head=3,
            rel="case",
            misc=True,
        ),
        WPToken(
            idx=2, surface="die", lemma="d", tag="DET", head=3, rel="det", misc=True
        ),
        WPToken(
            idx=3,
            surface="Entwicklung",
            lemma="Entwicklung",
            tag="NOUN",
            head=8,
            rel="obl",
            misc=True,
        ),
        WPToken(
            idx=4, surface="ist", lemma="sein", tag="AUX", head=8, rel="cop", misc=True
        ),
        WPToken(
            idx=5, surface="der", lemma="d", tag="DET", head=8, rel="det", misc=True
        ),
        WPToken(
            idx=6,
            surface="Tag",
            lemma="Tag",
            tag="NOUN",
            head=8,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=7,
            surface="nicht",
            lemma="nicht",
            tag="PART",
            head=8,
            rel="advmod",
            misc=True,
        ),
        WPToken(
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
        WPToken(
            idx=1,
            surface="Sie",
            lemma="sie",
            tag="PRON",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="befindet",
            lemma="befinden",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="ihn",
            lemma="PRON",
            tag="er",
            head=2,
            rel="obj",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="für",
            lemma="für",
            tag="ADP",
            head=5,
            rel="case",
            misc=True,
        ),
        WPToken(
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
        WPToken(
            idx=1, surface="Das", lemma="d", tag="PRON", head=4, rel="nsubj", misc=True
        ),
        WPToken(
            idx=2, surface="ist", lemma="sein", tag="AUX", head=4, rel="cop", misc=True
        ),
        WPToken(
            idx=3, surface="das", lemma="d", tag="DET", head=4, rel="det", misc=True
        ),
        WPToken(
            idx=4,
            surface="Ergebnis",
            lemma="Ergebnis",
            tag="NOUN",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="unserer",
            lemma="unsere",
            tag="DET",
            head=7,
            rel="det",
            morph={"Case": "Gen"},
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="gesamteuropäischen",
            lemma="gesamteuropäisch",
            tag="ADJ",
            head=7,
            rel="amod",
            misc=True,
        ),
        WPToken(
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
        WPToken(
            idx=1,
            surface="Diese",
            lemma="diese",
            tag="DET",
            head=2,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="Bilder",
            lemma="Bild",
            tag="NOUN",
            head=3,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="wirkten",
            lemma="wirken",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="wie",
            lemma="wie",
            tag="CCONJ",
            head=6,
            rel="case",
            misc=True,
        ),
        WPToken(
            idx=5, surface="ein", lemma="eine", tag="DET", head=6, rel="det", misc=True
        ),
        WPToken(
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
        WPToken(
            idx=1, surface="eine", lemma="eine", tag="DET", head=3, rel="det", misc=True
        ),
        WPToken(
            idx=2, surface="neue", lemma="neu", tag="ADJ", head=3, rel="amod", misc=True
        ),
        WPToken(
            idx=3,
            surface="Zeit",
            lemma="Zeit",
            tag="NOUN",
            head=4,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
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
            WPToken(
                idx=1,
                surface="eine",
                lemma="eine",
                tag="DET",
                head=3,
                rel="det",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="ganze",
                lemma="ganz",
                tag="ADJ",
                head=3,
                rel="amod",
                misc=True,
            ),
            WPToken(
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
            WPToken(
                idx=1,
                surface="eine",
                lemma="eine",
                tag="DET",
                head=3,
                rel="det",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="neue",
                lemma="neu",
                tag="ADJ",
                head=3,
                rel="amod",
                misc=True,
            ),
            WPToken(
                idx=3,
                surface="Zeit",
                lemma="Zeit",
                tag="NOUN",
                head=4,
                rel="nsubj",
                misc=True,
            ),
            WPToken(
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


def test_prepositional_object_not_matched_by_extract_object():
    sentence = [
        WPToken(
            idx=1,
            surface="Anwohner",
            lemma="Anwohner",
            tag="NOUN",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="protestieren",
            lemma="protestieren",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="heftig",
            lemma="heftig",
            tag="ADJ",
            head=2,
            rel="advmod",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="gegen",
            lemma="gegen",
            tag="ADP",
            head=6,
            rel="case",
            misc=True,
        ),
        WPToken(
            idx=5, surface="die", lemma="d", tag="DET", head=6, rel="det", misc=True
        ),
        WPToken(
            idx=6,
            surface="Autobahn",
            lemma="Autobahn",
            tag="NOUN",
            head=2,
            rel="obj",
            misc=False,
        ),
    ]
    result = list(ex.extract_objects(DependencyTree(sentence), 1))
    assert result == []


def test_prepositional_object_categorized_as_PP():
    inv_relations = ex.get_inverted_relation_patterns()
    sentence = [
        WPToken(
            idx=1,
            surface="Anwohner",
            lemma="Anwohner",
            tag="NOUN",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="protestieren",
            lemma="protestieren",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="heftig",
            lemma="heftig",
            tag="ADJ",
            head=2,
            rel="",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="gegen",
            lemma="gegen",
            tag="ADP",
            head=6,
            rel="case",
            misc=True,
        ),
        WPToken(
            idx=5, surface="die", lemma="d", tag="DET", head=6, rel="det", misc=True
        ),
        WPToken(
            idx=6,
            surface="Autobahn",
            lemma="Autobahn",
            tag="NOUN",
            head=2,
            rel="obj",
            misc=False,
        ),
    ]
    result = list(ex.extract_matches_by_pattern(inv_relations, sentence, 1))

    assert [
        (match.relation, match.head.surface, match.dep.surface, match.prep.surface)
        for match in result
    ] == [("PP", "protestieren", "Autobahn", "gegen")]


def test_prepositional_object_not_categorized_as_OBJ_by_pattern():
    inv_relations = ex.get_inverted_relation_patterns()
    sentence = [
        WPToken(
            idx=1,
            surface="Anwohner",
            lemma="Anwohner",
            tag="NOUN",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="protestieren",
            lemma="protestieren",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="heftig",
            lemma="heftig",
            tag="ADJ",
            head=2,
            rel="",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="gegen",
            lemma="gegen",
            tag="ADP",
            head=6,
            rel="case",
            misc=True,
        ),
        WPToken(
            idx=5, surface="die", lemma="d", tag="DET", head=6, rel="det", misc=True
        ),
        WPToken(
            idx=6,
            surface="Autobahn",
            lemma="Autobahn",
            tag="NOUN",
            head=2,
            rel="obj",
            misc=False,
        ),
    ]
    result = list(ex.extract_matches_by_pattern(inv_relations, sentence, 1))
    assert len(result) == 1


def test_double_object_without_prep_acc_and_dative():
    sentences = [
        [
            WPToken(
                idx=1,
                surface="Sie",
                lemma="sie",
                tag="PRON",
                head=2,
                rel="nsubj",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="empfinden",
                lemma="empfinden",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=3,
                surface="das",
                lemma="d",
                tag="DET",
                head=4,
                rel="det",
                morph={"Case": "Acc"},
                misc=True,
            ),
            WPToken(
                idx=4,
                surface="Aquarium",
                lemma="Aquarium",
                tag="NOUN",
                head=2,
                rel="obj",
                misc=True,
            ),
            WPToken(
                idx=5,
                surface="der",
                lemma="d",
                tag="DET",
                head=6,
                rel="det",
                morph={"Case": "Dat"},
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="Natur",
                lemma="Natur",
                tag="NOUN",
                head=2,
                rel="obj",
                misc=False,
            ),
            WPToken(
                idx=7,
                surface="nach",
                lemma="nach",
                tag="compound:prt",
                head=2,
                rel="",
                misc=False,
            ),
        ],
        [
            WPToken(
                idx=1,
                surface="Die",
                lemma="d",
                tag="DET",
                head=2,
                rel="det",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="Reporterin",
                lemma="Reporterin",
                tag="NOUN",
                head=3,
                rel="nsubj",
                misc=True,
            ),
            WPToken(
                idx=3,
                surface="überreichte",
                lemma="überreichen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=4,
                surface="König",
                lemma="König",
                tag="NOUN",
                head=3,
                rel="obl:arg",
                morph={"Case": "Dat"},
                misc=True,
            ),
            WPToken(
                idx=5,
                surface="Charles",
                lemma="Charles",
                tag="PROPN",
                head=4,
                rel="flat:name",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="das",
                lemma="d",
                tag="DET",
                head=7,
                rel="det",
                morph={"Case": "Acc"},
                misc=True,
            ),
            WPToken(
                idx=7,
                surface="Buch",
                lemma="Buch",
                tag="NOUN",
                head=3,
                rel="obj",
                misc=True,
            ),
        ],
        [
            WPToken(
                idx=1,
                surface="Die",
                lemma="d",
                tag="DET",
                head=2,
                rel="det",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="Zivilgesellschaft",
                lemma="Zivilgesellschaft",
                tag="NOUN",
                head=3,
                rel="nsubj",
                misc=True,
            ),
            WPToken(
                idx=3,
                surface="erstattet",
                lemma="erstatten",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=4,
                surface="dem",
                lemma="d",
                tag="DET",
                head=5,
                rel="det",
                morph={"Case": "Dat"},
                misc=True,
            ),
            WPToken(
                idx=7,
                surface="Staat",
                lemma="Staat",
                tag="NOUN",
                head=3,
                rel="obl:arg",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="Korruptionsgelder",
                lemma="Korruptionsgeld",
                tag="NOUN",
                head=3,
                rel="obj",
                misc=True,
            ),
            WPToken(
                idx=7,
                surface="zurück",
                lemma="zurücl",
                tag="ADP",
                head=3,
                rel="compound:prt",
                misc=True,
            ),
        ],
    ]
    for sent in sentences:
        result = list(ex.extract_objects(DependencyTree(sent), 1))
        assert len(result) == 2


def test_double_object_without_prep_two_accusative_objects():
    sentence = [
        WPToken(
            idx=1,
            surface="Die",
            lemma="d",
            tag="DET",
            head=2,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="Funksprüche",
            lemma="Funkspruch",
            tag="NOUN",
            head=5,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="seiner",
            lemma="seine",
            tag="DET",
            head=4,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="Kinder",
            lemma="Kind",
            tag="NOUN",
            head=2,
            rel="nmod",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="kosten",
            lemma="kosten",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="einen",
            lemma="eine",
            tag="DET",
            head=7,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=7,
            surface="Fluglotsen",
            lemma="Fluglotse",
            tag="NOUN",
            head=5,
            rel="obj",
            misc=True,
        ),
        WPToken(
            idx=8,
            surface="den",
            lemma="d",
            tag="DET",
            head=9,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=9,
            surface="Job",
            lemma="Job",
            tag="NOUN",
            head=5,
            rel="obj",
            misc=True,
        ),
    ]
    result = list(ex.extract_objects(DependencyTree(sentence), 1))
    assert len(result) == 2
    assert {match.relation for match in result} == {"OBJ"}


def test_double_object_without_prep_acc_and_genitive():
    sentence = [
        WPToken(
            idx=1,
            surface="Intel",
            lemma="Intel",
            tag="PRON",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="bezichtigt",
            lemma="bezichtigen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="auch",
            lemma="auch",
            tag="ADV",
            head=2,
            rel="advmod",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="deren",
            lemma="d",
            tag="PRON",
            head=5,
            rel="nmod",
            morph={"Case": "Acc"},
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="Kunden",
            lemma="Kunde",
            tag="NOUN",
            head=2,
            rel="obj",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="illegaler",
            lemma="illegal",
            tag="ADJ",
            head=7,
            rel="amod",
            morph={"Case": "Gen"},
            misc=True,
        ),
        WPToken(
            idx=7,
            surface="Handlungen",
            lemma="Handlung",
            tag="NOUN",
            head=2,
            rel="obj",
            morph={"Case": "Gen"},
            misc=True,
        ),
    ]
    result = list(ex.extract_objects(DependencyTree(sentence), 1))
    assert len(result) == 2
    assert {match.relation for match in result} == {"OBJ", "OBJO"}


def test_extract_iobj():
    inv_relations = ex.get_inverted_relation_patterns()
    sentence = [
        WPToken(
            idx=1,
            surface="Die",
            lemma="d",
            tag="DET",
            head=2,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="Funksprüche",
            lemma="Funkspruch",
            tag="NOUN",
            head=5,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="seiner",
            lemma="seine",
            tag="DET",
            head=4,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="Kinder",
            lemma="Kind",
            tag="NOUN",
            head=2,
            rel="nmod",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="kosten",
            lemma="kosten",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="einen",
            lemma="eine",
            tag="DET",
            head=7,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=7,
            surface="Fluglotsen",
            lemma="Fluglotse",
            tag="NOUN",
            head=5,
            rel="iobj",
            misc=True,
        ),
        WPToken(
            idx=8,
            surface="den",
            lemma="d",
            tag="DET",
            head=9,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=9,
            surface="Job",
            lemma="Job",
            tag="NOUN",
            head=5,
            rel="obj",
            misc=True,
        ),
    ]
    result = list(ex.extract_matches_by_pattern(inv_relations, sentence, 1))
    assert len(result) == 1
    assert ("OBJ", "kosten", "Fluglotse") in [
        (match.relation, match.head.lemma, match.dep.lemma) for match in result
    ]


@pytest.mark.xfail
def test_pp_match_only_extracted_once():
    sentences = [
        [
            WPToken(
                idx=1,
                surface="Sitze",
                lemma="Sitz",
                tag="NOUN",
                head=2,
                rel="nsubj",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="gehören",
                lemma="gehören",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=3,
                surface="zur",
                lemma="zu",
                tag="ADP",
                head=4,
                rel="case",
                misc=True,
            ),
            WPToken(
                idx=4,
                surface="Sonderausstatung",
                lemma="Sonderausstatung",
                tag="NOUN",
                head=2,
                rel="obj",
                misc=True,
            ),
        ],
        [
            WPToken(
                idx=1,
                surface="Der",
                lemma="d",
                tag="DET",
                head=2,
                rel="det",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="Flughafen",
                lemma="Flughafen",
                tag="NOUN",
                head=3,
                rel="nsubj",
                misc=True,
            ),
            WPToken(
                idx=3,
                surface="schließt",
                lemma="schließen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=4,
                surface="für",
                lemma="für",
                tag="ADP",
                head=5,
                rel="case",
                misc=True,
            ),
            WPToken(
                idx=5,
                surface="Passagierverkehr",
                lemma="Passagierverkehr",
                tag="NOUN",
                head=3,
                rel="obl",
                misc=True,
            ),
        ],
    ]
    for sentence in sentences:
        result = list(ex.extract_matches([sentence]))
        assert len(result) == 2
        assert "PP" in [match.relation for match in result]


def test_pred_match_only_extracted_once():
    sentence = [
        WPToken(
            idx=1,
            surface="Sie",
            lemma="sie",
            tag="PRON",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="bezeichnet",
            lemma="bezeichnen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="Berichte",
            lemma="Bericht",
            tag="NOUN",
            head=2,
            rel="obj",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="als",
            lemma="als",
            tag="CCONJ",
            head=5,
            rel="case",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="Horrormeldungen",
            lemma="Horrormeldung",
            tag="NOUN",
            head=2,
            rel="obl",
            misc=True,
        ),
    ]
    result = list(ex.extract_matches([sentence]))
    assert "PRED" in [match.relation for match in result]
    assert len(result) == 2


def test_adverbial_adjective_with_verb_extracted():
    adv_rules = ex.get_inverted_relation_patterns()["advmod"]
    sentence = [
        WPToken(
            idx=1,
            surface="indem",
            lemma="indem",
            tag="SCONJ",
            head=6,
            rel="mark",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="sie",
            lemma="sie",
            tag="PRON",
            head=6,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="ihnen",
            lemma="ihnen",
            tag="PRON",
            head=6,
            rel="obl:arg",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="pauschal",
            lemma="pauschal",
            tag="ADJ",
            head=6,
            rel="advmod",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="Revanchismus",
            lemma="Revanchismus",
            tag="NOUN",
            head=6,
            rel="obj",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="unterstellten",
            lemma="unterstellen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
    ]
    result = list(ex.extract_matches_by_pattern({"advmod": adv_rules}, sentence, 1))
    assert len(result) == 1
    assert [("unterstellen", "pauschal")] == [
        (match.head.lemma, match.dep.lemma) for match in result
    ]


def test_adverbial_adjective_with_adjective_extracted():
    adv_rules = ex.get_inverted_relation_patterns()["advmod"]
    sentence = [
        WPToken(
            idx=1,
            surface="davon",
            lemma="davon",
            tag="ADV",
            head=2,
            rel="advmod",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="nutzt",
            lemma="nutzen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="durchschnittlich",
            lemma="durchschnittlich",
            tag="ADJ",
            head=4,
            rel="advmod",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="knapp",
            lemma="knapp",
            tag="ADJ",
            head=6,
            rel="advmod",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="die",
            lemma="d",
            tag="DET",
            head=6,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="Hälfte",
            lemma="Hälfte",
            tag="NOUN",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=7,
            surface="Internet",
            lemma="Internet",
            tag="NOUN",
            head=2,
            rel="obj",
            misc=True,
        ),
    ]
    result = list(ex.extract_matches_by_pattern({"advmod": adv_rules}, sentence, 1))
    assert len(result) == 2
    assert ("knapp", "durchschnittlich") in [
        (match.head.lemma, match.dep.lemma) for match in result
    ]


def test_extract_matches_by_pattern_with_collapsed_phrasal_verb_adv():
    sentence = [
        WPToken(
            idx=1,
            surface="Der",
            lemma="d",
            tag="DET",
            head=2,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="Test",
            lemma="Test",
            tag="NOUN",
            head=3,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="schlug",
            lemma="fehlschlagen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
            prt_pos=5,
        ),
        WPToken(
            idx=4,
            surface="kläglich",
            lemma="kläglich",
            tag="ADJ",
            head=3,
            rel="advmod",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="fehl",
            lemma="fehl",
            tag="ADP",
            head=3,
            rel="compound:prt",
            misc=True,
        ),
    ]
    inv_rel = {"advmod": {("VERB", "ADJ"): "ADV"}}
    result = list(ex.extract_matches_by_pattern(inv_rel, sentence, 1))
    assert result == [
        Match(
            WPToken(
                idx=3,
                surface="schlug",
                lemma="fehlschlagen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
                prt_pos=5,
            ),
            WPToken(
                idx=4,
                surface="kläglich",
                lemma="kläglich",
                tag="ADJ",
                head=3,
                rel="advmod",
                misc=True,
            ),
            None,
            "ADV",
            1,
        )
    ]


def test_extract_matches_by_pattern_with_collapsed_phrasal_verb_kon():
    inv_rel = {("conj", "cc"): {("VERB", "VERB", "CCONJ"): "KON"}}
    sentence = [
        WPToken(
            idx=1,
            surface="Der",
            lemma="d",
            tag="DET",
            head=2,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="Sprecher",
            lemma="Sprecher",
            tag="Noun",
            head=3,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="bezeichnet",
            lemma="bezeichnen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="dies",
            lemma="dieser",
            tag="DET",
            head=3,
            rel="obj",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="als",
            lemma="als",
            tag="CCONJ",
            head=6,
            rel="case",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="Spekulation",
            lemma="Spekulation",
            tag="NOUN",
            head=3,
            rel="obl",
            misc=True,
        ),
        WPToken(
            idx=7,
            surface="und",
            lemma="und",
            tag="CCONJ",
            head=8,
            rel="cc",
            misc=True,
        ),
        WPToken(
            idx=8,
            surface="lehnt",
            lemma="ablehnen",
            tag="VERB",
            head=3,
            rel="conj",
            misc=True,
            prt_pos=11,
        ),
        WPToken(
            idx=9,
            surface="eine",
            lemma="ein",
            tag="DET",
            head=10,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=10,
            surface="Stellungnahme",
            lemma="Stellungnahme",
            tag="NOUN",
            head=8,
            rel="obj",
            misc=True,
        ),
        WPToken(
            idx=11,
            surface="ab",
            lemma="ab",
            tag="ADP",
            head=8,
            rel="compound:prt",
            misc=True,
        ),
    ]
    result = list(ex.extract_matches_by_pattern(inv_rel, sentence, 1))
    assert result == [
        Match(
            WPToken(
                idx=3,
                surface="bezeichnet",
                lemma="bezeichnen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=8,
                surface="lehnt",
                lemma="ablehnen",
                tag="VERB",
                head=3,
                rel="conj",
                misc=True,
                prt_pos=11,
            ),
            None,
            "KON",
            1,
        )
    ]


def test_extract_matches_by_pattern_kon_with_two_phrasal_verbs():
    inv_rel = {("conj", "cc"): {("VERB", "VERB", "CCONJ"): "KON"}}
    sentence = [
        WPToken(
            idx=1,
            surface="Sie",
            lemma="sie",
            tag="PRON",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="steht",
            lemma="aufstehen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
            prt_pos=3,
        ),
        WPToken(
            idx=3,
            surface="auf",
            lemma="auf",
            tag="ADP",
            head=2,
            rel="compound:prt",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="und",
            lemma="und",
            tag="CCONJ",
            head=5,
            rel="cc",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="schläft",
            lemma="einschlafen",
            tag="VERB",
            head=2,
            rel="conj",
            misc=True,
            prt_pos=6,
        ),
        WPToken(
            idx=6,
            surface="ein",
            lemma="ein",
            tag="ADP",
            head=4,
            rel="compound:prt",
            misc=True,
        ),
    ]
    result = list(ex.extract_matches_by_pattern(inv_rel, sentence, 1))
    assert result == [
        Match(
            WPToken(
                idx=2,
                surface="steht",
                lemma="aufstehen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
                prt_pos=3,
            ),
            WPToken(
                idx=5,
                surface="schläft",
                lemma="einschlafen",
                tag="VERB",
                head=2,
                rel="conj",
                misc=True,
                prt_pos=6,
            ),
            None,
            "KON",
            1,
        )
    ]


def test_extract_matches_by_pattern_with_collapsed_phrasal_verb_obj():
    inv_rel = {"obj": {("VERB", "NOUN"): "OBJ"}}
    sentence = [
        WPToken(
            idx=1,
            surface="Der",
            lemma="d",
            tag="DET",
            head=2,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="Sprecher",
            lemma="Sprecher",
            tag="Noun",
            head=3,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="lehnt",
            lemma="ablehnen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
            prt_pos=6,
        ),
        WPToken(
            idx=4,
            surface="eine",
            lemma="ein",
            tag="DET",
            head=5,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="Stellungnahme",
            lemma="Stellungnahme",
            tag="NOUN",
            head=3,
            rel="obj",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="ab",
            lemma="ab",
            tag="ADP",
            head=3,
            rel="compound:prt",
            misc=True,
        ),
    ]
    result = list(ex.extract_matches_by_pattern(inv_rel, sentence, 1))
    assert result == [
        Match(
            WPToken(
                idx=3,
                surface="lehnt",
                lemma="ablehnen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
                prt_pos=6,
            ),
            WPToken(
                idx=5,
                surface="Stellungnahme",
                lemma="Stellungnahme",
                tag="NOUN",
                head=3,
                rel="obj",
                misc=True,
            ),
            None,
            "OBJ",
            1,
        )
    ]


def test_extract_matches_by_pattern_with_collapsed_phrasal_verb_pp():
    inv_rel = {("obl", "case"): {("VERB", "NOUN", "ADP"): "PP"}}
    sentence = [
        WPToken(
            idx=1,
            surface="Frankreichs",
            lemma="Frankreich",
            tag="PROPN",
            head=2,
            rel="nmod",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="Innenminister",
            lemma="Innenminister",
            tag="NOUN",
            head=3,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="lehnt",
            lemma="ablehnen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
            prt_pos=11,
        ),
        WPToken(
            idx=4,
            surface="eine",
            lemma="ein",
            tag="DET",
            head=7,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="grenzüberschreitend",
            lemma="grenzüberschreitend",
            tag="ADJ",
            head=6,
            rel="advmod",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="tätige",
            lemma="tätig",
            tag="ADJ",
            head=7,
            rel="amod",
            misc=True,
        ),
        WPToken(
            idx=7,
            surface="Cyber-Polizei",
            lemma="Cyper-Polizei",
            tag="NOUN",
            head=3,
            rel="obj",
            misc=True,
        ),
        WPToken(
            idx=8,
            surface="für",
            lemma="für",
            tag="ADP",
            head=10,
            rel="case",
            misc=True,
        ),
        WPToken(
            idx=9,
            surface="sein",
            lemma="sein",
            tag="DET",
            head=10,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=10,
            surface="Land",
            lemma="Land",
            tag="NOUN",
            head=3,
            rel="obl",
            misc=True,
        ),
        WPToken(
            idx=11,
            surface="ab",
            lemma="ab",
            tag="ADP",
            head=3,
            rel="compound:prt",
            misc=True,
        ),
    ]
    result = list(ex.extract_matches_by_pattern(inv_rel, sentence, 1))
    assert result == [
        Match(
            WPToken(
                idx=3,
                surface="lehnt",
                lemma="ablehnen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
                prt_pos=11,
            ),
            WPToken(
                idx=10,
                surface="Land",
                lemma="Land",
                tag="NOUN",
                head=3,
                rel="obl",
                misc=True,
            ),
            WPToken(
                idx=8,
                surface="für",
                lemma="für",
                tag="ADP",
                head=10,
                rel="case",
                misc=True,
            ),
            "PP",
            1,
        )
    ]


def test_extract_predicatives_verb_with_collapsed_phrasal_verb():
    sentence = [
        WPToken(
            idx=1,
            surface="Eine",
            lemma="ein",
            tag="DET",
            head=2,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="Wiedertaufe",
            lemma="Wiedertaufe",
            tag="NOUN",
            head=3,
            rel="obj",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="lehnt",
            lemma="ablehnen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
            prt_pos=7,
        ),
        WPToken(
            idx=4,
            surface="er",
            lemma="er",
            tag="PRON",
            head=0,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="als",
            lemma="als",
            tag="CCONJ",
            head=6,
            rel="case",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="Irrglauben",
            lemma="Irrglaube",
            tag="NOUN",
            head=3,
            rel="obl",
            misc=True,
        ),
        WPToken(
            idx=7,
            surface="ab",
            lemma="ab",
            tag="ADP",
            head=3,
            rel="compound:prt",
            misc=True,
        ),
    ]
    result = list(ex.extract_predicatives(DependencyTree(sentence), 1))
    assert result == [
        Match(
            WPToken(
                idx=3,
                surface="lehnt",
                lemma="ablehnen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
                prt_pos=7,
            ),
            WPToken(
                idx=6,
                surface="Irrglauben",
                lemma="Irrglaube",
                tag="NOUN",
                head=3,
                rel="obl",
                misc=True,
            ),
            None,
            "PRED",
            1,
        )
    ]


def test_extract_active_subjects_with_collapsed_phrasal_verb():
    sentence = [
        WPToken(
            idx=1,
            surface="Der",
            lemma="d",
            tag="DET",
            head=2,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="Sprecher",
            lemma="Sprecher",
            tag="NOUN",
            head=3,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="lehnt",
            lemma="ablehnen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
            prt_pos=6,
        ),
        WPToken(
            idx=4,
            surface="eine",
            lemma="ein",
            tag="DET",
            head=5,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="Stellungnahme",
            lemma="Stellungnahme",
            tag="NOUN",
            head=3,
            rel="obj",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="ab",
            lemma="ab",
            tag="ADP",
            head=3,
            rel="compound:prt",
            misc=True,
        ),
    ]
    result = list(ex.extract_active_subjects(DependencyTree(sentence), 1))
    assert result == [
        Match(
            WPToken(
                idx=3,
                surface="lehnt",
                lemma="ablehnen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
                prt_pos=6,
            ),
            WPToken(
                idx=2,
                surface="Sprecher",
                lemma="Sprecher",
                tag="NOUN",
                head=3,
                rel="nsubj",
                misc=True,
            ),
            None,
            "SUBJA",
            1,
        )
    ]


def test_genitive_with_preposition_not_extracted_as_GMOD():
    sentence = [
        WPToken(
            idx=1,
            surface="das",
            lemma="d",
            tag="DET",
            head=2,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="Jahrhunderhochwasser",
            lemma="Jahrhunderhochwasser",
            tag="NOUN",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="entlang",
            lemma="entlang",
            tag="ADP",
            head=5,
            rel="case",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="der",
            lemma="d",
            tag="DET",
            head=5,
            rel="det",
            morph={"Case": "Gen"},
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="Elbe",
            lemma="Elbe",
            tag="NOUN",
            head=2,
            rel="nmod",
            misc=True,
        ),
    ]
    result = list(ex.extract_genitives(DependencyTree(sentence), 1))
    assert len(result) == 0


def test_extract_genitives_with_morphological_features():
    sentences = [
        [
            WPToken(
                idx=1,
                surface="Fall",
                lemma="Fall",
                tag="NOUN",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="der",
                lemma="d",
                tag="DET",
                head=4,
                rel="det",
                morph={"Case": "Gen"},
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="Berliner",
                lemma="Berliner",
                tag="ADJ",
                head=4,
                rel="amod",
                misc=True,
            ),
            WPToken(
                idx=4,
                surface="Mauer",
                lemma="Mauer",
                tag="NOUN",
                head=1,
                rel="nmod",
                misc=True,
            ),
        ],
        [
            WPToken(
                idx=1,
                surface="die",
                lemma="d",
                tag="DET",
                head=2,
                rel="det",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="Anteilseigner",
                lemma="Anteilseigner",
                tag="NOUN",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=3,
                surface="von",
                lemma="von",
                tag="ADP",
                head=6,
                rel="case",
                misc=True,
            ),
            WPToken(
                idx=4,
                surface="Europas",
                lemma="Europa",
                tag="NOUN",
                head=6,
                rel="nmod",
                morph={"Case": "Gen"},
                misc=True,
            ),
            WPToken(
                idx=5,
                surface="größtem",
                lemma="groß",
                tag="ADJ",
                head=6,
                rel="amod",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="Werftenverband",
                lemma="Werftenverband",
                tag="NOUN",
                head=2,
                rel="nmod",
                misc=True,
            ),
        ],
    ]
    for sentence in sentences:
        result = list(ex.extract_genitives(DependencyTree(sentence), 1))
        assert len(result) == 1


def test_extraction_of_genitive_object():
    sentence = [
        WPToken(
            idx=1,
            surface="der",
            lemma="d",
            tag="DET",
            head=2,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="Prozessor",
            lemma="Prozessor",
            tag="NOUN",
            head=3,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="erfreute",
            lemma="erfreuen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="sich",
            lemma="sich",
            tag="PRON",
            head=3,
            rel="expl:pv",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="eines",
            lemma="ein",
            tag="DET",
            head=7,
            rel="det",
            morph={"Case": "Gen"},
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="mächtigen",
            lemma="mächtig",
            tag="ADJ",
            head=7,
            rel="amod",
            morph={"Case": "Gen"},
            misc=True,
        ),
        WPToken(
            idx=7,
            surface="Grafikpartners",
            lemma="Grafikpartner",
            tag="NOUN",
            head=3,
            rel="obj",
            morph={"Case": "Gen"},
            misc=True,
        ),
    ]
    result = list(ex.extract_objects(DependencyTree(sentence), 1))
    assert len(result) == 1
    assert result[0].relation == "OBJO"


def test_extraction_of_dative_objects():
    sentence = [
        WPToken(
            idx=1,
            surface="Altlasten",
            lemma="Altlast",
            tag="NOUN",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="machen",
            lemma="machen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="der",
            lemma="d",
            tag="DET",
            head=4,
            rel="det",
            morph={"Case": "Dat"},
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="Firma",
            lemma="Firma",
            tag="NOUN",
            head=2,
            rel="obj",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="zu",
            lemma="zu",
            tag="PART",
            head=6,
            rel="mark",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="schaffen",
            lemma="schaffen",
            tag="VERB",
            head=2,
            rel="xcomp",
            misc=True,
        ),
    ]
    result = list(ex.extract_objects(DependencyTree(sentence), 1))
    assert len(result) == 1
    assert result[0].relation == "OBJO"


def test_accusative_object_without_case_marking():
    sentence = [
        WPToken(
            idx=1,
            surface="der",
            lemma="d",
            tag="DET",
            head=2,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="Verein",
            lemma="Verein",
            tag="NOUN",
            head=3,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="bietet",
            lemma="bieten",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="dem",
            lemma="d",
            tag="DET",
            head=5,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="Druck",
            lemma="Druck",
            tag="NOUN",
            head=3,
            rel="",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="Paroli",
            lemma="Paroli",
            tag="NOUN",
            head=3,
            rel="obj",
            misc=True,
        ),
    ]
    result = list(ex.extract_objects(DependencyTree(sentence), 1))
    assert len(result) == 1
    assert result[0].relation == "OBJ"


def test_verb_modifying_obl_not_extracted_as_object():
    sentence = [
        WPToken(
            idx=1,
            surface="Sie",
            lemma="sie",
            tag="PRON",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="arbeitet",
            lemma="arbeiten",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="drei",
            lemma="drei",
            tag="NUM",
            head=4,
            rel="nummod",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="Tage",
            lemma="Tag",
            tag="NOUN",
            head=2,
            rel="obl",
            misc=True,
        ),
    ]
    result = list(ex.extract_objects(DependencyTree(sentence), 1))
    assert len(result) == 0
