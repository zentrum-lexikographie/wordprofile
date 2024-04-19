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
