import unittest
from pathlib import Path

from preprocessing.pytabs.tabs import TabsDocument

test_dir = (Path(__file__) / "..").resolve()
sample_tabs_file = test_dir / "testdata" / "sample.tabs"
sample_conllu_file = test_dir / "testdata" / "sample.conllu"


def test_tabs2conllu():
    expected = sample_conllu_file.read_text()
    doc = TabsDocument.from_tabs(sample_tabs_file.as_posix())
    assert expected == doc.as_conllu()


class TabsDocumentTest(unittest.TestCase):
    def setUp(self):
        self.tabs_file = test_dir / "testdata" / "to_clean.tabs"

    def test_xml_fragment_removed_from_token(self):
        doc = TabsDocument.from_tabs(self.tabs_file.as_posix())
        for sent in doc.sentences:
            with self.subTest():
                res = [
                    "<" in "".join(tok[:3:2]) or ">" in "".join(tok[:3:2])
                    for tok in sent.tokens
                ]
                self.assertFalse(any(res))

    def test_partial_xml_fragmet_removed_leading(self):
        doc = TabsDocument.from_tabs(self.tabs_file.as_posix())
        sent = doc.sentences[-1]
        expected = ("Schaden", "NN", "Schaden", "1")
        self.assertTrue(expected in sent.tokens)

    def test_partial_xml_fragmet_removed_following(self):
        doc = TabsDocument.from_tabs(self.tabs_file.as_posix())
        sent = doc.sentences[0]
        expected = ("Buschmann", "FM", "Buschmann", "1")
        self.assertTrue(expected in sent.tokens)

    def test_xml_fragment_removed_from_punctuation(self):
        doc = TabsDocument.from_tabs(self.tabs_file.as_posix())
        sent = doc.sentences[-1]
        self.assertEqual(sent.tokens[-1], ("?", "$.", "?", "0"))

    def test_xml_token_removed_if_empty_after_cleaning(self):
        doc = TabsDocument.from_tabs(self.tabs_file.as_posix())
        sent = doc.sentences[0]
        self.assertEqual(len(sent.tokens), 20)
        self.assertEqual(sent.tokens[0][0], "Bundesjustizminister")

    def test_conll_serialization(self):
        doc = TabsDocument.from_tabs(self.tabs_file.as_posix())
        expected = [
            "# text = Bundesjustizminister Marco Buschmann ( FDP ) überreichte "
            "dem 62-Jährigen gestern die Ernennungsurkunde , wie das Ministerium "
            "in Berlin mitteilte .",
            "# text = Stadt trägt nur die",
            "# text = Schaden an Demokratie ?",
        ]
        result = []
        for line in doc.as_conllu().split("\n"):
            if line.startswith("# text"):
                result.append(line)
        self.assertEqual(result, expected)
