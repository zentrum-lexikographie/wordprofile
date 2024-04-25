import datetime
import unittest


from wordprofile.datatypes import Concordance, Coocc, LemmaInfo
from wordprofile.wp import Wordprofile


class MockDb:
    def __init__(self):
        self.coocc = {
            -1: Coocc(
                id=-1,
                rel="SUBJA",
                lemma1="Feuerwehr",
                lemma2="rücken",
                form1="Feuerwehr",
                form2="rückt",
                tag1="NOUN",
                tag2="VERB",
                freq=25,
                score=8.484615325927734,
                inverse=1,
                has_mwe=1,
                num_concords=25,
            ),
            2: Coocc(
                id=2,
                rel="GMOD",
                lemma1="Feuerwehr",
                lemma2="Umgebung",
                form1="Feuerwehr",
                form2="Umgebung",
                tag1="NOUN",
                tag2="NOUN",
                freq=1,
                score=4.772384166717529,
                inverse=0,
                has_mwe=1,
                num_concords=1,
            ),
            3: Coocc(
                id=3,
                rel="GMOD",
                lemma1="Kommandant",
                lemma2="Feuerwehr",
                form1="Kommandant",
                form2="Feuerwehr",
                tag1="NOUN",
                tag2="NOUN",
                freq=1,
                score=9.75207233428955,
                inverse=0,
                has_mwe=0,
                num_concords=1,
            ),
            -3: Coocc(
                id=-3,
                rel="GMOD",
                lemma1="Feuerwehr",
                lemma2="Kommandant",
                form1="Feuerwehr",
                form2="Kommandant",
                tag1="NOUN",
                tag2="NOUN",
                freq=19,
                score=8.484715461730957,
                inverse=1,
                has_mwe=1,
                num_concords=19,
            ),
            4: Coocc(
                id=4,
                rel="KON",
                lemma1="Rettungsdienst",
                lemma2="Feuerwehr",
                form1="Rettungsdienst",
                form2="Feuerwehr",
                tag1="NOUN",
                tag2="NOUN",
                freq=8,
                score=8.768778800964355,
                inverse=0,
                has_mwe=1,
                num_concords=8,
            ),
            5: Coocc(
                id=5,
                rel="KON",
                lemma1="Rettungsdienst",
                lemma2="Feuerwehr",
                form1="Rettungsdienst",
                form2="Feuerwehr",
                tag1="NOUN",
                tag2="NOUN",
                freq=8,
                score=8.768778800964355,
                inverse=1,
                has_mwe=1,
                num_concords=8,
            ),
            11: Coocc(
                id=11,
                rel="",
                lemma1="",
                lemma2="",
                form1="",
                form2="",
                tag1="",
                tag2="",
                freq=1,
                score=0.5,
                inverse=1,
                has_mwe=0,
                num_concords=3,
            ),
        }
        self.conc = {
            11: [
                Concordance(
                    sentence="Vor\x02allem\x02die\x01,\x02die\x02beiden\x02immer\x02besonders\x02wichtig\x02waren\x01.",
                    token_position_1=1,
                    token_position_2=2,
                    extra_position="0",
                    corpus="corpus",
                    date=datetime.date.fromisoformat("2024-01-01"),
                    textclass="tc",
                    orig="",
                    avail="",
                    page="",
                    file="",
                    scan="",
                    score=5,
                    sentence_left="",
                    sentence_right="",
                ),
                Concordance(
                    sentence="Vor\x02allem\x02die\x01,\x02die\x02beiden\x02immer\x02besonders\x02wichtig\x02waren\x01.",
                    token_position_1=5,
                    token_position_2=6,
                    extra_position="0",
                    corpus="corpus",
                    date=datetime.date.fromisoformat("2024-01-01"),
                    textclass="tc",
                    orig="",
                    avail="",
                    page="",
                    file="",
                    scan="",
                    score=5,
                    sentence_left="",
                    sentence_right="",
                ),
                Concordance(
                    sentence="Vor\x02allem\x02die\x01,\x02die\x02beiden\x02immer\x02besonders\x02wichtig\x02waren\x01.",
                    token_position_1=7,
                    token_position_2=10,
                    extra_position="0",
                    corpus="corpus",
                    date=datetime.date.fromisoformat("2024-01-01"),
                    textclass="tc",
                    orig="",
                    avail="",
                    page="",
                    file="",
                    scan="",
                    score=5,
                    sentence_left="",
                    sentence_right="",
                ),
            ]
        }

    def get_relation_by_id(self, coocc_id, is_mwe=False):
        return self.coocc[coocc_id]

    def get_lemma_and_pos(self, lemma, pos):
        return [
            LemmaInfo(
                item.lemma1, item.form1, item.tag1, item.rel, item.freq, item.inverse
            )
            for item in self.coocc.values()
            if item.lemma1 == lemma
        ]

    def get_concordances(
        self, coocc_id: int, use_context: bool = False, start_index=0, result_number=3
    ) -> list[Concordance]:
        concordances = self.conc.get(coocc_id, [])
        return concordances[start_index : start_index + result_number]


class WordprofileTest(unittest.TestCase):
    def setUp(self):
        self.wp = Wordprofile()
        self.wp.db = MockDb()

    def test_invalid_lemma_raises_error(self):
        invalid_lemmata = ["test+", "string;", "select'", "dot,dot", "U_u\\", "other%"]
        for lemma in invalid_lemmata:
            with self.assertRaises(ValueError):
                self.wp.get_lemma_and_pos(lemma)

    def test_retrieval_of_relation_info_by_id(self):
        result = self.wp.get_relation_by_info_id(2)
        expected = {
            "Description": "Feuerwehr hat Genitivattribut Umgebung",
            "Relation": "GMOD",
            "Lemma1": "Feuerwehr",
            "Lemma2": "Umgebung",
            "Form1": "Feuerwehr",
            "Form2": "Umgebung",
            "POS1": "NOUN",
            "POS2": "NOUN",
        }
        self.assertEqual(result, expected)

    def test_retrieval_of_relation_info_by_id_inverse_relation(self):
        result = self.wp.get_relation_by_info_id(-3)
        expected = {
            "Description": "Feuerwehr ist Genitivattribut von Kommandant",
            "Relation": "GMOD",
            "Lemma1": "Feuerwehr",
            "Lemma2": "Kommandant",
            "Form1": "Feuerwehr",
            "Form2": "Kommandant",
            "POS1": "NOUN",
            "POS2": "NOUN",
        }
        self.assertEqual(result, expected)

    def test_relation_description_falls_back_to_default_if_relation_is_not_found(self):
        result = self.wp.get_relation_by_info_id(5)
        self.assertEqual(
            result["Description"], "Rettungsdienst tritt auf mit Feuerwehr"
        )

    def test_get_lemma_and_pos_aggregates_information(self):
        result = self.wp.get_lemma_and_pos("Feuerwehr")
        expected = [
            {
                "Form": "Feuerwehr",
                "Lemma": "Feuerwehr",
                "POS": "Substantiv",
                "PosId": "Substantiv",
                "Frequency": 45,
                "Relations": ["META", "GMOD", "~SUBJA", "~GMOD"],
            }
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_concordances_by_id(self):
        sents = self.wp.get_concordances_and_relation(11)
        result = {sent["ConcordLine"] for sent in sents["Tuples"]}
        expected = {
            "_&Vor&_ _&allem&_ die, die beiden immer besonders wichtig waren.",
            "Vor allem die, _&die&_ _&beiden&_ immer besonders wichtig waren.",
            "Vor allem die, die beiden _&immer&_ besonders wichtig _&waren&_.",
        }
        self.assertEqual(result, expected)
