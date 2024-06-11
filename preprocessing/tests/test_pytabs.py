import unittest
from pathlib import Path

from preprocessing.pytabs.tabs import ConllToken, TabsDocument, TabsSentence


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

    def test_cleaning_also_applied_to_lemma(self):
        doc = TabsDocument.from_tabs(self.to_clean)
        sent = doc.sentences[1]
        self.assertEqual(sent.tokens[1], ("trägt", "VAFIN", "tragen", "1"))


class TabsSentenceTest(unittest.TestCase):
    def test_space_information_before_last_punctuation_mark_set_correctly(self):
        sent = TabsSentence(
            [],
            [
                ("Sehr", "ADV", "sehr", "1"),
                ("geehrter", "ADJA", "geehrt", "1"),
                ("Herr", "NN", "Herr", "1"),
                ("Präsident", "NN", "Präsident", "1"),
                ("Palinkás", "NE", "Palinkás", "1"),
                (",", "$,", ",", "0"),
                ("meine", "PPOSAT", "meine", "1"),
                ("sehr", "ADV", "sehr", "1"),
                ("verehrten", "ADJA", "verehrt", "1"),
                ("Damen", "NN", "Dame", "1"),
                ("und", "KON", "und", "1"),
                ("Herren", "NN", "Herr", "1"),
                (",", "$,", ",", "0"),
            ],
        )
        result = sent.to_conll({"Token": 0, "Lemma": 1, "Pos": 2, "WordSep": 3})
        expected = [
            ConllToken("Sehr", "ADV", "sehr", "", "_", "_", "_"),
            ConllToken("geehrter", "ADJA", "geehrt", "", "_", "_", "_"),
            ConllToken("Herr", "NN", "Herr", "", "_", "_", "_"),
            ConllToken("Präsident", "NN", "Präsident", "", "_", "_", "_"),
            ConllToken("Palinkás", "NE", "Palinkás", "", "_", "_", "SpaceAfter=No"),
            ConllToken(",", "$,", ",", "", "_", "_", "_"),
            ConllToken("meine", "PPOSAT", "meine", "", "_", "_", "_"),
            ConllToken("sehr", "ADV", "sehr", "", "_", "_", "_"),
            ConllToken("verehrten", "ADJA", "verehrt", "", "_", "_", "_"),
            ConllToken("Damen", "NN", "Dame", "", "_", "_", "_"),
            ConllToken("und", "KON", "und", "", "_", "_", "_"),
            ConllToken("Herren", "NN", "Herr", "", "_", "_", "SpaceAfter=No"),
            ConllToken(",", "$,", ",", "", "_", "_", "_"),
        ]
        self.assertEqual(result, expected)

    def test_space_before_last_token_set_if_needed(self):
        sent = TabsSentence(
            [],
            [
                ("Sehr", "ADV", "sehr", "1"),
                ("geehrter", "ADJA", "geehrt", "1"),
                ("Herr", "NN", "Herr", "1"),
                ("Präsident", "NN", "Präsident", "1"),
                ("Palinkás", "NE", "Palinkás", "1"),
                (",", "$,", ",", "0"),
                ("meine", "PPOSAT", "meine", "1"),
                ("sehr", "ADV", "sehr", "1"),
                ("verehrten", "ADJA", "verehrt", "1"),
                ("Damen", "NN", "Dame", "1"),
                ("und", "KON", "und", "1"),
                ("Herren", "NN", "Herr", "1"),
                (",", "$,", ",", "1"),
            ],
        )
        result = sent.to_conll({"Token": 0, "Lemma": 1, "Pos": 2, "WordSep": 3})
        expected = [
            ConllToken("Sehr", "ADV", "sehr", "", "_", "_", "_"),
            ConllToken("geehrter", "ADJA", "geehrt", "", "_", "_", "_"),
            ConllToken("Herr", "NN", "Herr", "", "_", "_", "_"),
            ConllToken("Präsident", "NN", "Präsident", "", "_", "_", "_"),
            ConllToken("Palinkás", "NE", "Palinkás", "", "_", "_", "SpaceAfter=No"),
            ConllToken(",", "$,", ",", "", "_", "_", "_"),
            ConllToken("meine", "PPOSAT", "meine", "", "_", "_", "_"),
            ConllToken("sehr", "ADV", "sehr", "", "_", "_", "_"),
            ConllToken("verehrten", "ADJA", "verehrt", "", "_", "_", "_"),
            ConllToken("Damen", "NN", "Dame", "", "_", "_", "_"),
            ConllToken("und", "KON", "und", "", "_", "_", "_"),
            ConllToken("Herren", "NN", "Herr", "", "_", "_", "_"),
            ConllToken(",", "$,", ",", "", "_", "_", "_"),
        ]
        self.assertEqual(result, expected)

    def test_xml_fragment_removed_from_token(self):
        sent = TabsSentence(
            [],
            [
                ("fett>Sehr", "ADV", "fett>sehr", "1"),
                ("verehrten", "ADJA", "verehrt", "1"),
                ("Damen", "NN", "Dame", "1"),
                ("und", "KON", "und", "1"),
                ("Herren</fett>", "NN", "Herr</fett>", "1"),
                ("fett>", "NN", "fett>", "1"),
            ],
        )
        expected = ["Sehr", "verehrten", "Damen", "und", "Herren"]
        self.assertEqual([tok[0] for tok in sent.tokens], expected)

    def test_xml_fragment_removed_from_lemma(self):
        sent = TabsSentence(
            [],
            [
                ("fett>Sehr", "ADV", "fett>sehr", "1"),
                ("verehrten</", "ADJA", "verehrt</", "1"),
                ("Damen", "NN", "Dame", "1"),
                ("und</", "KON", "</", "1"),
                ("Herren</fett>", "NN", "Herr</fett>", "1"),
            ],
        )
        expected = ["sehr", "verehrt", "Dame", "und", "Herr"]
        result = [token[2] for token in sent.tokens]
        self.assertEqual(result, expected)
