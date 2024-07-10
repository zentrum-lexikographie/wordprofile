import os
import tempfile

import wordprofile.cli.compute_statistics as cs
import wordprofile.cli.extract_collocations as ec


def main():
    with tempfile.TemporaryDirectory() as tmp_dir:
        extract_collocation(tmp_dir)
        compute_statistics(tmp_dir)


def extract_collocation(tmp_dir):
    ec.main(
        [
            "--input",
            os.path.join(
                "tests",
                "testdata",
                "int_test_data.conll",
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
        "matches",
    ]
    check_matches(tmp_dir)
    check_sentences(tmp_dir)


def check_sentences(tmp_dir):
    with open(os.path.join(tmp_dir, "colloc", "corpus", "concord_sentences")) as fh:
        lines = fh.readlines()
        assert len(lines) == 15
        # assert "fett>Sergio" not in "".join(lines)


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
        assert "Podiumdiskussion.ddc.xml" in fh.readline()


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
            ("holt", "zurück"),
            ("Übernahme", "Skandalbank"),
        }


if __name__ == "__main__":
    main()
