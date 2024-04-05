import unittest
from pathlib import Path

from preprocessing.pytabs.tabs import TabsDocument


class TabsDocumentTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(__file__).parent / "testdata"
        self.to_clean = self.test_dir / "to_clean.tabs"

    def test_tabs2conllu(self):
        expected = (self.test_dir / "sample.conllu").read_text()
        doc = TabsDocument.from_tabs((self.test_dir / "sample.tabs"))
        self.assertEqual(expected, doc.as_conllu())

    def test_xml_fragment_removed_from_token(self):
        doc = TabsDocument.from_tabs(self.to_clean.as_posix())
        for sent in doc.sentences:
            with self.subTest():
                res = [
                    "<" in "".join(tok[:3:2]) or ">" in "".join(tok[:3:2])
                    for tok in sent.tokens
                ]
                self.assertFalse(any(res))

    def test_partial_xml_fragmet_removed_leading(self):
        doc = TabsDocument.from_tabs(self.to_clean)
        sent = doc.sentences[-1]
        expected = ("Schaden", "NN", "Schaden", "1")
        self.assertTrue(expected in sent.tokens)

    def test_partial_xml_fragmet_removed_following(self):
        doc = TabsDocument.from_tabs(self.to_clean)
        sent = doc.sentences[0]
        expected = ("Buschmann", "FM", "Buschmann", "1")
        self.assertTrue(expected in sent.tokens)

    def test_xml_fragment_removed_from_punctuation(self):
        doc = TabsDocument.from_tabs(self.to_clean)
        sent = doc.sentences[-1]
        self.assertEqual(sent.tokens[-1], ("?", "$.", "?", "0"))

    def test_xml_token_removed_if_empty_after_cleaning(self):
        doc = TabsDocument.from_tabs(self.to_clean)
        sent = doc.sentences[0]
        self.assertEqual(len(sent.tokens), 20)
        self.assertEqual(sent.tokens[0][0], "Bundesjustizminister")

    def test_conll_serialization(self):
        doc = TabsDocument.from_tabs(self.to_clean)
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
