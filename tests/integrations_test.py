import os
import tempfile

import preprocessing.cli.annotate_deprel as ad
import wordprofile.cli.compute_statistics as cs
import wordprofile.cli.extract_collocations as ec
from preprocessing.pytabs.tabs import TabsDocument


def main():
    with tempfile.TemporaryDirectory() as tmp_dir:
        convert(tmp_dir)
        annotate_dependency_relations(tmp_dir)
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


def annotate_dependency_relations(tmp_dir):
    ad.main(
        [
            "-i",
            os.path.join(tmp_dir, "data.orig.conll"),
            "-o",
            os.path.join(tmp_dir, "data.anno.conll"),
            "-m",
            "de_dwds_dep_hdt_lg",
        ],
        standalone_mode=False,
    )
    assert "data.anno.conll" in os.listdir(tmp_dir)
    with open(os.path.join(tmp_dir, "data.anno.conll")) as fh:
        lines = fh.readlines()
    assert lines != []


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
            "zurückholen für",
            "für Übernahme",
        }


def check_matches_stats(tmp_dir):
    with open(os.path.join(tmp_dir, "stats", "matches")) as fh:
        lines = fh.readlines()
        lemma_pairs = {tuple(line.split("\t")[2:4]) for line in lines}
        assert lemma_pairs == {
            ("gestalten", "Demokratie"),
            ("holt Für", "Übernahme"),
            ("holt", "Für Übernahme"),
            ("Übernahme", "heikle"),
            ("holt", "Chef"),
            ("Übernahme", "Skandalbank"),
            ("Chef", "früheren"),
            ("Chef", "früherer"),
        }


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
    assert mwe_collocations == {
        ("2", "3", "GMOD", "Skandalbank", "NOUN", "0", "2"),
        ("3", "2", "ATTR", "heikel", "ADJ", "0", "2"),
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
    main()
