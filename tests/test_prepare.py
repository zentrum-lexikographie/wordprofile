from conllu.models import Metadata

import wordprofile.wpse.prepare as pre
from wordprofile.datatypes import DBConcordance, DBCorpusFile, DBMatch, Match, WPToken


def test_prepare_corpus_file():
    metadata = Metadata(
        {
            "DDC:meta.file_": "path/to/file",
            "text": "text",
            "DDC:meta.collection": "coll",
            "DDC:meta.basename": "basename",
            "DDC:meta.bibl": "bibl",
            "DDC:meta.biblLext": "biblLex",
            "DDC:meta.data_": "data",
            "DDC:meta.textClass": "textclass",
        }
    )
    result = pre.prepare_corpus_file(metadata)
    assert result[0] == "path/to/file"
    assert isinstance(result[1], DBCorpusFile)
    assert result[1].id == result[0]
    assert result[1].corpus == "coll"
    assert result[1].orig == "bibl"


def test_prepare_concord_sentence():
    parses = [
        [
            WPToken(
                idx=1,
                surface="A",
                lemma="",
                tag="",
                head="",
                rel="",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="B",
                lemma="",
                tag="",
                head="",
                rel="",
                misc=False,
            ),
        ]
    ]
    assert pre.prepare_concord_sentences("1", parses) == [
        DBConcordance(corpus_file_id="1", sentence_id=1, sentence="A\x01B", page="-")
    ]


def test_index_counter_starts_at_one_for_concord_sentences():
    parses = [
        [WPToken(idx=1, surface="A", lemma="", tag="", head="", rel="", misc=True)]
    ]
    result = pre.prepare_concord_sentences("1", parses * 3)
    assert [sent.sentence_id for sent in result] == [1, 2, 3]


def test_prepare_matches_long_token_excluded(caplog):
    head = WPToken(
        idx=1,
        surface="thiscontainsmorethanfiftyletterstoexcedethecharlimit",
        lemma="",
        tag="",
        head=0,
        rel="",
        misc=True,
    )
    dep = WPToken(idx=2, surface="B", lemma="B", tag="", head=0, rel="", misc=False)
    matches = [Match(head, dep, prep=None, relation="", sid=0)]
    assert pre.prepare_matches("1", matches) == []
    assert "SKIP LONG MATCH" in caplog.text


def test_conversion_to_db_match():
    head = WPToken(
        idx=1, surface="Head", lemma="head", tag="Tag1", head=0, rel="", misc=True
    )
    dep = WPToken(
        idx=2, surface="Dep", lemma="dep", tag="Tag2", head=1, rel="", misc=False
    )
    matches = [Match(head, dep, prep=None, relation="REL", sid=0)]
    assert pre.prepare_matches("1", matches) == [
        DBMatch(
            relation_label="REL",
            head_lemma="head",
            dep_lemma="dep",
            head_tag="Tag1",
            dep_tag="Tag2",
            head_surface="Head",
            dep_surface="Dep",
            head_position=1,
            dep_position=2,
            prep_position=0,
            corpus_file_id="1",
            sentence_id=0,
        )
    ]


def test_conversion_to_db_match_with_prep():
    head = WPToken(idx=1, surface="A", lemma="A", tag="", head="", rel="", misc=True)
    dep = WPToken(idx=3, surface="B", lemma="B", tag="", head="", rel="", misc=False)
    prep = WPToken(idx=2, surface="C", lemma="C", tag="", head="", rel="", misc=True)
    matches = [Match(head, dep, prep, relation="REL", sid=0)]
    assert pre.prepare_matches("1", matches) == [
        DBMatch(
            relation_label="REL",
            head_lemma="A C",
            dep_lemma="B",
            head_tag="",
            dep_tag="",
            head_surface="A C",
            dep_surface="B",
            head_position=1,
            dep_position=3,
            prep_position=2,
            corpus_file_id="1",
            sentence_id=0,
        ),
        DBMatch(
            relation_label="REL",
            head_lemma="A",
            dep_lemma="C B",
            head_tag="",
            dep_tag="",
            head_surface="A",
            dep_surface="C B",
            head_position=1,
            dep_position=3,
            prep_position=2,
            corpus_file_id="1",
            sentence_id=0,
        ),
    ]
