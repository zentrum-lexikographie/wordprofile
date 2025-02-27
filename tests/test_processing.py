import io
import multiprocessing as mp
import pathlib
import tempfile
from collections import defaultdict

import conllu
import pytest
from conllu.models import Token, TokenList

import wordprofile.wpse.processing as pro
from wordprofile.datatypes import Colloc, CollocInstance, DBMatch, WPToken


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
def testdata_dir():
    return pathlib.Path(__file__).parent / "testdata"


@pytest.fixture
def conll_sentences(testdata_dir):
    testdata_file = testdata_dir / "process_data.conll"
    with open(testdata_file, "r") as fh:
        return conllu.parse(fh.read(), fields=conllu.parser.DEFAULT_FIELDS)


@pytest.fixture
def collocations():
    return {
        30601: Colloc(
            30601, "GMOD", "Sprecher", "Feuerwehr", "NOUN", "NOUN", "_", 0, 15
        ),
        368: Colloc(368, "GMOD", "Haus", "Kunst", "NOUN", "NOUN", "_", 0, 389),
        2006644: Colloc(2006644, "ATTR", "Kunst", "schöne", "NOUN", "ADJ", "_", 0, 42),
        3406416: Colloc(3406416, "KON", "Kunst", "Kultur", "NOUN", "NOUN", "_", 0, 51),
        2367256: Colloc(2367256, "VZ", "nehmen", "fest", "VERB", "ADP", "_", 0, 386),
        2373301: Colloc(
            2373301, "SUBJA", "nehmen", "Polizei", "VERB", "NOUN", "_", 0, 262
        ),
    }


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
        WPToken(
            idx=1,
            surface="Test",
            lemma="Test",
            tag="NOUN",
            head="",
            rel="",
            misc=True,
            morph={},
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
        WPToken(
            idx=1,
            surface="Test",
            lemma="Test",
            tag="NOUN",
            head="",
            rel="",
            misc=True,
            morph={},
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
        WPToken(
            idx=1,
            surface="testen",
            lemma="testen",
            tag="VERB",
            head="",
            rel="",
            misc=True,
            morph={},
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
        WPToken(
            idx=1,
            surface="Name",
            lemma="Name",
            tag="PROPN",
            head="",
            rel="",
            misc=False,
            morph={},
        )
    ]


def test_sentence_conversion_contracted_adp():
    prepositions = [
        ("am", "an"),
        ("aufs", "auf"),
        ("ans", "an"),
        ("beim", "bei"),
        ("fürs", "für"),
        ("hinters", "hinter"),
        ("hinterm", "hinter"),
        ("im", "in"),
        ("ins", "in"),
        ("übers", "über"),
        ("überm", "über"),
        ("ums", "um"),
        ("unterm", "unter"),
        ("unters", "unter"),
        ("untern", "unter"),
        ("vorm", "vor"),
        ("vors", "vor"),
        ("vom", "von"),
        ("zum", "zu"),
        ("zur", "zu"),
    ]
    for prep, lemma in prepositions:
        token_list = TokenList(
            [
                Token(
                    id=1,
                    form=prep,
                    lemma=prep,
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
            WPToken(
                idx=1,
                surface=prep,
                lemma=lemma,
                tag="ADP",
                head="",
                rel="",
                misc=False,
                morph={},
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
        WPToken(
            idx=1,
            surface="testen",
            lemma="testen",
            tag="VERB",
            head="",
            rel="",
            misc=True,
            morph={},
        )
    ]


def test_process_doc_file_queues_filled(conll_sentences):
    file_reader_queue = MockQueue()
    file_reader_queue.put(conll_sentences)
    db_files_queue = MockQueue()
    db_sents_queue = MockQueue()
    db_matches_queue = MockQueue()
    lemma_counters = []
    pro.process_doc_file(
        file_reader_queue,
        db_files_queue,
        db_sents_queue,
        db_matches_queue,
        lemma_counters,
    )
    assert len(db_files_queue.queue) == 1
    db_file = db_files_queue.get()[0]
    assert (
        db_file.id,
        db_file.corpus,
        db_file.orig,
        db_file.date,
    ) == (
        "politische_reden01/../../ddc_xml/data/src/de1/DE1_0999_20090602.ddc.xml",
        "politische_reden",
        "Rede von Frank-Walter Steinmeier, 02.06.2009",
        "2009-06-02",
    )
    sentences = db_sents_queue.get()
    assert len(sentences) == 3
    assert sentences[2].sentence == "Eine\x02neue\x02Zeit\x02begann\x02."
    matches = db_matches_queue.get()
    assert len(matches) == 11
    assert (matches[0].head_lemma, matches[0].dep_lemma) == ("geehrt", "sehr")
    assert (matches[-1].relation_label, matches[-1].head_surface) == ("SUBJA", "begann")


def test_process_doc_file_errors_logged(conll_sentences, caplog):
    file_reader_queue = MockQueue()
    file_reader_queue.put(conll_sentences)
    db_files_queue = MockQueue()
    db_sents_queue = MockQueue()
    lemma_counters = []
    db_matches_queue = MockQueueWithError()
    pro.process_doc_file(
        file_reader_queue,
        db_files_queue,
        db_sents_queue,
        db_matches_queue,
        lemma_counters,
    )
    assert "Type Conversion Error:" in caplog.text
    file_reader_queue = MockQueue()
    file_reader_queue.put(conll_sentences)
    db_files_queue = MockQueue()
    db_sents_queue = MockQueue()
    db_matches_queue = MockQueueWithError(ValueError)
    pro.process_doc_file(
        file_reader_queue,
        db_files_queue,
        db_sents_queue,
        db_matches_queue,
        lemma_counters,
    )
    assert "ValueError" in caplog.text
    assert (
        "politische_reden01/../../ddc_xml/data/src/de1/DE1_0999_20090602.ddc.xml"
        in caplog.text
    )


def test_file_reader_single_file(testdata_dir):
    conll_file = testdata_dir / "process_data.conll"
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


def test_file_reader_multiple_files(testdata_dir):
    corpus_dir = testdata_dir / "corpus"
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


def test_file_reader_with_std_input(monkeypatch, testdata_dir):
    with open(testdata_dir / "corpus" / "file1.conll") as fh:
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
        WPToken(
            idx=1,
            surface="Kopf-an-Kopf-Rennen",
            lemma="Kopf-an-Kopf-Rennen",
            tag="NOUN",
            head="",
            rel="",
            misc=True,
            morph={},
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
        WPToken(
            idx=1,
            surface="Anfang",
            lemma="Anfang",
            tag="NOUN",
            head="",
            rel="",
            misc=True,
            morph={},
        ),
        WPToken(
            idx=2,
            surface="_",
            lemma="_",
            tag="NOUN",
            head="",
            rel="",
            misc=True,
            morph={},
        ),
        WPToken(
            idx=3,
            surface="Ende",
            lemma="Ende",
            tag="NOUN",
            head="",
            rel="",
            misc=True,
            morph={},
        ),
    ]


def test_inverse_attribute_written_to_mwe_file():
    mwe_freqs = {1: 1}
    mwe_ids = {(11, 12, "label", "lemma", "tag", 0): 1}
    collocs = {
        11: Colloc(11, "", "", "", "", "", "_", 0, 1.0),
        12: Colloc(12, "", "", "", "", "", "_", 0, 1.0),
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        file = pathlib.Path(tmpdir) / "file"
        pro.compute_mwe_scores(file, mwe_ids, mwe_freqs, collocs, min_freq=1)
        with open(file) as fp:
            result = fp.read().split()
    assert result == ["1", "11", "12", "label", "lemma", "tag", "0", "1", "14.0"]


def test_mwe_relation_not_inverse_if_not_reciprocal(collocations):
    collocations[2373301] = Colloc(
        2373301, "KON", "nehmen", "Polizei", "VERB", "NOUN", "_", 0, 262
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        file = pathlib.Path(tmpdir) / "file"
        mwe_ids, _ = pro.extract_mwe_from_collocs(
            "tests/testdata/test_db/matches", file, collocations
        )
    assert (2367256, 2373301, "KON", "Polizei", "NOUN", 0) in mwe_ids


def test_load_collocations_freq_filter_applied_to_aggregated_collocations(testdata_dir):
    input_files = list((testdata_dir / "freq_test").iterdir())
    collocations = pro.load_collocations(input_files, min_rel_freq=3)
    result = [col[1:] for col in collocations.values()]
    assert len(result) == 3
    assert ("GMOD", "Thema", "Gegenwart", "NOUN", "NOUN", "_", 0, 2) not in result
    assert ("ATTR", "Familienpolitik", "modern", "NOUN", "ADJ", "_", 0, 12) in result
    assert ("ATTR", "Stadtrand", "östlich", "NOUN", "ADJ", "_", 0, 3) in result


def test_collocation_ids_start_at_one(testdata_dir):
    colloc_files = list((testdata_dir / "freq_test").iterdir())
    collocations = pro.load_collocations(colloc_files, min_rel_freq=5)
    assert min(collocations.keys()) == 1


def test_collapse_lemma_of_phrasal_verbs():
    sentence = [
        WPToken(
            idx=1,
            surface="Denn",
            lemma="denn",
            tag="CCONJ",
            head=4,
            rel="cc",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="die",
            lemma="d",
            tag="DET",
            head=3,
            rel="det",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="Läuterung",
            lemma="Läuterung",
            tag="NOUN",
            head=4,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="setzt",
            lemma="setzen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="überlicherweise",
            lemma="überlicherweise",
            tag="ADJ",
            head=4,
            rel="advmod",
            misc=True,
        ),
        WPToken(
            idx=6,
            surface="erst",
            lemma="erst",
            tag="ADV",
            head=7,
            rel="advmod",
            misc=True,
        ),
        WPToken(
            idx=7,
            surface="später",
            lemma="spät",
            tag="ADJ",
            head=4,
            rel="advmod",
            misc=True,
        ),
        WPToken(
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
    assert sentence[3] == WPToken(
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
        WPToken(
            idx=1,
            surface="Opposition",
            lemma="Opposition",
            tag="NOUN",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="läuft",
            lemma="laufen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
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
    assert sentence[1] == WPToken(
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
        WPToken(
            idx=1,
            surface="Pauli",
            lemma="Pauli",
            tag="PROPN",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="folgt",
            lemma="folgen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="Ministerpräsident",
            lemma="Ministerpräsident",
            tag="NOUN",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="Günther",
            lemma="Günther",
            tag="PROPN",
            head=3,
            rel="flat:name",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="Beckstein",
            lemma="Beckstein",
            tag="PROPN",
            head=3,
            rel="flat:name",
            misc=True,
        ),
        WPToken(
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
    assert sentence[2] == WPToken(
        idx=3,
        surface="Ministerpräsident",
        lemma="Ministerpräsident",
        tag="NOUN",
        head=0,
        rel="ROOT",
        misc=True,
    )


def test_lemma_of_phrasal_verb_collapsed_during_conll_conversion():
    token_list = TokenList(
        [
            Token(
                id=1,
                form="Test",
                lemma="Test",
                upos="NOUN",
                xpos="",
                feats={},
                head=2,
                deprel="nsubj",
                deps=None,
                misc={"SpaceAfter": "Yes"},
            ),
            Token(
                id=2,
                form="schlägt",
                lemma="schlagen",
                upos="VERB",
                xpos="",
                feats={},
                head=0,
                deprel="ROOT",
                deps=None,
                misc={"SpaceAfter": "Yes"},
            ),
            Token(
                id=3,
                form="fehl",
                lemma="fehl",
                upos="ADP",
                xpos="",
                feats={},
                head=2,
                deprel="compound:prt",
                deps=None,
                misc={"SpaceAfter": "No"},
            ),
        ]
    )
    result = pro.convert_sentence(token_list)
    assert result[1].lemma == "fehlschlagen"


def test_case_normalization_and_phrasal_verb_lemmatization():
    token_list = TokenList(
        [
            Token(
                id=1,
                form="Test",
                lemma="Test",
                upos="NOUN",
                xpos="",
                feats={},
                head=2,
                deprel="nsubj",
                deps=None,
                misc={"SpaceAfter": "Yes"},
            ),
            Token(
                id=2,
                form="Schlägt",
                lemma="Schlagen",
                upos="VERB",
                xpos="",
                feats={},
                head=0,
                deprel="ROOT",
                deps=None,
                misc={"SpaceAfter": "Yes"},
            ),
            Token(
                id=3,
                form="fehl",
                lemma="fehl",
                upos="ADP",
                xpos="",
                feats={},
                head=2,
                deprel="compound:prt",
                deps=None,
                misc={"SpaceAfter": "No"},
            ),
        ]
    )
    result = pro.convert_sentence(token_list)
    assert result[1].lemma == "fehlschlagen"


def test_collapse_lemma_of_phrasal_verbs_from_file(testdata_dir):
    conll_file = testdata_dir / "phrasal_verbs.conll"
    with open(conll_file) as fh:
        doc = conllu.parse(fh.read())
    sentences = [pro.convert_sentence(sent) for sent in doc]
    result = [tok.lemma for sent in sentences for tok in sent if tok.tag == "VERB"]
    assert result == [
        "bereithalten",
        "erleben",
        "stattfinden",
        "naheliegen",
        "vornehmen",
        "ankommen",
    ]


def test_write_matches_with_phrasal_verb_to_file():
    def fill_queue(m_queue):
        matches = [
            DBMatch(
                relation_label="ADV",
                head_lemma="gestern",
                dep_lemma="einfallen",
                head_tag="ADV",
                dep_tag="VERB",
                prep="_",
                head_surface="gestern",
                dep_surface="fällt",
                head_position=2,
                dep_position=1,
                extra_position="5-3",
                corpus_file_id="1",
                sentence_id=0,
            ),
            DBMatch(
                relation_label="ADV",
                head_lemma="gestern",
                dep_lemma="einfallen",
                head_tag="ADV",
                dep_tag="VERB",
                prep="_",
                head_surface="gestern",
                dep_surface="fällt",
                head_position=2,
                dep_position=1,
                extra_position="3-5",
                corpus_file_id="1",
                sentence_id=0,
            ),
        ]
        m_queue.put(matches)
        m_queue.put(None)

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = mp.Manager()
        output_process = pro.FileWorker(tmpdir, "matches", manager)
        output_process.start()
        proc = mp.Process(target=fill_queue, args=(output_process.q,))
        proc.start()
        proc.join()
        output_process.join()
        with open(pathlib.Path(tmpdir) / "matches") as fh:
            result = fh.readlines()
    assert set(result) == {
        "ADV\tgestern\teinfallen\tADV\tVERB\t_\tgestern\tfällt\t2\t1\t5-3\t1\t0\n",
        "ADV\tgestern\teinfallen\tADV\tVERB\t_\tgestern\tfällt\t2\t1\t3-5\t1\t0\n",
    }


def test_aggregating_matches_with_extra_position(testdata_dir):
    colloc_files = list((testdata_dir / "freq_test").iterdir())
    collocations = pro.load_collocations(colloc_files, min_rel_freq=5)
    corpus_file_ids = {"doc1": 1}
    sentence_ids = {("1", "3"), ("1", "4")}
    matches_dir = testdata_dir / "matches_agg"
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = pathlib.Path(tmpdir) / "file"
        pro.filter_transform_matches(
            list(matches_dir.iterdir()),
            output_file,
            corpus_file_ids,
            sentence_ids,
            collocations,
        )
        with open(output_file) as fh:
            result = [line[4:] for line in fh]
    assert len(result) == 4
    assert "Zeitung\tsüddeutsche\t3\t2\t3-5\t1\t3\n" in result


def test_convert_line_from_matches_file_to_CollocInstance():
    lines = [
        "6\t184955\tUmzug\tHochhaus\t16\t22\t20\t0\t3",
        "8\t2028198\tStadtrand\töstlichen\t27\t26\t-\t0\t3",
        "4\t184954\tsetzte\tUmzug\t8\t16\t28-14\t0\t3",
    ]
    extra_pos = []
    for line in lines:
        colloc = pro.convert_line(line, CollocInstance, pro.COLLOC_INSTANCE_DTYPES)
        assert isinstance(colloc, CollocInstance)
        extra_pos.append(colloc.prep_pos)
    assert extra_pos == ["20", "-", "28-14"]


def test_extraction_of_mwe(testdata_dir):
    collocations = {
        3520378: Colloc(3520378, "KON", "Lust", "Laune", "NOUN", "NOUN", "_", 0, 10.0),
        281402: Colloc(
            281402, "PP", "dirigieren", "Lust", "VERB", "NOUN", "nach", 0, 10.0
        ),
        281401: Colloc(
            281401, "PP", "Lust", "dirigieren", "NOUN", "VERB", "nach", 1, 10.0
        ),
        5: Colloc(5, "GMOD", "Überangebot", "Umgebung", "NOUN", "NOUN", "_", 0, 11.0),
        2028213: Colloc(
            2028213,
            "ATTR",
            "Überangebot",
            "gastronomisch",
            "NOUN",
            "ADJ",
            "_",
            0,
            9.0,
        ),
        184977: Colloc(
            184977, "PP", "versumpfen", "Überangebot", "VERB", "NOUN", "in", 0, 8.0
        ),
        2028618: Colloc(
            2028618,
            "ATTR",
            "Steuersatz",
            "durchschnittlich",
            "NOUN",
            "ADJ",
            "_",
            0,
            5.0,
        ),
        186151: Colloc(
            186151, "SUBJA", "setzen", "Steuersatz", "VERB", "NOUN", "_", 0, 11.0
        ),
        186152: Colloc(
            186152, "SUBJA", "Steuersatz", "setzen", "NOUN", "VERB", "_", 1, 11.0
        ),
        185242: Colloc(
            185242, "PP", "Sparleistung", "Höhe", "NOUN", "NOUN", "_", 0, 10.0
        ),
        2028296: Colloc(
            2028296, "ATTR", "Sparleistung", "eigen", "NOUN", "ADJ", "_", 0, 10.0
        ),
    }
    matches_file = testdata_dir / "mwe_matches"
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = pathlib.Path(tmpdir) / "file"
        pro.extract_mwe_from_collocs(matches_file, output_file, collocations)
        with open(output_file) as fh:
            mwe = [line.strip().split("\t") for line in fh.readlines()]
    result = [(int(line[1]), int(line[2])) for line in mwe]
    assert (270699, 270697) in result
    assert len(result) == 10


def test_particles_with_adj_and_adv_tag_concatenated_in_phrasal_verb_lemmatisation():
    sentences = [
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
                surface="Fahrer",
                lemma="Fahrer",
                tag="NOUN",
                head=3,
                rel="nsubj",
                misc=True,
            ),
            WPToken(
                idx=3,
                surface="fuhr",
                lemma="fahren",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=4,
                surface="an",
                lemma="an",
                tag="ADP",
                head=6,
                rel="case",
                misc=True,
            ),
            WPToken(
                idx=5,
                surface="dem",
                lemma="d",
                tag="DET",
                head=6,
                rel="det",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="Polizisten",
                lemma="Polizist",
                tag="NOUN",
                head=3,
                rel="obl",
                misc=True,
            ),
            WPToken(
                idx=7,
                surface="vorbei",
                lemma="vorbei",
                tag="ADV",
                head=3,
                rel="compound:prt",
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
                surface="Tür",
                lemma="Tür",
                tag="NOUN",
                head=3,
                rel="nsubj",
                misc=True,
            ),
            WPToken(
                idx=3,
                surface="steht",
                lemma="stehen",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=4,
                surface="offen",
                lemma="offen",
                tag="ADJ",
                head=3,
                rel="compound:prt",
                misc=True,
            ),
        ],
    ]
    for sent in sentences:
        pro.collapse_phrasal_verbs(sent)
    assert sentences[0][2].lemma == "vorbeifahren"
    assert sentences[1][2].lemma == "offenstehen"


def test_verb_irgnored_if_sein_during_phrasal_verb_lemmatisation():
    sentence = [
        WPToken(
            idx=1,
            surface="Dann",
            lemma="dann",
            tag="ADV",
            head=3,
            rel="advmod",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="ist",
            lemma="sein",
            tag="AUX",
            head=2,
            rel="parataxis",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="es",
            lemma="es",
            tag="PRON",
            head=2,
            rel="nsubj",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="mit",
            lemma="mit",
            tag="ADP",
            head=5,
            rel="case",
            misc=True,
        ),
        WPToken(
            idx=5,
            surface="der",
            lemma="d",
            tag="DET",
            head=6,
            rel="det",
            misc=False,
        ),
        WPToken(
            idx=6,
            surface="Heimlichkeit",
            lemma="Heimlichkeit",
            tag="NOUN",
            head=2,
            rel="obl",
            misc=True,
        ),
        WPToken(
            idx=7,
            surface="vorbei",
            lemma="vorbei",
            tag="ADP",
            head=2,
            rel="compound:prt",
            misc=True,
        ),
    ]
    pro.collapse_phrasal_verbs(sentence)
    assert sentence[1].lemma == "sein"
    assert sentence[1].prt_pos is None


def test_wrong_lemma_replaced_after_phrasal_verb_concatenation():
    sentence = [
        Token(
            id=1,
            form="Schwaben",
            lemma="Schwaben",
            upos="PROPN",
            xpos="NE",
            feats={},
            head=2,
            deprel="nsubj",
            deps=None,
            misc={},
        ),
        Token(
            id=2,
            form="fällt",
            lemma="fällen",
            upos="VERB",
            xpos="VVFIN",
            feats={},
            head=0,
            deprel="ROOT",
            deps=None,
            misc={},
        ),
        Token(
            id=3,
            form="oft",
            lemma="oft",
            upos="ADV",
            xpos="ADV",
            feats={},
            head=3,
            deprel="advmod",
            deps=None,
            misc={},
        ),
        Token(
            id=4,
            form="hinten",
            lemma="hinten",
            upos="ADV",
            xpos="ADV",
            feats={},
            head=2,
            deprel="advmod",
            deps=None,
            misc={},
        ),
        Token(
            id=5,
            form="heraus",
            lemma="heraus",
            upos="ADV",
            xpos="ADV",
            feats={},
            head=2,
            deprel="compound:prt",
            deps=None,
            misc={},
        ),
    ]
    result = pro.convert_sentence(sentence)
    assert result[1].lemma == "herausfallen"


def test_phrasal_verb_with_recht_as_particle_not_concatenated():
    sentences = [
        [
            WPToken(
                idx=1,
                surface="Hat",
                lemma="haben",
                tag="AUX",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="er",
                lemma="er",
                tag="PRON",
                head=1,
                rel="nsubj",
                misc=True,
            ),
            WPToken(
                idx=3,
                surface="doch",
                lemma="doch",
                tag="ADV",
                head=1,
                rel="advmod",
                misc=True,
            ),
            WPToken(
                idx=4,
                surface="recht",
                lemma="recht",
                tag="ADJ",
                head=1,
                rel="compound:prt",
                misc=True,
            ),
        ],
        [
            WPToken(
                idx=1,
                surface="VGH",
                lemma="VGH",
                tag="PROPN",
                head=2,
                rel="nsubj",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="gab",
                lemma="geben",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=3,
                surface="dem",
                lemma="d",
                tag="DET",
                head=4,
                rel="det",
                misc=True,
            ),
            WPToken(
                idx=4,
                surface="Landratsamt",
                lemma="Landratsamt",
                tag="NOUN",
                head=2,
                rel="obj",
                misc=True,
            ),
            WPToken(
                idx=5,
                surface="recht",
                lemma="recht",
                tag="ADP",
                head=2,
                rel="compound:prt",
                misc=True,
            ),
        ],
        [
            WPToken(
                idx=1,
                surface="Recht",
                lemma="recht",
                tag="ADP",
                head=2,
                rel="compound:prt",
                misc=True,
            ),
            WPToken(
                idx=2,
                surface="hat",
                lemma="haben",
                tag="VERB",
                head=0,
                rel="ROOT",
                misc=True,
            ),
            WPToken(
                idx=3,
                surface="sie",
                lemma="sie",
                tag="PRON",
                head=2,
                rel="nsubj",
                misc=True,
            ),
        ],
    ]
    for sent in sentences:
        pro.collapse_phrasal_verbs(sent)
    assert sentences[0][0].lemma == "haben"
    assert sentences[1][1].lemma == "geben"
    assert sentences[2][1].lemma == "haben"


def test_morphological_features_parse_from_conll_token():
    sentence = TokenList(
        [
            Token(
                id=1,
                form="am",
                lemma="an",
                upos="ADP",
                xpos="",
                feats={"AdpType": "Prep", "Case": "Dat"},
                head=2,
                deprel="case",
                deps=None,
                misc={"SpaceAfter": "Yes"},
            ),
            Token(
                id=2,
                form="Wochenende",
                lemma="Wochenende",
                upos="NOUN",
                xpos="",
                feats={"Gender": "Neut", "Number": "Sing"},
                head=None,
                deprel="ROOT",
                deps=None,
                misc={"SpaceAfter": "Yes"},
            ),
        ]
    )
    result = [tok.morph for tok in pro.convert_sentence(sentence)]
    assert result == [
        {"AdpType": "Prep", "Case": "Dat"},
        {"Gender": "Neut", "Number": "Sing"},
    ]


def test_morphological_features_parse_from_conll_file(conll_sentences):
    sentence = conll_sentences[2]
    result = pro.convert_sentence(sentence)
    assert result[0].morph is None
    assert ("Case", "Nom") in result[2].morph.items()
    assert ("Number", "Sing") in result[2].morph.items()


def test_inverse_of_objo_written_to_file():
    collocations = {
        1: Colloc(1, "OBJO", "beschuldigen", "Betrug", "VERB", "NOUN", "_", 0, 10.0),
    }
    lemma_frequencies = {("beschuldigen", "VERB"): 10, ("Betrug", "NOUN"): 10}
    with tempfile.TemporaryDirectory() as tmpdir:
        file = pathlib.Path(tmpdir) / "file"
        pro.compute_collocation_scores(file, collocations, lemma_frequencies)
        with open(file) as fp:
            result = [line.split() for line in fp.readlines()]
    assert result == [
        [
            "1",
            "OBJO",
            "beschuldigen",
            "Betrug",
            "VERB",
            "NOUN",
            "_",
            "0",
            "10.0",
            "14.0",
        ]
    ]


def test_mwe_filtered_for_min_freq():
    mwe_freqs = {1: 1, 0: 5, 2: 3}
    mwe_ids = {
        (11, 12, "label", "lemma", "tag", 0): 0,
        (13, 14, "label", "lemma", "tag", 0): 1,
        (15, 16, "label", "lemma", "tag", 0): 2,
    }
    collocs = {
        11: Colloc(11, "", "", "", "", "", "_", 0, 5.0),
        12: Colloc(12, "", "", "", "", "", "_", 0, 5.0),
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        file = pathlib.Path(tmpdir) / "file"
        pro.compute_mwe_scores(file, mwe_ids, mwe_freqs, collocs, min_freq=4)
        with open(file) as fp:
            result = fp.read().split()
    assert result == ["0", "11", "12", "label", "lemma", "tag", "0", "5", "14.0"]


def test_mwe_freq_and_id_update_unseen_mwe():
    mwe_freqencies = defaultdict(lambda: 1, {0: 2, 1: 4, 2: 10})
    mwe_ids = {
        (11, 12, "label", "a", "tag", 0): 0,
        (13, 14, "label", "b", "tag", 0): 1,
        (15, 16, "label", "c", "tag", 0): 2,
    }
    mwe_to_add = (1, 2, "label", "d", "tag", 1)
    new_id = pro.add_mwe_to_inventory(mwe_freqencies, mwe_ids, mwe_to_add)
    assert new_id == 3
    assert mwe_ids == {
        (11, 12, "label", "a", "tag", 0): 0,
        (13, 14, "label", "b", "tag", 0): 1,
        (15, 16, "label", "c", "tag", 0): 2,
        (1, 2, "label", "d", "tag", 1): 3,
    }
    assert set(mwe_freqencies.keys()) == {0, 1, 2}
    assert mwe_freqencies[new_id] == 1


def test_mwe_freq_and_id_update_mwe_encountered_second_time():
    mwe_freqencies = defaultdict(lambda: 1, {0: 2, 1: 4})
    mwe_ids = {
        (11, 12, "label", "a", "tag", 0): 0,
        (13, 14, "label", "b", "tag", 0): 1,
        (15, 16, "label", "c", "tag", 0): 2,
    }
    mwe_to_add = (15, 16, "label", "c", "tag", 0)
    mwe_id = pro.add_mwe_to_inventory(mwe_freqencies, mwe_ids, mwe_to_add)
    assert mwe_id == 2
    assert mwe_freqencies[mwe_id] == 2
    assert set(mwe_freqencies.keys()) == {0, 1, 2}


def test_mwe_freq_and_id_update_previously_seen_mwe():
    mwe_freqencies = defaultdict(lambda: 1, {0: 2, 1: 4, 2: 10})
    mwe_ids = {
        (11, 12, "label", "a", "tag", 0): 0,
        (13, 14, "label", "b", "tag", 0): 1,
        (15, 16, "label", "c", "tag", 0): 2,
    }
    mwe_to_add = (13, 14, "label", "b", "tag", 0)
    mwe_id = pro.add_mwe_to_inventory(mwe_freqencies, mwe_ids, mwe_to_add)
    assert mwe_id == 1
    assert mwe_freqencies[mwe_id] == 5


def test_mwe_scores_not_inflated_by_inverses_frequency():
    mwe_freqs = {1: 10, 2: 10, 3: 25}
    mwe_ids = {
        (11, 12, "label", "lemma", "tag", 0): 1,
        (12, 11, "label", "lemma", "tag", 1): 2,
        (11, 13, "label", "lemma2", "tag", 0): 3,
    }
    collocs = {
        11: Colloc(11, "", "", "", "", "", "_", 0, 45.0),
        12: Colloc(12, "", "", "", "", "", "_", 0, 20.0),
        13: Colloc(13, "", "", "", "", "", "_", 0, 25.0),
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        file = pathlib.Path(tmpdir) / "file"
        pro.compute_mwe_scores(file, mwe_ids, mwe_freqs, collocs, min_freq=4)
        with open(file) as fp:
            result = [
                round(float(line.strip().split()[-1]), 2) for line in fp.readlines()
            ]
    assert result == [12.3, 12.3, 13.51]


def test_mwe_inverse_extraction(testdata_dir):
    collocations = {
        1: Colloc(1, "ATTR", "Bekenntnis", "gemeinsam", "NOUN", "ADJ", "_", 0, 10.0),
        3: Colloc(3, "PP", "Bekenntnis", "Freiheit", "NOUN", "NOUN", "zu", 0, 10.0),
        4: Colloc(4, "KON", "Freiheit", "Menschenrecht", "NOUN", "NOUN", "_", 0, 10.0),
        5: Colloc(
            5, "ATTR", "Menschenrecht", "unveräußerlich", "NOUN", "ADJ", "_", 0, 10.0
        ),
        6: Colloc(6, "SUBJA", "verbinden", "Bekenntnis", "VERB", "NOUN", "_", 0, 10.0),
        7: Colloc(7, "ATTR", "Schritt", "erst", "NOUN", "ADJ", "_", 0, 10.0),
        8: Colloc(8, "OBJ", "machen", "Schritt", "VERB", "NOUN", "_", 0, 10.0),
    }

    matches_file = testdata_dir / "mwe_matches2"
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = pathlib.Path(tmpdir) / "file"
        mwe_ids, _ = pro.extract_mwe_from_collocs(
            matches_file, output_file, collocations
        )
    expected = {
        (1, 3, "PP", "Freiheit", "NOUN", 0),
        (1, 6, "SUBJA", "verbinden", "VERB", 1),
        (3, 1, "ATTR", "gemeinsam", "ADJ", 0),
        (3, 4, "KON", "Menschenrecht", "NOUN", 0),
        (3, 6, "SUBJA", "verbinden", "VERB", 1),
        (4, 3, "PP", "Bekenntnis", "NOUN", 1),
        (4, 5, "ATTR", "unveräußerlich", "ADJ", 0),
        (5, 4, "KON", "Freiheit", "NOUN", 0),
        (6, 1, "ATTR", "gemeinsam", "ADJ", 0),
        (6, 3, "PP", "Freiheit", "NOUN", 0),
        (7, 8, "OBJ", "machen", "VERB", 1),
        (8, 7, "ATTR", "erst", "ADJ", 0),
    }
    assert mwe_ids.keys() == expected


def test_mwe_not_inverted_if_KON_relation(testdata_dir):
    collocations = {
        10: Colloc(10, "ADV", "verletzen", "tödlich", "VERB", "ADJ", "_", 0, 10.0),
        11: Colloc(11, "KON", "rasen", "verletzen", "VERB", "VERB", "_", 0, 10.0),
        12: Colloc(12, "KON", "Bau", "Sanierung", "NOUN", "NOUN", "_", 0, 10.0),
        13: Colloc(13, "GMOD", "Sanierung", "Schule", "NOUN", "NOUN", "_", 0, 10.0),
    }

    matches_file = testdata_dir / "mwe_matches2"
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = pathlib.Path(tmpdir) / "file"
        mwe_ids, _ = pro.extract_mwe_from_collocs(
            matches_file, output_file, collocations
        )
    expected = {
        (10, 11, "KON", "rasen", "VERB", 0),
        (11, 10, "ADV", "tödlich", "ADJ", 0),
        (12, 13, "GMOD", "Schule", "NOUN", 0),
        (13, 12, "KON", "Bau", "NOUN", 0),
    }
    assert mwe_ids.keys() == expected


def test_filter_mwe_matches():
    mwe_matches = [(1, 2, 3), (2, 3, 44), (3, 43, 23), (4, 5, 3), (5, 23, 21)]
    mwe_freqs = {2: 2, 3: 10, 5: 3}
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(pathlib.Path(tmpdir) / "mwe_match_full", "w") as fh:
            for match in mwe_matches:
                print("\t".join(map(str, match)), file=fh)
        pro.filter_mwe_matches(tmpdir, mwe_freqs)
        files = [p.name for p in pathlib.Path(tmpdir).iterdir()]
        assert "mwe_match" in files
        with open(pathlib.Path(tmpdir) / "mwe_match") as fh:
            final_ids = []
            for line in fh:
                mwe_id = line.strip().split("\t")[0]
                final_ids.append(mwe_id)
        assert final_ids == ["2", "3", "5"]


def test_extract_collocations(testdata_dir):
    matches_file = testdata_dir / "matches_pp"
    with tempfile.TemporaryDirectory() as tmpdir:
        collocations_file = pathlib.Path(tmpdir) / "collocations"
        pro.extract_collocations(matches_file, collocations_file)
        with open(collocations_file) as fh:
            data = {tuple(line.strip().split("\t")) for line in fh}
    assert data == {
        ("ATTR", "Familienpolitik", "NOUN", "modern", "ADJ", "_", "1"),
        ("PP", "Gast", "NOUN", "Bundestreffen", "NOUN", "bei", "1"),
    }


def test_extract_most_common_surface(testdata_dir):
    matches_file = testdata_dir / "matches_pp"
    with tempfile.TemporaryDirectory() as tmpdir:
        types_file = pathlib.Path(tmpdir) / "types"
        pro.extract_most_common_surface(matches_file, types_file)
        with open(types_file) as fh:
            data = {tuple(line.strip().split("\t")) for line in fh}
    assert data == {
        ("Gast", "NOUN", "Gast", "1"),
        ("Familienpolitik", "NOUN", "Familienpolitik", "1"),
        ("Bundestreffen", "NOUN", "Bundestreffen", "1"),
        ("modern", "ADJ", "moderne", "1"),
    }


def test_pp_collocations_with_same_lemmas_and_different_prep_counted_separately():
    collocations = {
        1: Colloc(1, "PP", "Buch", "Tisch", "NOUN", "NOUN", "auf", 0, 10.0),
        2: Colloc(2, "PP", "Buch", "Tisch", "NOUN", "NOUN", "neben", 0, 20.0),
        3: Colloc(3, "PP", "Buch", "Tisch", "NOUN", "NOUN", "unter", 0, 30.0),
    }
    lemma_frequencies = {("Buch", "NOUN"): 60, ("Tisch", "NOUN"): 60}
    with tempfile.TemporaryDirectory() as tmpdir:
        file = pathlib.Path(tmpdir) / "file"
        pro.compute_collocation_scores(file, collocations, lemma_frequencies)
        with open(file) as fp:
            result = {round(float(line.split("\t")[-1]), 1) for line in fp}
            assert result == {11.4, 12.4, 13.0}


def test_prepositions_written_to_file_with_collocation_scores():
    collocations = {
        1: Colloc(1, "PP", "Buch", "Tisch", "NOUN", "NOUN", "auf", 0, 10.0),
    }
    lemma_freqs = {("Buch", "NOUN"): 10, ("Tisch", "NOUN"): 10}
    with tempfile.TemporaryDirectory() as tmpdir:
        file = pathlib.Path(tmpdir) / "file"
        pro.compute_collocation_scores(file, collocations, lemma_freqs)
        with open(file) as fp:
            result = [line.strip().split("\t") for line in fp]
    assert result == [
        ["1", "PP", "Buch", "Tisch", "NOUN", "NOUN", "auf", "0", "10.0", "14.0"],
    ]


def test_lemma_counter_filled(conll_sentences):
    file_reader_queue = MockQueue()
    file_reader_queue.put(conll_sentences)
    db_files_queue = MockQueue()
    db_sents_queue = MockQueue()
    db_matches_queue = MockQueue()
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = mp.Manager()
        lemma_counters = manager.list()
        pro.process_doc_file(
            file_reader_queue,
            db_files_queue,
            db_sents_queue,
            db_matches_queue,
            lemma_counters,
        )
    lemma_counter = lemma_counters[0]
    assert dict(lemma_counter.freqs) == {
        "sehr\tADV": 2,
        "geehrt\tADJ": 1,
        "Herr\tNOUN": 2,
        "Präsident\tNOUN": 1,
        "verehrt\tADJ": 1,
        "Dame\tNOUN": 1,
        "gehen\tVERB": 1,
        "ganz\tADJ": 1,
        "Epoche\tNOUN": 1,
        "Ende\tNOUN": 1,
        "neu\tADJ": 1,
        "Zeit\tNOUN": 1,
        "damals\tADV": 1,
        "beginnen\tVERB": 1,
    }


def test_irrelevant_tags_discarded_for_lemma_count():
    parses = [
        [
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
        ],
        [
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
                idx=2,
                surface="die",
                lemma="d",
                tag="DET",
                head=3,
                rel="det",
                misc=True,
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
                idx=4,
                surface="ist",
                lemma="sein",
                tag="AUX",
                head=8,
                rel="cop",
                misc=True,
            ),
            WPToken(
                idx=5,
                surface="der",
                lemma="d",
                tag="DET",
                head=8,
                rel="det",
                misc=True,
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
        ],
        [
            WPToken(
                idx=8,
                surface="denkbar",
                lemma="denkbar",
                tag="ADJ",
                head=0,
                rel="ROOT",
                misc=False,
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
                idx=6,
                surface="Test",
                lemma="Test",
                tag="NOUN",
                head=8,
                rel="nsubj",
                misc=True,
            ),
            WPToken(
                idx=7,
                surface="2024",
                lemma="2024",
                tag="NUM",
                head=8,
                rel="nmod",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="sich",
                lemma="sich",
                tag="PRON",
                head=8,
                rel="",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface=".",
                lemma=".",
                tag="PUNCT",
                head=8,
                rel="",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="unter",
                lemma="unter",
                tag="ADP",
                head=8,
                rel="",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="als",
                lemma="als",
                tag="CCONJ",
                head=8,
                rel="",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="dass",
                lemma="dass",
                tag="SCONJ",
                head=8,
                rel="mark",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="sans",
                lemma="sans",
                tag="X",
                head=8,
                rel="flat",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="zu",
                lemma="zu",
                tag="PART",
                head=8,
                rel="mark",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="bitte",
                lemma="bitte",
                tag="INTJ",
                head=8,
                rel="",
                misc=True,
            ),
            WPToken(
                idx=6,
                surface="Tussauds",
                lemma="Tussauds",
                tag="PROPN",
                head=8,
                rel="nsubj",
                misc=True,
            ),
        ],
    ]
    counter = pro.LemmaCounter()
    counter.count_token(parses)
    result = {(key, freq) for key, freq in counter.freqs.items()}
    assert result == {
        ("Maßlosigkeit\tNOUN", 1),
        ("sein\tAUX", 2),
        ("Folge\tNOUN", 1),
        ("Entwicklung\tNOUN", 1),
        ("Tag\tNOUN", 2),
        ("Test\tNOUN", 1),
        ("denkbar\tADJ", 3),
    }


def test_lemma_counts_written_to_file():
    def fill_queue(shared_list):
        parses = [
            [
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
            ],
            [
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
                    idx=2,
                    surface="die",
                    lemma="d",
                    tag="DET",
                    head=3,
                    rel="det",
                    misc=True,
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
                    idx=4,
                    surface="ist",
                    lemma="sein",
                    tag="AUX",
                    head=8,
                    rel="cop",
                    misc=True,
                ),
                WPToken(
                    idx=5,
                    surface="der",
                    lemma="d",
                    tag="DET",
                    head=8,
                    rel="det",
                    misc=True,
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
            ],
            [
                WPToken(
                    idx=8,
                    surface="denkbar",
                    lemma="denkbar",
                    tag="ADJ",
                    head=0,
                    rel="ROOT",
                    misc=False,
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
                    idx=6,
                    surface="Test",
                    lemma="Test",
                    tag="NOUN",
                    head=8,
                    rel="nsubj",
                    misc=True,
                ),
            ],
        ]
        counter = pro.LemmaCounter()
        counter.count_token(parses)
        shared_list.append(counter)

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = mp.Manager()
        shared_list = manager.list()
        proc = mp.Process(target=fill_queue, args=(shared_list,))
        proc.start()
        proc.join()
        pro.save_lemma_counts_to_file(shared_list, pathlib.Path(tmpdir))
        with open(pathlib.Path(tmpdir) / "lemma_freqs") as fh:
            result = fh.readlines()
        assert "Maßlosigkeit\tNOUN\t1\n" in result


def test_counting_lemma_multiple_processes():
    def fill_queue(shared_list):
        parses = [
            [
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
        ]
        counter = pro.LemmaCounter()
        counter.count_token(parses)
        shared_list.append(counter)

    def fill_queue2(shared_list):
        parses = [
            [
                WPToken(
                    idx=8,
                    surface="denkbar",
                    lemma="denkbar",
                    tag="ADJ",
                    head=0,
                    rel="ROOT",
                    misc=False,
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
                    idx=6,
                    surface="Test",
                    lemma="Test",
                    tag="NOUN",
                    head=8,
                    rel="nsubj",
                    misc=True,
                ),
            ]
        ]
        counter = pro.LemmaCounter()
        counter.count_token(parses)
        shared_list.append(counter)

    with tempfile.TemporaryDirectory() as tmpdir:
        counters = mp.Manager().list()
        proc1 = mp.Process(target=fill_queue, args=(counters,))
        proc2 = mp.Process(target=fill_queue2, args=(counters,))
        proc2.start()
        proc1.start()
        proc1.join()
        proc2.join()
        pro.save_lemma_counts_to_file(counters, pathlib.Path(tmpdir))
        with open(pathlib.Path(tmpdir) / "lemma_freqs") as fh:
            result = {tuple(line.strip().split("\t")) for line in fh}
        assert result == {
            ("Maßlosigkeit", "NOUN", "1"),
            ("sein", "AUX", "1"),
            ("denkbar", "ADJ", "3"),
            ("Tag", "NOUN", "1"),
            ("Test", "NOUN", "1"),
        }


def test_lemma_frequency_aggregation_one_file(testdata_dir):
    result = pro.aggregate_lemma_frequencies([testdata_dir / "lemma_freqs"])
    assert result == {
        ("Maßlosigkeit", "NOUN"): 1,
        ("sein", "AUX"): 2,
        ("denkbar", "ADJ"): 3,
        ("Tag", "NOUN"): 1,
        ("Schiff", "NOUN"): 3,
        ("neu", "ADJ"): 10,
    }


def test_lemma_frequency_aggregation_multiple_files(testdata_dir):
    result = pro.aggregate_lemma_frequencies(
        [
            testdata_dir / "l_freqs" / "f1",
            testdata_dir / "l_freqs" / "f2",
            testdata_dir / "l_freqs" / "f3",
        ]
    )
    assert result == {
        ("Arbeit", "NOUN"): 7,
        ("Ferien", "NOUN"): 5,
        ("geistig", "ADJ"): 2,
        ("suchen", "VERB"): 18,
        ("Hilfe", "NOUN"): 3,
        ("einigermaßen", "ADV"): 4,
        ("schön", "ADJ"): 10,
        ("bauen", "VERB"): 23,
        ("weich", "ADJ"): 3,
        ("Zeitung", "NOUN"): 7,
    }


def test_compute_token_stats_result_written_to_file(testdata_dir):
    lemma_freqs = {
        ("Richtung", "NOUN"): 10,
        ("Passagier", "NOUN"): 12,
        ("Fahrgast", "NOUN"): 15,
        ("starten", "VERB"): 30,
        ("bieten", "VERB"): 40,
        ("neu", "ADJ"): 15,
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        pro.compute_token_statistics(
            [testdata_dir / "type_freqs"], pathlib.Path(tmpdir) / "output", lemma_freqs
        )
        with open(pathlib.Path(tmpdir) / "output") as fh:
            data = [tuple(line.strip().split("\t")) for line in fh]
    assert data == [
        ("Richtung", "NOUN", "10", "Richtung", "5"),
        ("Passagier", "NOUN", "12", "Passagiere", "10"),
        ("Fahrgast", "NOUN", "15", "Fahrgäste", "11"),
        ("starten", "VERB", "30", "startet", "20"),
        ("bieten", "VERB", "40", "bietet", "31"),
        ("neu", "ADJ", "15", "neue", "10"),
    ]


def test_type_with_preposition_mapped_to_correct_token(testdata_dir):
    lemma_freqs = {
        ("Schule", "NOUN"): 20,
        ("Schiff", "NOUN"): 10,
        ("stellen", "VERB"): 10,
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        pro.compute_token_statistics(
            [testdata_dir / "type_freqs"], pathlib.Path(tmpdir) / "output", lemma_freqs
        )
        with open(pathlib.Path(tmpdir) / "output") as fh:
            data = [tuple(line.strip().split("\t")) for line in fh]
    assert data == [
        ("Schule", "NOUN", "20", "in Schule", "3"),
        ("Schiff", "NOUN", "10", "mit Schiff", "5"),
        ("stellen", "VERB", "10", "stellen nach", "5"),
    ]


def test_lemmata_filtered_for_min_frequency_in_token_stats(testdata_dir):
    lemma_freqs = {
        ("Schule", "NOUN"): 3,
        ("Richtung", "NOUN"): 10,
        ("stellen", "VERB"): 10,
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        pro.compute_token_statistics(
            [testdata_dir / "type_freqs"],
            pathlib.Path(tmpdir) / "output",
            lemma_freqs,
            min_freq=4,
        )
        with open(pathlib.Path(tmpdir) / "output") as fh:
            data = [tuple(line.strip().split("\t")) for line in fh]
    assert data == [
        ("Richtung", "NOUN", "10", "Richtung", "5"),
        ("stellen", "VERB", "10", "stellen nach", "5"),
    ]


def test_reindex_filter_concordances(testdata_dir):
    input_files = [
        testdata_dir / "concord_sentences",
        testdata_dir / "concord_sentences2",
    ]
    file_ids = {"file1": 1, "file2": 2, "file3": 3, "file4": 4}
    with tempfile.TemporaryDirectory() as tmpdir:
        directory = pathlib.Path(tmpdir)
        result = pro.reindex_concordances(
            input_files,
            directory / "output_file",
            file_ids,
            directory / "duplicates",
        )
        with open(directory / "duplicates") as fh:
            duplicate_sents = fh.readlines()
        with open(directory / "output_file") as fh:
            sents = fh.readlines()
    assert len(result) == len(sents) == 36
    assert len(duplicate_sents) == 4
    assert duplicate_sents[0] == "file2\t5\thabe\x01angenommen\n"
    assert sents[0] == "1\t0\tsiebzig\x01siebzig\n"


def test_reindex_corpus_files(testdata_dir):
    input_files = [testdata_dir / "cf1", testdata_dir / "cf2", testdata_dir / "cf3"]
    with tempfile.TemporaryDirectory() as tmpdir:
        result = pro.reindex_corpus_files(input_files, pathlib.Path(tmpdir) / "docs")
        with open(pathlib.Path(tmpdir) / "docs") as fh:
            files = fh.readlines()
    assert files[0] == "0\tcorpus\tfile0\tQuelle\t2024-01-01\tcorpus\n"
    assert files[-1] == "14\tcorpus3\tfile4\tQuelle\t2024-01-01\tcorpus3\n"
    assert len(result) == len(files) == 15
    assert {
        ("corpus/file1", 1),
        ("corpus2/file3", 8),
        ("corpus3/file2", 12),
    }.issubset(result.items())


def test_sentence_initial_particle_of_phrasal_verbs_normalized():
    sentence = [
        WPToken(
            idx=1,
            surface="Hinzu",
            lemma="hinzu",
            tag="ADP",
            head=2,
            rel="compound:prt",
            misc=True,
        ),
        WPToken(
            idx=2,
            surface="kommen",
            lemma="kommen",
            tag="VERB",
            head=0,
            rel="ROOT",
            misc=True,
        ),
        WPToken(
            idx=3,
            surface="unerklärliche",
            lemma="unerklärlich",
            tag="ADJ",
            head=4,
            rel="amod",
            misc=True,
        ),
        WPToken(
            idx=4,
            surface="Gliederschmerzen",
            lemma="Gliederschmerz",
            tag="NOUN",
            head=2,
            rel="nsuj",
            misc=True,
        ),
    ]
    pro.collapse_phrasal_verbs(sentence)
    assert sentence[1] == WPToken(
        idx=2,
        surface="kommen",
        lemma="hinzukommen",
        tag="VERB",
        head=0,
        rel="ROOT",
        misc=True,
        prt_pos=1,
    )


def test_collocations_with_invalid_id_removed():
    collocations = {
        1: Colloc(1, "PP", "Buch", "Tisch", "NOUN", "NOUN", "auf", 0, 10.0),
        2: Colloc(2, "PP", "Buch", "Boden", "NOUN", "NOUN", "neben", 0, 20.0),
        3: Colloc(3, "PP", "Buch", "Regal", "NOUN", "NOUN", "unter", 0, 30.0),
    }
    invalid_ids = {1}
    filtered_collocs = pro.filter_invalid_collocations(collocations, invalid_ids)
    assert len(filtered_collocs) == 2
    assert 1 not in filtered_collocs


def test_collocations_with_negative_logDice_not_written_to_file():
    collocations = {
        1: Colloc(1, "PP", "Buch", "Tisch", "NOUN", "NOUN", "auf", 0, 10.0),
        2: Colloc(2, "PP", "Buch", "Boden", "NOUN", "NOUN", "neben", 0, 5.0),
        3: Colloc(3, "PP", "Buch", "Regal", "NOUN", "NOUN", "unter", 0, 300.0),
    }
    lemma_freqs = {
        ("Buch", "NOUN"): 70000,
        ("Tisch", "NOUN"): 300000,
        ("Boden", "NOUN"): 100000,
        ("Regal", "NOUN"): 330,
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        file = pathlib.Path(tmpdir) / "file"
        pro.compute_collocation_scores(file, collocations, lemma_freqs)
        with open(file) as fp:
            result = [int(line.split("\t")[0]) for line in fp]
    assert result == [3]


def test_ids_for_collocations_with_negative_logDice_returned():
    collocations = {
        1: Colloc(1, "PP", "Buch", "Tisch", "NOUN", "NOUN", "auf", 0, 10.0),
        2: Colloc(2, "PP", "Buch", "Boden", "NOUN", "NOUN", "neben", 0, 5.0),
        3: Colloc(3, "PP", "Buch", "Regal", "NOUN", "NOUN", "unter", 0, 300.0),
    }
    lemma_freqs = {
        ("Buch", "NOUN"): 70000,
        ("Tisch", "NOUN"): 300000,
        ("Boden", "NOUN"): 100000,
        ("Regal", "NOUN"): 330,
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        file = pathlib.Path(tmpdir) / "file"
        invalid_ids = pro.compute_collocation_scores(file, collocations, lemma_freqs)
    assert invalid_ids == {1, 2}


def test_match_processing_returns_index_of_valid_concordances(testdata_dir):
    collocations = {
        1: Colloc(
            id=1,
            label="ATTR",
            lemma1="Familienpolitik",
            lemma2="modern",
            lemma1_tag="NOUN",
            lemma2_tag="ADJ",
            prep="_",
            inv=0,
            frequency=12,
        )
    }
    corpus_file_ids = {"doc1": 1}
    sentence_ids = {("1", "3"), ("1", "4")}
    matches_dir = testdata_dir / "matches_agg"
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = pathlib.Path(tmpdir) / "file"
        result = pro.filter_transform_matches(
            list(matches_dir.iterdir()),
            output_file,
            corpus_file_ids,
            sentence_ids,
            collocations,
        )
    assert result == {("1", "4")}


def test_invalid_concordances_removed():
    valid_sentence_ids = {("0", "1"), ("0", "2"), ("2", "1")}
    sentence_data = [
        (0, 1, "sent1"),
        (0, 2, "sent2"),
        (1, 1, "sent3"),
        (1, 2, "sent4"),
        (2, 1, "sent5"),
        (3, 1, "sent6"),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        directory = pathlib.Path(tmpdir)
        with open(directory / "tmp_sents", "w") as fh:
            for sent in sentence_data:
                print("\t".join(map(str, sent)), file=fh)
        pro.filter_concordances(
            directory / "tmp_sents", directory / "final_sents", valid_sentence_ids
        )
        with open(directory / "final_sents") as fh:
            result = [line.strip().split("\t") for line in fh]
        assert result == [["0", "1", "sent1"], ["0", "2", "sent2"], ["2", "1", "sent5"]]


def test_unnecessary_corpus_files_removed():
    valid_sentence_ids = {("0", "1"), ("1", "2"), ("4", "1")}
    doc_data = [
        ("0", "corpus1", "file1", "bibl", "date", "corpus1"),
        ("1", "corpus1", "file2", "bibl", "date", "corpus1"),
        ("2", "corpus1", "file3", "bibl", "date", "corpus1"),
        ("3", "corpus2", "file4", "bibl", "date", "corpus2"),
        ("4", "corpus2", "file5", "bibl", "date", "corpus2"),
        ("5", "corpus3", "file6", "bibl", "date", "corpus3"),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        directory = pathlib.Path(tmpdir)
        with open(directory / "tmp_files", "w") as fh:
            for doc in doc_data:
                print("\t".join(doc), file=fh)
        pro.filter_corpus_files(
            directory / "tmp_files", directory / "final_files", valid_sentence_ids
        )
        with open(directory / "final_files") as fh:
            result = [line.strip().split("\t") for line in fh]
        assert result == [
            ["0", "corpus1", "file1", "bibl", "date", "corpus1"],
            ["1", "corpus1", "file2", "bibl", "date", "corpus1"],
            ["4", "corpus2", "file5", "bibl", "date", "corpus2"],
        ]
