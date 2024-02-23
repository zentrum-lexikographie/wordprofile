import random

import pytest

import wordprofile.sentence_filter as sf
from wordprofile.datatypes import DBToken, Match


@pytest.fixture
def valid_sentences():
    return [
        [
            DBToken(
                idx=1,
                surface="Eine",
                lemma="eine",
                tag="DET",
                head=3,
                rel="det",
                misc=False,
            ),
            DBToken(
                idx=2,
                surface="neue",
                lemma="neu",
                tag="ADJ",
                head=3,
                rel="amod",
                misc=False,
            ),
            DBToken(
                idx=3,
                surface="Zeit",
                lemma="Zeit",
                tag="NOUN",
                head=4,
                rel="nsubj",
                misc=False,
            ),
            DBToken(
                idx=4,
                surface="begann",
                lemma="beginnen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=False,
            ),
        ],
        [
            DBToken(
                idx=1,
                surface="Eine",
                lemma="eine",
                tag="DET",
                head=3,
                rel="det",
                misc=False,
            ),
            DBToken(
                idx=2,
                surface="neue",
                lemma="neu",
                tag="ADJ",
                head=3,
                rel="amod",
                misc=False,
            ),
            DBToken(
                idx=3,
                surface="Zeit",
                lemma="Zeit",
                tag="NOUN",
                head=4,
                rel="nsubj",
                misc=False,
            ),
            DBToken(
                idx=4,
                surface="begann",
                lemma="beginnen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=False,
            ),
            DBToken(
                idx=5,
                surface=",",
                lemma=",",
                tag="PUNCT",
                head=1,
                rel="punct",
                misc=False,
            ),
        ],
        [
            DBToken(
                idx=1,
                surface="Ohne",
                lemma="ohne",
                tag="ADP",
                head=3,
                rel="case",
                misc=False,
            ),
            DBToken(
                idx=2,
                surface="den",
                lemma="d",
                tag="DET",
                head=3,
                rel="det",
                misc=False,
            ),
            DBToken(
                idx=3,
                surface="Helsinki-Prozess",
                lemma="Helsinki-Prozeß",
                tag="NOUN",
                head=8,
                rel="obl",
                misc=False,
            ),
            DBToken(
                idx=4,
                surface="hätte",
                lemma="haben",
                tag="AUX",
                head=8,
                rel="aux",
                misc=False,
            ),
            DBToken(
                idx=5,
                surface="es",
                lemma="es",
                tag="PRON",
                head=8,
                rel="nsubj",
                misc=False,
            ),
            DBToken(
                idx=6,
                surface="1989",
                lemma="1989",
                tag="NUM",
                head=8,
                rel="obl",
                misc=False,
            ),
            DBToken(
                idx=7,
                surface="nicht",
                lemma="nicht",
                tag="PART",
                head=8,
                rel="advmod",
                misc=False,
            ),
            DBToken(
                idx=8,
                surface="gegeben",
                lemma="geben",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=False,
            ),
            DBToken(
                idx=9,
                surface=".",
                lemma=".",
                tag="PUNCT",
                head=8,
                rel="punct",
                misc=False,
            ),
        ],
        [
            DBToken(
                idx=1,
                surface="A-Rosa",
                lemma="A-Rosa",
                tag="NOUN",
                head=0,
                rel="ROOT",
                misc=False,
            ),
            DBToken(
                idx=2,
                surface="mit",
                lemma="mit",
                tag="ADP",
                head=5,
                rel="case",
                misc=False,
            ),
            DBToken(
                idx=3,
                surface="zwei",
                lemma="zwei",
                tag="NUM",
                head=5,
                rel="nummod",
                misc=False,
            ),
            DBToken(
                idx=4,
                surface="neuen",
                lemma="neu",
                tag="ADJ",
                head=5,
                rel="amod",
                misc=False,
            ),
            DBToken(
                idx=5,
                surface="Schiffen",
                lemma="Schiff",
                tag="NOUN",
                head=1,
                rel="nmod",
                misc=False,
            ),
            DBToken(
                idx=6,
                surface="2024",
                lemma="2024",
                tag="NUM",
                head=5,
                rel="nmod",
                misc=False,
            ),
        ],
    ]


@pytest.fixture
def invalid_sentences():
    return [
        [
            DBToken(
                idx=1,
                surface="Exzellenzen",
                lemma="Exzellenz",
                tag="NOUN",
                head=0,
                rel="ROOT",
                misc=False,
            ),
            DBToken(
                idx=2,
                surface=",",
                lemma=",",
                tag="PUNCT",
                head=1,
                rel="punct",
                misc=False,
            ),
        ],
        [
            DBToken(
                idx=1,
                surface="Heppenheim",
                lemma="Heppenheim",
                tag="PROPN",
                head=0,
                rel="ROOT",
                misc=False,
            )
        ],
        [
            DBToken(
                idx=1, surface="<", lemma="<", tag="X", head=0, rel="ROOT", misc=True
            ),
            DBToken(
                idx=2,
                surface="bold>Serbien",
                lemma="Bold>serbien",
                tag="PROPN",
                head=1,
                rel="flat",
                misc=False,
            ),
            DBToken(
                idx=3,
                surface="-",
                lemma="-",
                tag="PUNCT",
                head=4,
                rel="punct",
                misc=False,
            ),
            DBToken(
                idx=4,
                surface="Kanada",
                lemma="Kanada",
                tag="PROPN",
                head=1,
                rel="appos",
                misc=True,
            ),
            DBToken(
                idx=5,
                surface="95:86USA",
                lemma="95:86usa",
                tag="PROPN",
                head=4,
                rel="flat:name",
                misc=False,
            ),
            DBToken(
                idx=6,
                surface="-",
                lemma="-",
                tag="PUNCT",
                head=7,
                rel="punct",
                misc=False,
            ),
            DBToken(
                idx=7,
                surface="Deutschland",
                lemma="Deutschland",
                tag="PROPN",
                head=4,
                rel="appos",
                misc=False,
            ),
            DBToken(
                idx=8,
                surface="111:113</bold",
                lemma="111:113</bold",
                tag="X",
                head=7,
                rel="appos",
                misc=False,
            ),
            DBToken(
                idx=9, surface=">", lemma=">", tag="X", head=7, rel="appos", misc=False
            ),
        ],
        [
            DBToken(
                idx=1,
                surface='"[',
                lemma='"[',
                tag="PUNCT",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            DBToken(
                idx=2,
                surface=".",
                lemma=".",
                tag="PUNCT",
                head=0,
                rel="ROOT",
                misc=False,
            ),
            DBToken(
                idx=3,
                surface=".",
                lemma=".",
                tag="PUNCT",
                head=2,
                rel="punct",
                misc=False,
            ),
            DBToken(
                idx=4,
                surface=".",
                lemma=".",
                tag="PUNCT",
                head=2,
                rel="punct",
                misc=False,
            ),
            DBToken(
                idx=5, surface="]", lemma="]", tag="X", head=0, rel="ROOT", misc=False
            ),
        ],
        [
            DBToken(
                idx=1, surface="<", lemma="<", tag="X", head=0, rel="ROOT", misc=True
            ),
            DBToken(
                idx=2,
                surface="bold>",
                lemma="bold>",
                tag="X",
                head=1,
                rel="flat",
                misc=True,
            ),
            DBToken(
                idx=3,
                surface="UCI",
                lemma="uci",
                tag="PROPN",
                head=2,
                rel="flat:name",
                misc=False,
            ),
            DBToken(
                idx=4,
                surface="WorldTour",
                lemma="worldtour",
                tag="PROPN",
                head=2,
                rel="flat:name",
                misc=True,
            ),
            DBToken(
                idx=5,
                surface=",",
                lemma=",",
                tag="PUNCT",
                head=6,
                rel="punct",
                misc=False,
            ),
        ],
        [
            DBToken(
                idx=1, surface="<", lemma="<", tag="X", head=0, rel="ROOT", misc=True
            ),
            DBToken(
                idx=2,
                surface="bold>Tischler*in",
                lemma="Bold>tischler*in",
                tag="X",
                head=1,
                rel="flat",
                misc=False,
            ),
            DBToken(
                idx=3,
                surface="(",
                lemma="(",
                tag="PUNCT",
                head=4,
                rel="punct",
                misc=True,
            ),
            DBToken(
                idx=4,
                surface="Berufsschule",
                lemma="Berufsschule",
                tag="NOUN",
                head=2,
                rel="appos",
                misc=False,
            ),
            DBToken(
                idx=5,
                surface="Melle",
                lemma="Melle",
                tag="PROPN",
                head=4,
                rel="flat:name",
                misc=True,
            ),
            DBToken(
                idx=6,
                surface=")",
                lemma=")",
                tag="PUNCT",
                head=4,
                rel="punct",
                misc=True,
            ),
            DBToken(
                idx=7,
                surface=":</bold",
                lemma=":</bold",
                tag="PUNCT",
                head=1,
                rel="punct",
                misc=False,
            ),
            DBToken(
                idx=8, surface=">", lemma=">", tag="X", head=0, rel="ROOT", misc=False
            ),
        ],
    ]


def test_valid_token_identified():
    tokens = [
        DBToken(
            idx=1,
            surface="Eine",
            lemma="eine",
            tag="DET",
            head=3,
            rel="det",
            misc=False,
        ),
        DBToken(
            idx=2,
            surface="neue",
            lemma="neu",
            tag="ADJ",
            head=3,
            rel="amod",
            misc=False,
        ),
        DBToken(
            idx=3,
            surface="Zeit",
            lemma="Zeit",
            tag="NOUN",
            head=4,
            rel="nsubj",
            misc=False,
        ),
        DBToken(
            idx=4,
            surface="begann",
            lemma="beginnen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=False,
        ),
        DBToken(
            idx=1,
            surface="Ohne",
            lemma="ohne",
            tag="ADP",
            head=3,
            rel="case",
            misc=False,
        ),
        DBToken(
            idx=4,
            surface="WorldTour",
            lemma="worldtour",
            tag="PROPN",
            head=2,
            rel="flat:name",
            misc=True,
        ),
        DBToken(
            idx=1,
            surface="A-Rosa",
            lemma="A-Rosa",
            tag="NOUN",
            head=0,
            rel="ROOT",
            misc=False,
        ),
        DBToken(
            idx=5,
            surface="es",
            lemma="es",
            tag="PRON",
            head=8,
            rel="nsubj",
            misc=False,
        ),
        DBToken(
            idx=8,
            surface="España",
            lemma="España",
            tag="PROPN",
            head=6,
            rel="flat:name",
            misc=True,
        ),
        DBToken(
            idx=2,
            surface="den",
            lemma="d",
            tag="DET",
            head=3,
            rel="det",
            misc=False,
        ),
        DBToken(
            idx=3,
            surface="Helsinki-Prozess",
            lemma="Helsinki-Prozeß",
            tag="NOUN",
            head=8,
            rel="obl",
            misc=False,
        ),
        DBToken(
            idx=15,
            surface="Súria",
            lemma="Súria",
            tag="NOUN",
            head=2,
            rel="appos",
            misc=False,
        ),
        DBToken(
            idx=10,
            surface="Männer",
            lemma="Mann",
            tag="NOUN",
            head=6,
            rel="appos",
            misc=True,
        ),
    ]
    for token in tokens:
        assert sf.is_valid_token(token) is True


def test_invalid_token_rejected():
    tokens = [
        DBToken(
            idx=6,
            surface="2024",
            lemma="2024",
            tag="NUM",
            head=5,
            rel="nmod",
            misc=False,
        ),
        DBToken(
            idx=9,
            surface=".",
            lemma=".",
            tag="PUNCT",
            head=8,
            rel="punct",
            misc=False,
        ),
        DBToken(
            idx=2,
            surface=",",
            lemma=",",
            tag="PUNCT",
            head=1,
            rel="punct",
            misc=False,
        ),
        DBToken(
            idx=6,
            surface=")",
            lemma=")",
            tag="PUNCT",
            head=4,
            rel="punct",
            misc=True,
        ),
        DBToken(
            idx=7,
            surface=":</bold",
            lemma=":</bold",
            tag="PUNCT",
            head=1,
            rel="punct",
            misc=False,
        ),
        DBToken(idx=8, surface=">", lemma=">", tag="X", head=0, rel="ROOT", misc=False),
        DBToken(
            idx=2,
            surface="bold>Tischler*in",
            lemma="Bold>tischler*in",
            tag="X",
            head=1,
            rel="flat",
            misc=False,
        ),
        DBToken(
            idx=19,
            surface="158,50",
            lemma="158,50",
            tag="NUM",
            head=20,
            rel="nummod",
            misc=False,
        ),
        DBToken(
            idx=16,
            surface="-",
            lemma="-",
            tag="PUNCT",
            head=17,
            rel="punct",
            misc=False,
        ),
        DBToken(
            idx=12,
            surface="3.",
            lemma="3.",
            tag="ADJ",
            head=13,
            rel="amod",
            misc=False,
        ),
        DBToken(
            idx=5,
            surface="95:86USA",
            lemma="95:86usa",
            tag="PROPN",
            head=4,
            rel="flat:name",
            misc=False,
        ),
        DBToken(
            idx=5,
            surface="USA95:86",
            lemma="usa95:86",
            tag="PROPN",
            head=4,
            rel="flat:name",
            misc=False,
        ),
        DBToken(
            idx=3,
            surface="#Helsinki-Prozess",
            lemma="#Helsinki-Prozeß",
            tag="NOUN",
            head=8,
            rel="obl",
            misc=False,
        ),
        DBToken(
            idx=3,
            surface="Hels1nk1",
            lemma="Hels1nk1",
            tag="NOUN",
            head=8,
            rel="obl",
            misc=False,
        ),
        DBToken(
            idx=3,
            surface="-Prozess",
            lemma="-Prozeß",
            tag="NOUN",
            head=8,
            rel="obl",
            misc=False,
        ),
    ]
    for token in tokens:
        assert sf.is_valid_token(token) is False


def test_too_short_sentences_filtered():
    token = DBToken(
        idx=0,
        surface="Schiffen",
        lemma="Schiff",
        tag="NOUN",
        head=1,
        rel="nmod",
        misc=False,
    )
    for i in range(3):
        assert sf.sent_filter_length([token] * i) is False
    assert sf.sent_filter_length([token] * 3)


def test_too_long_sentences_filtered():
    token = DBToken(
        idx=0,
        surface="Schiffen",
        lemma="Schiff",
        tag="NOUN",
        head=1,
        rel="nmod",
        misc=False,
    )
    assert sf.sent_filter_length([token] * 100)
    assert sf.sent_filter_length([token] * 101) is False


def test_sentence_filtered_according_to_last_token():
    noun = DBToken(
        idx=0,
        surface="Zeit",
        lemma="Zeit",
        tag="NOUN",
        head=4,
        rel="nsubj",
        misc=False,
    )
    colon = DBToken(
        idx=1, surface=":", lemma=":", tag="PUNCT", head=1, rel="punct", misc=False
    )
    comma = DBToken(
        idx=1, surface=",", lemma=",", tag="PUNCT", head=1, rel="punct", misc=False
    )
    assert sf.sent_filter_endings([noun, colon]) is False
    assert sf.sent_filter_endings([noun, comma]) is False
    assert sf.sent_filter_endings([noun] * 4 + [colon])
    assert sf.sent_filter_endings([noun] * 4 + [comma])
    assert sf.sent_filter_endings([noun])


def test_sentence_must_contain_one_desired_tag():
    necessary_tags = ["NOUN", "VERB", "AUX"]
    other_tags = ["X", "PUNCT", "ADV", "ADJ", "PROPN", "DET", "FM", "ADP", "PRON"]
    x_tag = DBToken(
        idx=0,
        surface="",
        lemma="",
        tag=random.choice(other_tags),
        head=1,
        rel="det",
        misc=True,
    )
    token_with_necessary_tag = DBToken(
        idx=1,
        surface="",
        lemma="",
        tag=random.choice(necessary_tags),
        head=2,
        rel="",
        misc=False,
    )
    assert sf.sent_filter_tags([x_tag]) is False
    assert sf.sent_filter_tags([token_with_necessary_tag, x_tag])


def test_sentence_contains_maximal_9_unwanted_tags():
    invalid_token = [
        DBToken(idx=1, surface="<", lemma="<", tag="SYM", head=0, rel="", misc=True),
        DBToken(
            idx=2,
            surface="bold>27.",
            lemma="Bold>27.",
            tag="X",
            head=1,
            rel="flat:name",
            misc=False,
        ),
    ]
    valid_tags = [
        "NOUN",
        "VERB",
        "AUX",
        "PUNCT",
        "ADV",
        "ADJ",
        "PROPN",
        "DET",
        "FM",
        "ADP",
        "PRON",
    ]
    valid_token = DBToken(
        idx=1,
        surface="",
        lemma="",
        tag=random.choice(valid_tags),
        head=0,
        rel="",
        misc=True,
    )

    assert sf.sent_filter_invalid_tags([valid_token for _ in range(10)])
    assert sf.sent_filter_invalid_tags([invalid_token[0] for _ in range(10)]) is False
    assert sf.sent_filter_invalid_tags(invalid_token + [valid_token for _ in range(15)])
    assert sf.sent_filter_invalid_tags(invalid_token + [valid_token]) is False
    assert sf.sent_filter_invalid_tags(
        invalid_token[:1] + [valid_token for _ in range(3)]
    )
    assert sf.sent_filter_invalid_tags(
        invalid_token * 4 + [valid_token for _ in range(22)]
    )


def test_invalid_sentences_filtered(invalid_sentences):
    for sent in invalid_sentences:
        assert sf.sentence_is_valid(sent) is False


def test_valid_sentences_not_filtered(valid_sentences):
    for sent in valid_sentences:
        assert sf.sentence_is_valid(sent)


def test_valid_match():
    tok1 = DBToken(
        idx=1, surface="Test", lemma="<", tag="Noun", head=0, rel="", misc=True
    )
    tok2 = DBToken(idx=2, surface="<", lemma="<", tag="SYM", head=0, rel="", misc=True)
    assert sf.valid_match(Match(head=tok1, dep=tok1, prep=None, relation="", sid=0))
    assert (
        sf.valid_match(Match(head=tok1, dep=tok2, prep=None, relation="", sid=0))
        is False
    )
    assert (
        sf.valid_match(Match(head=tok2, dep=tok2, prep=None, relation="", sid=0))
        is False
    )


def test_extraction_of_matches_from_doc(invalid_sentences, valid_sentences):
    assert list(sf.extract_matches_from_doc(invalid_sentences[:1])) == []
    assert list(sf.extract_matches_from_doc(invalid_sentences[2:3])) == []
    assert len(list(sf.extract_matches_from_doc(valid_sentences[:1]))) == 2


def test_lemma_repair_load():
    repair_dict = sf.load_lemma_repair_files()
    assert len(repair_dict) == 3
    assert repair_dict["ADJ"]["mißinformiert"] == "missinformiert"


def test_replace_lemma():
    assert sf.repair_lemma("Tag", "NOUN") == "Tag"
    assert sf.repair_lemma("tätig", "VERB") == "tätigen"
    assert sf.repair_lemma("Test", "X") == "Test"


def test_remove_invalid_chars():
    assert sf.remove_invalid_chars("path\\to") == "pathto"
    assert sf.remove_invalid_chars("abc\udeed") == "abc"


def test_case_normalisation_regex_invalid_lemmata_matched():
    invalid_lemmata = [
        "Kopf-an-kopf-rennen",
        "E-mail",
        "Social-media-expertin",
        "US-dollar",
        "Bertha-von-suttner-straße"
        # theoretisch nicht falsch s. https://git.zdl.org/zdl/wordprofile/issues/44
        "Prêt-à-porter",
        "CDU-regiert",
        "Coming-out",
    ]
    for lemma in invalid_lemmata:
        assert sf.RE_GK_NORM_ERROR.match(lemma) is not None


def test_case_normalisation_regex_valid_lemmata_not_matched():
    valid_lemmata = [
        "Kopf-an-Kopf-Rennen",
        "Tour-de-France",
        "US-Amerikanerin",
        "Berlin",
        "Bertha-von-Suttner-Straße",
        "Champs-Élysées",
    ]
    for lemma in valid_lemmata:
        assert sf.RE_GK_NORM_ERROR.match(lemma) is None
