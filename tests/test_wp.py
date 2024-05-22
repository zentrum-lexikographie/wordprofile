import unittest

from wordprofile.datatypes import Coocc, LemmaInfo
from wordprofile.wp import Wordprofile


class MockDb:
    def __init__(self):
        self.db = {
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
            6: Coocc(
                id=6,
                rel="ATTR",
                lemma1="Sofa",
                lemma2="gemütlich",
                form1="Sofa",
                form2="gemütliche",
                tag1="NOUN",
                tag2="ADJ",
                freq=20,
                score=8,
                inverse=0,
                has_mwe=0,
                num_concords=20,
            ),
            7: Coocc(
                id=7,
                rel="ATTR",
                lemma1="Sessel",
                lemma2="gemütlich",
                form1="Sessel",
                form2="gemütliche",
                tag1="NOUN",
                tag2="ADJ",
                freq=10,
                score=7,
                inverse=0,
                has_mwe=0,
                num_concords=10,
            ),
            8: Coocc(
                id=8,
                rel="ATTR",
                lemma1="Sofa",
                lemma2="plüschig",
                form1="Sofa",
                form2="plüschig",
                tag1="NOUN",
                tag2="ADJ",
                freq=200,
                score=1.7,
                inverse=0,
                has_mwe=0,
                num_concords=200,
            ),
            9: Coocc(
                id=9,
                rel="ATTR",
                lemma1="Sessel",
                lemma2="plüschig",
                form1="Sessel",
                form2="plüschig",
                tag1="NOUN",
                tag2="ADJ",
                freq=10,
                score=7.6,
                inverse=0,
                has_mwe=0,
                num_concords=10,
            ),
            10: Coocc(
                id=10,
                rel="ATTR",
                lemma1="Sofa",
                lemma2="bequem",
                form1="Sessel",
                form2="bequem",
                tag1="NOUN",
                tag2="ADJ",
                freq=10,
                score=7.6,
                inverse=0,
                has_mwe=0,
                num_concords=10,
            ),
        }

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

    def get_relation_tuples_diff(self, lemma1, lemma2, lemma_tag, relation, *kwargs):
        return [
            item
            for item in self.db.values()
            if item.tag1 == lemma_tag
            and item.lemma1 in {lemma1, lemma2}
            and item.rel == relation
        ]


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

    def test_calculate_diff(self):
        result = self.wp.get_diff(
            "Sofa",
            "Sessel",
            pos="Substantiv",
            relations=["ATTR"],
            operation="adiff",
            use_intersection=False,
        )[0]["Tuples"]
        expected = {
            "Position": "center",
            "Score": {
                "AScomp": 1,
                "Assoziation1": 8,
                "Assoziation2": 7,
                "Frequency1": 20,
                "Frequency2": 10,
                "Rank1": 0,
                "Rank2": 1,
            },
        }
        self.assertEqual(len(result), 3)
        self.assertEqual(expected["Position"], result[1]["Position"])
        self.assertEqual(expected["Score"], result[1]["Score"])

    def test_calculate_diff_with_intersection(self):
        result = self.wp.get_diff(
            "Sofa",
            "Sessel",
            pos="Substantiv",
            relations=["ATTR"],
            operation="adiff",
            use_intersection=True,
        )[0]["Tuples"]
        self.assertEqual(len(result), 2)

    def test_retrieval_of_intersection(self):
        result = self.wp.get_diff(
            "Sofa",
            "Sessel",
            pos="Substantiv",
            relations=["ATTR"],
            operation="hmean",
            use_intersection=True,
        )[0]["Tuples"]
        self.assertEqual(len(result), 2)
        self.assertEqual(
            [(col["Lemma"], round(col["Score"]["AScomp"], 1)) for col in result],
            [("gemütlich", 7.5), ("plüschig", 2.8)],
        )
