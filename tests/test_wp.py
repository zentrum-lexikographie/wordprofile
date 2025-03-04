import datetime
import unittest

from wordprofile.datatypes import Concordance, Coocc, LemmaInfo
from wordprofile.wp import Wordprofile


class MockDb:
    def __init__(self, db):
        self.db = db
        self.conc = {
            11: [
                Concordance(
                    sentence="Vor\x02allem\x02die\x01,\x02die\x02beiden\x02immer\x02besonders\x02wichtig\x02waren\x01.",
                    token_position_1=1,
                    token_position_2=2,
                    extra_position="0",
                    corpus="corpus",
                    date=datetime.date.fromisoformat("2024-01-01"),
                    orig="",
                    avail="",
                    file="",
                ),
                Concordance(
                    sentence="Vor\x02allem\x02die\x01,\x02die\x02beiden\x02immer\x02besonders\x02wichtig\x02waren\x01.",
                    token_position_1=5,
                    token_position_2=6,
                    extra_position="0",
                    corpus="corpus",
                    date=datetime.date.fromisoformat("2024-01-01"),
                    orig="",
                    avail="",
                    file="",
                ),
                Concordance(
                    sentence="Vor\x02allem\x02die\x01,\x02die\x02beiden\x02immer\x02besonders\x02wichtig\x02waren\x01.",
                    token_position_1=7,
                    token_position_2=10,
                    extra_position="0",
                    corpus="corpus",
                    date=datetime.date.fromisoformat("2024-01-01"),
                    orig="",
                    avail="",
                    file="",
                ),
            ]
        }

    def get_relation_by_id(self, coocc_id, is_mwe=False):
        return self.db.get(coocc_id)

    def get_lemma_and_pos(self, lemma, pos):
        return [
            LemmaInfo(item.lemma1, item.tag1, item.rel, item.freq, item.inverse)
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

    def get_concordances(
        self, coocc_id: int, start_index=0, result_number=3
    ) -> list[Concordance]:
        concordances = self.conc.get(coocc_id, [])
        return concordances[start_index : start_index + result_number]

    def get_collocates(
        self, lemma, lemma_tag, number, order_by, min_freq=5, min_stat=0
    ):
        collocates = []
        for id, coocc in self.db.items():
            if coocc.lemma1 == lemma and coocc.tag1 == lemma_tag:
                if coocc.freq >= min_freq and coocc.score >= min_stat:
                    score = coocc.score if order_by == "log_dice" else coocc.freq
                    collocates.append((coocc.lemma2, score))
        return sorted(collocates, key=lambda x: x[1], reverse=True)[:number]


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

    def get_collocations(self, lemma1, lemma2):
        result = set()
        for col_id, collocations in self.db.items():
            for col in collocations:
                if col.lemma1 == "-".join([lemma1, lemma2]):
                    result.add((col_id,))
        return list(result)


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
                prep="_",
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
                prep="_",
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
                prep="_",
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
                prep="_",
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
                prep="_",
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
                prep="_",
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
                prep="_",
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
                prep="_",
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
                prep="_",
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
                prep="_",
            ),
            11: Coocc(
                id=11,
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
                prep="_",
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
                prep="_",
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
                prep="_",
            ),
            15: Coocc(
                id=15,
                rel="OBJO",
                lemma1="gedenken",
                lemma2="Heldin",
                form1="gedenken",
                form2="Heldinnen",
                tag1="",
                tag2="",
                freq=1,
                score=0.5,
                inverse=0,
                has_mwe=0,
                num_concords=3,
                prep="_",
            ),
            16: Coocc(
                id=15,
                rel="OBJO",
                lemma1="Kommandant",
                lemma2="gedenken",
                form1="Kommandanten",
                form2="gedacht",
                tag1="NOUN",
                tag2="VERB",
                freq=1,
                score=0.5,
                inverse=1,
                has_mwe=0,
                num_concords=3,
                prep="_",
            ),
            17: Coocc(
                id=17,
                rel="PP",
                lemma1="Meer",
                lemma2="Sand",
                form1="Meer",
                form2="Sand",
                tag1="NOUN",
                tag2="NOUN",
                freq=1,
                score=0.5,
                inverse=1,
                has_mwe=0,
                num_concords=3,
                prep="an",
            ),
            18: Coocc(
                id=18,
                rel="ATTR",
                lemma1="Meer",
                lemma2="offen",
                form1="Meer",
                form2="offenen",
                tag1="NOUN",
                tag2="ADJ",
                freq=1,
                score=0.5,
                inverse=0,
                has_mwe=0,
                num_concords=3,
                prep="_",
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
                    inverse=1,
                    has_mwe=0,
                    num_concords=1,
                    prep="_",
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
                    prep="_",
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
                    prep="_",
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
                    inverse=1,
                    has_mwe=0,
                    num_concords=1,
                    prep="_",
                )
            ],
            -10: [
                Coocc(
                    id=101,
                    rel="SUBJP",
                    lemma1="gemeinnützig-Arbeit",
                    lemma2="aufbrummen",
                    form1="gemeinnützige-Arbeit",
                    form2="aufgebrummt",
                    tag1="NOUN-ADJ",
                    tag2="VERB",
                    freq=1,
                    score=12.67,
                    inverse=0,
                    has_mwe=0,
                    num_concords=1,
                    prep="_",
                ),
            ],
            18: [
                Coocc(
                    id=181,
                    rel="PP",
                    lemma1="Meer-offen",
                    lemma2="Zugang",
                    form1="Meer-offenen",
                    form2="Zugang",
                    tag1="NOUN-ADJ",
                    tag2="NOUN",
                    freq=1,
                    score=10.0,
                    inverse=1,
                    has_mwe=0,
                    num_concords=1,
                    prep="zu",
                ),
                Coocc(
                    id=182,
                    rel="PP",
                    lemma1="Meer-offen",
                    lemma2="Zugang",
                    form1="Meer-offenen",
                    form2="Zugang",
                    tag1="NOUN-ADJ",
                    tag2="NOUN",
                    freq=2,
                    score=11.0,
                    inverse=1,
                    has_mwe=0,
                    num_concords=2,
                    prep="von",
                ),
            ],
        }

        self.wp = Wordprofile()
        self.wp.db = MockDb(self.cooc_data)
        self.wp.db_mwe = MockMweDb(self.mwe_data)

    def test_invalid_lemma_returns_empty_list(self):
        invalid_lemmata = [
            "test+",
            "string;",
            "select'",
            "dot,dot",
            "U_u\\",
            "other%",
            "1%",
            "'rauf",
        ]
        for lemma in invalid_lemmata:
            result = self.wp.get_lemma_and_pos(lemma)
            with self.subTest():
                self.assertEqual(result, [])

    def test_retrieval_of_relation_info_by_id(self):
        result = self.wp.get_relation_by_info_id(2)
        expected = {
            "Description": "Feuerwehr hat Genitivattribut Umgebung",
            "Lemma1": "Feuerwehr",
            "Lemma2": "Umgebung",
        }
        self.assertEqual(result, expected)

    def test_retrieval_of_relation_info_by_id_inverse_relation(self):
        result = self.wp.get_relation_by_info_id(-3)
        expected = {
            "Description": "Feuerwehr ist Genitivattribut von Kommandant",
            "Lemma1": "Feuerwehr",
            "Lemma2": "Kommandant",
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
                "Lemma": "Feuerwehr",
                "POS": "Substantiv",
                "PosId": "Substantiv",
                "Frequency": 45,
                "Relations": ["META", "GMOD", "~SUBJA", "~GMOD"],
            }
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_relation_description_for_mwe_if_inverse(self):
        mwe_data = self.wp.get_mwe_relations([14])["data"]
        result = mwe_data["Grammatik-lateinisch"][0]["Description"]
        self.assertEqual(result, "ist Passivsubjekt von")

    def test_retrieval_of_relation_description_if_not_inverse(self):
        mwe_data = self.wp.get_mwe_relations([10])["data"]
        result = mwe_data["Arbeit-gemeinnützig"][-1]["Description"]
        self.assertEqual(result, "hat Prädikativ")

    def test_relation_grouping(self):
        mwe_data = self.wp.get_mwe_relations([10])["data"]["Arbeit-gemeinnützig"]
        result = [(group["Relation"], group["Description"]) for group in mwe_data]
        expected = [
            ("~SUBJP", "ist Passivsubjekt von"),
            ("KON", "ist in Koordination mit"),
            ("PRED", "hat Prädikativ"),
        ]
        self.assertEqual(result, expected)

    def test_concatenation_of_rel_id(self):
        mwe_data = self.wp.get_mwe_relations([10])["data"]["Arbeit-gemeinnützig"]
        result = [group["RelId"] for group in mwe_data]
        expected = [
            ("Arbeit-gemeinnützig#NOUN-ADJ#~SUBJP"),
            ("Arbeit-gemeinnützig#NOUN-ADJ#KON"),
            ("Arbeit-gemeinnützig#NOUN-ADJ#PRED"),
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

    def test_retrieval_of_collocation_ids_for_mwe_candidates(self):
        result = self.wp.get_collocation_ids("Arbeit", "gemeinnützig")
        self.assertEqual(result, [10])

    def test_retrieval_of_collocation_ids_for_mwe_candidates_with_inverse(self):
        result = self.wp.get_collocation_ids("gemeinnützig", "Arbeit")
        self.assertEqual(result, [10])

    def test_retrieval_of_collocation_ids_for_mwe_candidates_no_mwe(self):
        result = self.wp.get_collocation_ids("Neun", "falsch")
        self.assertEqual(result, [])

    def test_retrieval_of_concordances_by_id(self):
        sents = self.wp.get_concordances_and_relation(11)
        result = {sent["ConcordLine"] for sent in sents["Tuples"]}
        expected = {
            "_&Vor&_ _&allem&_ die, die beiden immer besonders wichtig waren.",
            "Vor allem die, _&die&_ _&beiden&_ immer besonders wichtig waren.",
            "Vor allem die, die beiden _&immer&_ besonders wichtig _&waren&_.",
        }
        self.assertEqual(result, expected)

    def test_retrieval_of_objo_relation_description(self):
        result = self.wp.get_relation_by_info_id(15)["Description"]
        expected = "gedenken hat Dativ-/Genitiv-Objekt Heldin"
        self.assertEqual(result, expected)

    def test_get_lemma_and_pos_returns_empty_list_for_different_pos(self):
        result = self.wp.get_lemma_and_pos_diff("Feuerwehr", "plüschig")
        self.assertEqual(result, [])

    def test_get_lemma_and_pos_diff_for_same_pos_aggregates_relations(self):
        result = self.wp.get_lemma_and_pos_diff("Feuerwehr", "Kommandant")
        expected = [
            {
                "LemmaId1": "Feuerwehr",
                "LemmaId2": "Kommandant",
                "POS": "Substantiv",
                "PosId": "Substantiv",
                "Relations": ["META", "~OBJO", "GMOD", "~SUBJA", "~GMOD"],
            }
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_mwe_relation_parts_contains_lemma_information(self):
        result = self.wp.get_mwe_relations([10])["parts"]
        expected = [{"Lemma": "Arbeit"}, {"Lemma": "gemeinnützig"}]
        self.assertEqual(result, expected)

    def test_concordance_result_contains_lemma_info_and_bibl(self):
        result = self.wp.get_concordances_and_relation(-1)
        expected = {
            "Description": "Feuerwehr ist Subjekt von rücken",
            "Lemma1": "Feuerwehr",
            "Lemma2": "rücken",
            "Tuples": [],
        }
        self.assertEqual(result, expected)

    def test_invalid_lemma_returns_empty_list_for_get_relations(self):
        lemmata = ["", "10%", "98/15", "eh'", "#tag", "test+"]
        for lemma in lemmata:
            result = self.wp.get_relations(lemma, "")
            with self.subTest():
                self.assertEqual(result, [])

    def test_invalid_lemma_returns_empty_list_for_collocations_ids(self):
        lemmata = [
            "",
            "10%",
            "98/15",
            "eh'",
            "#tag",
            "test+",
            "select'",
            "dot,dot",
            "U_u\\",
            "other%",
        ]
        for lemma in lemmata:
            result = self.wp.get_collocation_ids(lemma, "lemma")
            with self.subTest():
                self.assertEqual(result, [])

    def test_invalid_lemma_returns_empty_list_for_diff_comparison(self):
        lemmata = [
            "",
            "10%",
            "98/15",
            "eh'",
            "#tag",
            "test+",
            "select'",
            "dot,dot",
            "U_u\\",
            "other%",
            "...",
            ".txt",
        ]
        for lemma1, lemma2 in zip(lemmata, lemmata[1:] + lemmata[:1]):
            result = self.wp.get_diff(lemma1, lemma2, pos="", relations=[])
            with self.subTest():
                self.assertEqual(result, [])

    def test_formatting_of_lemmata_in_pp_mwe_relation(self):
        result = self.wp.get_mwe_relations([17])["parts"]
        expected = [{"Lemma": "Meer"}, {"Lemma": "Sand an"}]
        self.assertEqual(result, expected)

    def test_mwe_pp_collocates_with_different_prepositions_not_discarded(self):
        result = self.wp.get_mwe_relations([18])["data"]["Meer-offen"][0]["Tuples"]
        expected = [
            {
                "Relation": "~PP",
                "RelationDescription": "ist in Präpositionalgruppe",
                "POS": "Substantiv",
                "Form": "Zugang zu",
                "Lemma": "Zugang zu",
                "Score": {"Frequency": 1, "logDice": 10.0},
                "ConcordId": "#mwe181",
                "ConcordNoAccessible": 1,
                "HasMwe": 0,
            },
            {
                "Relation": "~PP",
                "RelationDescription": "ist in Präpositionalgruppe",
                "POS": "Substantiv",
                "Form": "Zugang von",
                "Lemma": "Zugang von",
                "Score": {"Frequency": 2, "logDice": 11.0},
                "ConcordId": "#mwe182",
                "ConcordNoAccessible": 2,
                "HasMwe": 0,
            },
        ]
        self.assertEqual(len(result), 2)
        self.assertEqual(result, expected)

    def test_reduced_profile_order_by_logdice(self):
        response = self.wp.get_reduced_profile(
            "Feuerwehr", "Substantiv", number=4, order_by="log_dice", min_freq=1
        )
        result = []
        for col in response:
            score = col["Score"]
            col["Score"] = round(score, 1)
            result.append(col)
        expected = [
            {"Lemma": "Kommandant", "Score": 8.5},
            {"Lemma": "rücken", "Score": 8.5},
            {"Lemma": "Umgebung", "Score": 4.8},
        ]

        self.assertEqual(result, expected)

    def test_reduced_profile_order_by_freq(self):
        result = self.wp.get_reduced_profile(
            "Sofa", "Substantiv", number=2, order_by="frequency"
        )
        self.assertEqual(
            result,
            [{"Lemma": "plüschig", "Score": 200}, {"Lemma": "gemütlich", "Score": 20}],
        )

    def test_empty_id_list_returns_empty_data(self):
        result = self.wp.get_mwe_relations([])
        self.assertEqual(result, {"parts": [], "data": {}})

    def test_collocations_skipped_if_not_in_passed_relations(self):
        result = self.wp.get_mwe_relations([14], relations=["GMOD"])
        expected = {
            "parts": [{"Lemma": "Grammatik"}, {"Lemma": "lateinisch"}],
            "data": {},
        }
        self.assertEqual(result, expected)

    def test_invalid_id_returns_empty_dict(self):
        result = self.wp.get_relation_by_info_id(234, is_mwe=False)
        mwe_result = self.wp.get_relation_by_info_id(1001, is_mwe=True)
        self.assertEqual(result, {})
        self.assertEqual(mwe_result, {})
