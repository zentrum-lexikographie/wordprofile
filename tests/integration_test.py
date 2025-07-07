import os
import shutil
import tempfile

import conllu
import huggingface_hub

import wordprofile.cli.compute_statistics as cs
import wordprofile.cli.extract_collocations as ec
import wordprofile.preprocessing.cli.annotate as ann
from wordprofile.preprocessing.pytabs.tabs import TabsDocument


def test_integration():
    with tempfile.TemporaryDirectory() as tmp_dir:
        if huggingface_hub.repo_exists("zentrum-lexikographie/dwdsmor-dwds"):
            convert(tmp_dir)
            annotate(tmp_dir)
        else:
            shutil.copyfile(
                os.path.join("tests", "testdata", "data.anno.conll"),
                os.path.join(tmp_dir, "data.anno.conll"),
            )
        extract_collocation(tmp_dir)
        compute_statistics(tmp_dir)
        compute_statistics_with_mwe(tmp_dir)
        mwe_filtering(tmp_dir)


def convert(tmp_dir):
    doc = TabsDocument.from_tabs(
        os.path.join("tests", "testdata", "int_test_data.tabs")
    )
    assert doc.sentences != []
    with open(os.path.join(tmp_dir, "data.orig.conll"), "w") as fh:
        fh.write(doc.as_conllu())


def annotate(tmp_dir):
    ann.main(
        [
            "-i",
            os.path.join(tmp_dir, "data.orig.conll"),
            "-o",
            os.path.join(tmp_dir, "data.anno.conll"),
            "-f",
        ],
        standalone_mode=False,
    )
    assert "data.anno.conll" in os.listdir(tmp_dir)
    with open(os.path.join(tmp_dir, "data.anno.conll")) as fh:
        doc = conllu.parse(fh.read())
    assert doc[0][0]["deprel"] == "det"
    assert "NamedEntity" in doc[9][9]["misc"]
    assert doc[9][1]["lemma"] == "die"
    assert doc[9][8]["lemma"] == "zurückholen"


def extract_collocation(tmp_dir):
    ec.main(
        [
            "--input",
            os.path.join(
                tmp_dir,
                "data.anno.conll",
            ),
            "--dest",
            os.path.join(tmp_dir, "colloc", "corpus"),
        ]
    )
    assert sorted(os.listdir(os.path.join(tmp_dir, "colloc", "corpus"))) == [
        "collocations",
        "common_surfaces",
        "concord_sentences",
        "corpus_files",
        "lemma_freqs",
        "matches",
    ]
    check_matches(tmp_dir)
    check_sentences(tmp_dir)
    check_lemma_freqs(tmp_dir)


def check_lemma_freqs(tmp_dir):
    with open(os.path.join(tmp_dir, "colloc", "corpus", "lemma_freqs")) as fh:
        lemma_freqs = {tuple(line.strip().split("\t")) for line in fh}
        assert ("Zeit", "NOUN", "1") in lemma_freqs
        assert ("erinnern", "VERB", "3") in lemma_freqs
        assert ("heute", "ADV", "2") in lemma_freqs
        assert ("zurückholen", "VERB", "2") in lemma_freqs
    ec.main(
        [
            "--input",
            os.path.join(
                tmp_dir,
                "data.anno.conll",
            ),
            "--dest",
            os.path.join(tmp_dir, "colloc-j"),
            "--njobs",
            "10",
        ]
    )
    with open(os.path.join(tmp_dir, "colloc-j", "lemma_freqs")) as fh:
        lemma_freqs_j = {tuple(line.strip().split("\t")) for line in fh}
    assert lemma_freqs == lemma_freqs_j


def check_sentences(tmp_dir):
    with open(os.path.join(tmp_dir, "colloc", "corpus", "concord_sentences")) as fh:
        lines = fh.readlines()
        assert len(lines) == 16
        assert "fett>Sergio" not in "".join(lines)


def check_matches(tmp_dir):
    with open(os.path.join(tmp_dir, "colloc", "corpus", "matches")) as fh:
        data = fh.read()
        assert "UNESCO" not in data
        assert "DDR-Regierung" in data
        assert "Kopf-an-Kopf-Rennen" in data
        assert "Original-Dieboijer-Nachtwächter-Rundgang-Kartoffelsupp" not in data


def compute_statistics(tmp_dir):
    cs.main(
        [
            os.path.join(tmp_dir, "colloc", "corpus"),
            "--dest",
            os.path.join(tmp_dir, "stats"),
            "--min-rel-freq",
            "2",
        ]
    )
    assert sorted(os.listdir(os.path.join(tmp_dir, "stats"))) == [
        "collocations",
        "concord_sentences",
        "concord_sentences.duplicate",
        "corpus_files",
        "matches",
        "token_freqs",
    ]
    check_duplicates(tmp_dir)
    check_token_freqs(tmp_dir)
    check_matches_stats(tmp_dir)


def check_duplicates(tmp_dir):
    with open(os.path.join(tmp_dir, "stats", "concord_sentences.duplicate")) as fh:
        data = fh.readline()
        sentence_frag = "heikle\x02Übernahme\x02der\x02Skandalbank\x02Credit\x02Suisse\x02holt\x02UBS"
        assert "Podiumdiskussion.ddc.xml" in data
        assert sentence_frag in data


def check_token_freqs(tmp_dir):
    with open(os.path.join(tmp_dir, "stats", "token_freqs")) as fh:
        lines = fh.readlines()
        lemmata = {line.split("\t")[0] for line in lines}
        assert lemmata == {
            "Chef",
            "früh",
            "Übernahme",
            "heikel",
            "Skandalbank",
            "gestalten",
            "Demokratie",
            "zurückholen",
            "wie",
            "erinnern",
            "hier",
            "Mensch",
            "herzlich",
        }


def check_matches_stats(tmp_dir):
    with open(os.path.join(tmp_dir, "stats", "matches")) as fh:
        lines = fh.readlines()
        lemma_pairs = {tuple(line.split("\t")[2:4]) for line in lines}
        assert lemma_pairs == {
            ("gestalten", "Demokratie"),
            ("holt", "Übernahme"),
            ("Übernahme", "heikle"),
            ("holt", "Chef"),
            ("Übernahme", "Skandalbank"),
            ("Chef", "früheren"),
            ("Chef", "früherer"),
        }
        phrasal_matches = {
            tuple(line.split("\t")[2:7]) for line in lines if line.split("\t")[6] != "-"
        }
        assert ("holt", "Chef", "9", "13", "14") in phrasal_matches


def compute_statistics_with_mwe(tmp_dir):
    cs.main(
        [
            os.path.join(tmp_dir, "colloc", "corpus"),
            "--dest",
            os.path.join(tmp_dir, "stats_mwe"),
            "--min-rel-freq",
            "2",
            "--mwe",
        ]
    )
    assert "mwe" in os.listdir(os.path.join(tmp_dir, "stats_mwe"))
    check_mwe(tmp_dir)


def check_mwe(tmp_dir):
    with open(os.path.join(tmp_dir, "stats_mwe", "mwe")) as fh:
        lines = fh.readlines()
        mwe_collocations = {tuple(line.split("\t")[1:8]) for line in lines}
    with open(os.path.join(tmp_dir, "stats_mwe", "collocations")) as fh:
        lines = fh.readlines()
        collocations = {
            col[0]: col[1:4] for line in lines if (col := line.split("\t")[:4])
        }
    result = set()
    for mwe in mwe_collocations:
        _, w1, w2 = collocations[mwe[0]]
        result.add((w1, w2, *mwe[2:]))
    assert result == {
        ("Übernahme", "heikel", "GMOD", "Skandalbank", "NOUN", "0", "2"),
        ("Übernahme", "Skandalbank", "ATTR", "heikel", "ADJ", "0", "2"),
    }


def mwe_filtering(tmp_dir):
    cs.main(
        [
            os.path.join(tmp_dir, "colloc", "corpus"),
            "--dest",
            os.path.join(tmp_dir, "stats_mwe"),
            "--min-rel-freq",
            "3",
            "--mwe",
        ]
    )
    with open(os.path.join(tmp_dir, "stats_mwe", "mwe_match")) as fh:
        assert fh.read() == ""
    with open(os.path.join(tmp_dir, "stats_mwe", "mwe")) as fh:
        assert fh.read() == ""


if __name__ == "__main__":
    test_integration()
