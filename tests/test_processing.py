import io
import pathlib
import tempfile

import conllu
import pytest
from conllu.models import Token, TokenList

import wordprofile.wpse.processing as pro
from wordprofile.datatypes import DBToken


class MockQueue:
    def __init__(self):
        self.queue = []

    def get(self):
        if self.queue:
            return self.queue.pop(0)
        return None

    def put(self, item):
        self.queue.append(item)


class MockQueueWithError(MockQueue):
    def __init__(self, error=TypeError):
        self.error = error
        super().__init__()

    def put(self, item):
        raise self.error


@pytest.fixture
def conll_sentences():
    testdata_file = pathlib.Path(__file__).parent / "testdata" / "process_data.conll"
    with open(testdata_file, "r") as fh:
        return conllu.parse(fh.read(), fields=conllu.parser.DEFAULT_FIELDS)


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


def test_process_doc_file_queues_filled(conll_sentences):
    file_reader_queue = MockQueue()
    file_reader_queue.put(conll_sentences)
    db_files_queue = MockQueue()
    db_sents_queue = MockQueue()
    db_matches_queue = MockQueue()
    pro.process_doc_file(
        file_reader_queue, db_files_queue, db_sents_queue, db_matches_queue
    )
    assert len(db_files_queue.queue) == 1
    db_file = db_files_queue.get()[0]
    assert (
        db_file.id,
        db_file.corpus,
        db_file.orig,
        db_file.date,
        db_file.text_class,
    ) == (
        "politische_reden01/../../ddc_xml/data/src/de1/DE1_0999_20090602.ddc.xml",
        "politische_reden",
        "Rede von Frank-Walter Steinmeier, 02.06.2009",
        "2009-06-02",
        "gesprochen:Rede",
    )
    sentences = db_sents_queue.get()
    assert len(sentences) == 3
    assert sentences[2].sentence == "Eine\x02neue\x02Zeit\x02begann\x02."
    matches = db_matches_queue.get()
    assert len(matches) == 12
    assert (matches[0].head_lemma, matches[0].dep_lemma) == ("geehrt", "sehr")
    assert (matches[-1].relation_label, matches[-1].head_surface) == ("SUBJA", "begann")


def test_process_doc_file_errors_logged(conll_sentences, caplog):
    file_reader_queue = MockQueue()
    file_reader_queue.put(conll_sentences)
    db_files_queue = MockQueue()
    db_sents_queue = MockQueue()
    db_matches_queue = MockQueueWithError()
    pro.process_doc_file(
        file_reader_queue, db_files_queue, db_sents_queue, db_matches_queue
    )
    assert "Type Conversion Error:" in caplog.text
    file_reader_queue = MockQueue()
    file_reader_queue.put(conll_sentences)
    db_files_queue = MockQueue()
    db_sents_queue = MockQueue()
    db_matches_queue = MockQueueWithError(ValueError)
    pro.process_doc_file(
        file_reader_queue, db_files_queue, db_sents_queue, db_matches_queue
    )
    assert "ValueError" in caplog.text
    assert (
        "politische_reden01/../../ddc_xml/data/src/de1/DE1_0999_20090602.ddc.xml"
        in caplog.text
    )


def test_file_reader_single_file():
    conll_file = pathlib.Path(__file__).parent / "testdata" / "process_data.conll"
    file_reader = pro.FileReader([conll_file], MockQueue())
    file_reader.run()
    file_reader.stop(1)
    result = []
    while True:
        doc = file_reader.q.get()
        if doc is None:
            break
        result.append(doc)
    assert len(result) == 1
    assert (
        " ".join([token["form"] for sent in result[0] for token in sent])
        == "Sehr geehrter Herr Präsident Palinkás , meine sehr verehrten Damen und Herren ,"
        " Exzellenzen , Damals ging eine ganze Epoche zu Ende . Eine neue Zeit begann ."
    )


def test_file_reader_multiple_files():
    corpus_dir = pathlib.Path(__file__).parent / "testdata" / "corpus"
    files = list(corpus_dir.glob("*"))
    file_reader = pro.FileReader(files, MockQueue())
    file_reader.run()
    file_reader.stop(1)
    result = []
    while True:
        doc = file_reader.q.get()
        if doc is None:
            break
        result.append(doc)
    assert len(result) == 4
    assert {sent[0]["form"] for doc in result for sent in doc} == {
        "Damals",
        "Sehr",
        "Eine",
        "Exzellenzen",
    }


def test_file_reader_with_std_input(monkeypatch):
    with open(
        pathlib.Path(__file__).parent / "testdata" / "corpus" / "file1.conll"
    ) as fh:
        data = io.StringIO()
        for line in fh:
            data.write(line)
    data.seek(0)
    monkeypatch.setattr("sys.stdin", data)
    file_reader = pro.FileReader("-", MockQueue())
    file_reader.run()
    file_reader.stop(1)
    result = []
    while True:
        doc = file_reader.q.get()
        if doc is None:
            break
        result.append(doc)
    assert (
        " ".join(token["form"] for token in result[0][0])
        == "Damals ging eine ganze Epoche zu Ende ."
    )


def test_sentence_conversion_casing_with_multi_part_token():
    token_list = TokenList(
        [
            Token(
                id=1,
                form="Kopf-an-Kopf-Rennen",
                lemma="kopf-an-Kopf-Rennen",
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
            surface="Kopf-an-Kopf-Rennen",
            lemma="Kopf-an-Kopf-Rennen",
            tag="NOUN",
            head="",
            rel="",
            misc=True,
        )
    ]


def test_sentence_conversion_token_only_contains_invalid_chars():
    token_list = TokenList(
        [
            Token(
                id=1,
                form="Anfang",
                lemma="Anfang",
                upos="NOUN",
                xpos="",
                feats={},
                head="",
                deprel="",
                deps=None,
                misc={"SpaceAfter": "No"},
            ),
            Token(
                id=2,
                form="\\",
                lemma="\\",
                upos="NOUN",
                xpos="",
                feats={},
                head="",
                deprel="",
                deps=None,
                misc={"SpaceAfter": "No"},
            ),
            Token(
                id=3,
                form="Ende",
                lemma="Ende",
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
            surface="Anfang",
            lemma="Anfang",
            tag="NOUN",
            head="",
            rel="",
            misc=True,
        ),
        DBToken(
            idx=2,
            surface="_",
            lemma="_",
            tag="NOUN",
            head="",
            rel="",
            misc=True,
        ),
        DBToken(
            idx=3,
            surface="Ende",
            lemma="Ende",
            tag="NOUN",
            head="",
            rel="",
            misc=True,
        ),
    ]


def test_load_collocations_freq_filter_applied_to_aggregated_collocations():
    input_files = list(
        (pathlib.Path(__file__).parent / "testdata" / "freq_test").iterdir()
    )
    collocations = pro.load_collocations(input_files, min_rel_freq=3)
    result = [col[1:] for col in collocations.values()]
    assert len(result) == 3
    assert ("GMOD", "Thema", "Gegenwart", "NOUN", "NOUN", 0, 2) not in result
    assert ("ATTR", "Familienpolitik", "modern", "NOUN", "ADJ", 0, 12) in result
    assert ("ATTR", "Stadtrand", "östlich", "NOUN", "ADJ", 0, 3) in result


def test_matches_with_collocation_id_zero_not_discarded():
    colloc_files = list(
        (pathlib.Path(__file__).parent / "testdata" / "freq_test").iterdir()
    )
    collocations = pro.load_collocations(colloc_files, min_rel_freq=5)
    corpus_file_ids = {"doc1": 1}
    sentence_ids = {("1", "3"), ("1", "4")}
    matches_file = pathlib.Path(__file__).parent / "testdata" / "matches"
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = pathlib.Path(tmpdir) / "file"
        pro.filter_transform_matches(
            [matches_file], output_file, corpus_file_ids, sentence_ids, collocations
        )
        with open(output_file) as fh:
            result = [line.split()[1:4] for line in fh]
    assert len(result) == 2
    assert ["Zeitung", "süddeutsche"] in [collocation[1:] for collocation in result]
    assert {"0", "1"} == {collocation[0] for collocation in result}


def test_collapse_lemma_of_phrasal_verbs():
    sentence = [
        DBToken(
            idx=1,
            surface="Denn",
            lemma="denn",
            tag="CCONJ",
            head=4,
            rel="cc",
            misc=True,
        ),
        DBToken(
            idx=2,
            surface="die",
            lemma="d",
            tag="DET",
            head=3,
            rel="det",
            misc=True,
        ),
        DBToken(
            idx=3,
            surface="Läuterung",
            lemma="Läuterung",
            tag="NOUN",
            head=4,
            rel="nsubj",
            misc=True,
        ),
        DBToken(
            idx=4,
            surface="setzt",
            lemma="setzen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        DBToken(
            idx=5,
            surface="überlicherweise",
            lemma="überlicherweise",
            tag="ADJ",
            head=4,
            rel="advmod",
            misc=True,
        ),
        DBToken(
            idx=6,
            surface="erst",
            lemma="erst",
            tag="ADV",
            head=7,
            rel="advmod",
            misc=True,
        ),
        DBToken(
            idx=7,
            surface="später",
            lemma="spät",
            tag="ADJ",
            head=4,
            rel="advmod",
            misc=True,
        ),
        DBToken(
            idx=8,
            surface="ein",
            lemma="ein",
            tag="ADP",
            head=4,
            rel="compound:prt",
            misc=True,
        ),
    ]
    pro.collapse_phrasal_verbs(sentence)
    assert sentence[3] == DBToken(
        idx=4,
        surface="setzt",
        lemma="einsetzen",
        tag="VERB",
        head=0,
        rel="ROOT",
        misc=True,
        prt_pos=8,
    )


def test_particle_not_collapsed_if_prt_not_adp():
    sentence = [
        DBToken(
            idx=1,
            surface="Opposition",
            lemma="Opposition",
            tag="NOUN",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        DBToken(
            idx=2,
            surface="läuft",
            lemma="laufen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        DBToken(
            idx=3,
            surface="Sturm",
            lemma="Sturm",
            tag="NOUN",
            head=2,
            rel="compound:prt",
            misc=True,
        ),
    ]
    pro.collapse_phrasal_verbs(sentence)
    assert sentence[1] == DBToken(
        idx=2,
        surface="läuft",
        lemma="laufen",
        tag="VERB",
        head=0,
        rel="ROOT",
        misc=True,
    )


def test_particle_not_collapsed_if_head_not_verb():
    sentence = [
        DBToken(
            idx=1,
            surface="Pauli",
            lemma="Pauli",
            tag="PROPN",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        DBToken(
            idx=2,
            surface="folgt",
            lemma="folgen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        DBToken(
            idx=3,
            surface="Ministerpräsident",
            lemma="Ministerpräsident",
            tag="NOUN",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        DBToken(
            idx=4,
            surface="Günther",
            lemma="Günther",
            tag="PROPN",
            head=3,
            rel="flat:name",
            misc=True,
        ),
        DBToken(
            idx=5,
            surface="Beckstein",
            lemma="Beckstein",
            tag="PROPN",
            head=3,
            rel="flat:name",
            misc=True,
        ),
        DBToken(
            idx=6,
            surface="nach",
            lemma="nach",
            tag="ADP",
            head=3,
            rel="compound:prt",
            misc=True,
        ),
    ]
    pro.collapse_phrasal_verbs(sentence)
    assert sentence[2] == DBToken(
        idx=3,
        surface="Ministerpräsident",
        lemma="Ministerpräsident",
        tag="NOUN",
        head=0,
        rel="ROOT",
        misc=True,
    )
