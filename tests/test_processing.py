from conllu.models import TokenList, Token

import wordprofile.wpse.processing as pro
from wordprofile.datatypes import DBToken


def test_sentence_conversion_to_dbtoken():
    token_list = TokenList(
        [
            Token(
                id=1,
                form="Test",
                lemma="Test",
                upos="NOUN",
                xpos="",
                feats={},
                head="",
                deprel="",
                deps=None,
                misc={"SpaceAfter": "No"},
            ),
        ]
    )
    assert pro.convert_sentence(token_list) == [
        DBToken(
            idx=1, surface="Test", lemma="Test", tag="NOUN", head="", rel="", misc=True
        )
    ]


def test_sentence_conversion_casing():
    token_list = TokenList(
        [
            Token(
                id=1,
                form="Test",
                lemma="test",
                upos="NOUN",
                xpos="",
                feats={},
                head="",
                deprel="",
                deps=None,
                misc={"SpaceAfter": "No"},
            ),
        ]
    )
    assert pro.convert_sentence(token_list) == [
        DBToken(
            idx=1,
            surface="Test",
            lemma="Test",
            tag="NOUN",
            head="",
            rel="",
            misc=True,
        )
    ]


def test_sentence_conversion_caps_normalization():
    token_list = TokenList(
        [
            Token(
                id=1,
                form="testen",
                lemma="TESTEN",
                upos="VERB",
                xpos="",
                feats={},
                head="",
                deprel="",
                deps=None,
                misc={"SpaceAfter": "No"},
            ),
        ]
    )
    assert pro.convert_sentence(token_list) == [
        DBToken(
            idx=1,
            surface="testen",
            lemma="testen",
            tag="VERB",
            head="",
            rel="",
            misc=True,
        )
    ]


def test_sentence_conversion_ne_tags():
    token_list = TokenList(
        [
            Token(
                id=1,
                form="Name",
                lemma="Name",
                upos="",
                xpos="",
                feats={},
                head="",
                deprel="",
                deps=None,
                misc={"NER": "S-PER"},
            ),
        ]
    )
    assert pro.convert_sentence(token_list) == [
        DBToken(
            idx=1,
            surface="Name",
            lemma="Name",
            tag="PROPN",
            head="",
            rel="",
            misc=False,
        )
    ]


def test_sentence_conversion_contracted_adp():
    token_list = TokenList(
        [
            Token(
                id=1,
                form="am",
                lemma="am",
                upos="ADP",
                xpos="",
                feats={},
                head="",
                deprel="",
                deps=None,
                misc={},
            ),
        ]
    )
    assert pro.convert_sentence(token_list) == [
        DBToken(
            idx=1,
            surface="am",
            lemma="an",
            tag="ADP",
            head="",
            rel="",
            misc=False,
        )
    ]


def test_sentence_conversion_to_dbtoken_invalid_chars_removed():
    token_list = TokenList(
        [
            Token(
                id=1,
                form="testen\\",
                lemma="testen",
                upos="VERB",
                xpos="",
                feats={},
                head="",
                deprel="",
                deps=None,
                misc={"SpaceAfter": "No"},
            ),
        ]
    )
    assert pro.convert_sentence(token_list) == [
        DBToken(
            idx=1,
            surface="testen",
            lemma="testen",
            tag="VERB",
            head="",
            rel="",
            misc=True,
        )
    ]
