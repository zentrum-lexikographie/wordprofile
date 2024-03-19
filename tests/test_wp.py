import unittest

from wordprofile.datatypes import Coocc, LemmaInfo
from wordprofile.wp import Wordprofile


class MockDb:
    def __init__(self, db):
        self.db = db

    def get_relation_by_id(self, coocc_id, is_mwe=False):
        return self.db[coocc_id]

    def get_lemma_and_pos(self, lemma, pos):
        return [
            LemmaInfo(
                item.lemma1, item.form1, item.tag1, item.rel, item.freq, item.inverse
            )
            for item in self.db.values()
            if item.lemma1 == lemma
        ]


class MockMweDb(MockDb):
    def get_relation_tuples(
        self,
        coocc_ids: list[int],
        by_order: str = "log_dice",
        min_freq: int = 0,
        min_stat: float = -1000.0,
    ):
        mwe_cooccs = []
        for coocc_id in coocc_ids:
            mwe_cooccs.extend(self.db.get(coocc_id, []))
        return mwe_cooccs


class WordprofileTest(unittest.TestCase):
    def setUp(self):
        self.cooc_data = {
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
            10: Coocc(
                id=10,
                rel="ATTR",
                lemma1="Arbeit",
                lemma2="gemeinnützig",
                form1="Arbeit",
                form2="gemeinnützige",
                tag1="NOUN",
                tag2="ADJ",
                freq=10,
                score=10.0,
                inverse=0,
                has_mwe=1,
                num_concords=10,
            ),
            14: Coocc(
                id=141,
                rel="ATTR",
                lemma1="Grammatik",
                lemma2="lateinisch",
                form1="Grammatik",
                form2="lateinischen",
                tag1="NOUN",
                tag2="ADJ",
                freq=1,
                score=13.41,
                inverse=0,
                has_mwe=1,
                num_concords=1,
            ),
        }
        self.mwe_data = {
            10: [
                Coocc(
                    id=101,
                    rel="SUBJP",
                    lemma1="Arbeit-gemeinnützig",
                    lemma2="aufbrummen",
                    form1="Arbeit-gemeinnützige",
                    form2="aufgebrummt",
                    tag1="NOUN-ADJ",
                    tag2="VERB",
                    freq=1,
                    score=12.67,
                    inverse=0,
                    has_mwe=0,
                    num_concords=1,
                ),
                Coocc(
                    id=11,
                    rel="KON",
                    lemma1="Arbeit-gemeinnützig",
                    lemma2="Meditation",
                    form1="Arbeit-gemeinnützige",
                    form2="Meditation",
                    tag1="NOUN-ADJ",
                    tag2="NOUN",
                    freq=1,
                    score=12.67,
                    inverse=0,
                    has_mwe=0,
                    num_concords=1,
                ),
                Coocc(
                    id=12,
                    rel="PRED",
                    lemma1="Arbeit-gemeinnützig",
                    lemma2="sinnvoll",
                    form1="Arbeit-gemeinnützige",
                    form2="sinnvoller",
                    tag1="NOUN-ADJ",
                    tag2="ADJ",
                    freq=1,
                    score=12.0,
                    inverse=0,
                    has_mwe=0,
                    num_concords=1,
                ),
            ],
            14: [
                Coocc(
                    id=141,
                    rel="SUBJP",
                    lemma1="Grammatik-lateinisch",
                    lemma2="büffeln",
                    form1="Grammatik-lateinischen",
                    form2="büffeln",
                    tag1="NOUN-ADJ",
                    tag2="VERB",
                    freq=1,
                    score=13.41,
                    inverse=0,
                    has_mwe=0,
                    num_concords=1,
                )
            ],
        }
        self.wp = Wordprofile()
        self.wp.db = MockDb(self.cooc_data)
        self.wp.db_mwe = MockMweDb(self.mwe_data)

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

    def test_retrieval_of_relation_description_for_mwe(self):
        mwe_data = self.wp.get_mwe_relations([14])["data"]
        result = mwe_data["Grammatik-lateinisch"][0]["Description"]
        self.assertEqual(result, "ist Passivsubjekt von")
