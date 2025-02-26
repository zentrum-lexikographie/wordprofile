import datetime
import os
import unittest
from pathlib import Path
from subprocess import check_call

import pytest

from wordprofile.datatypes import Coocc, LemmaInfo
from wordprofile.db import load_db, open_db
from wordprofile.wpse.connector import WPConnect
from wordprofile.wpse.mwe_connector import WPMweConnect

db_test_data_dir = Path(__file__).parent / "testdata" / "test_db"


@pytest.fixture(autouse=True, scope="session")
def test_db():
    if os.environ.get("WP_SKIP_TEST_DB_FIXTURE"):
        yield False
    else:
        check_call(["docker", "compose", "-p", "wp_test", "up", "db", "--wait"])
        load_db(open_db(clear=True), db_test_data_dir)
        yield True
        check_call(["docker", "compose", "-p", "wp_test", "down", "db", "-v"])


class WPConnectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.connector = WPConnect(host="localhost", user="wp", passwd="wp", dbname="wp")

    def test_random_examples_extracted(self):
        concordances = self.connector.get_concordances(
            -30601, start_index=0, result_number=5
        )
        all_available_concordance = self.connector.get_concordances(
            -30601, start_index=0, result_number=100
        )
        with self.subTest():
            for conc in concordances:
                self.assertTrue(conc in all_available_concordance)
        self.assertNotEqual(concordances, all_available_concordance[:5])

    def test_random_sample_reproducible(self):
        result = set()
        for _ in range(100):
            result.update(
                (
                    example.sentence,
                    example.token_position_1,
                    example.token_position_2,
                    example.date,
                )
                for example in self.connector.get_concordances(
                    368, start_index=0, result_number=1
                )
            )
        self.assertEqual(len(result), 1)

    def test_concordances_sorted_in_descending_order(self):
        result = [
            conc.date
            for conc in self.connector.get_concordances(
                -30601, start_index=0, result_number=100
            )
        ]
        self.assertEqual(result, sorted(result, reverse=True))

    def test_retrieval_of_collocation_with_preposition_via_id(self):
        result = self.connector.get_relation_by_id(300)
        expected = Coocc(
            id=300,
            rel="PP",
            lemma1="nehmen",
            lemma2="Angabe",
            form1="nehmen",
            form2="Angaben",
            tag1="VERB",
            tag2="NOUN",
            freq=386,
            score=11.0,
            inverse=0,
            has_mwe=0,
            num_concords=1,
            prep="nach",
        )
        self.assertEqual(result, expected)

    def test_retrieval_of_collocation_with_prep_via_tuple(self):
        result = self.connector.get_relation_tuples(
            "nehmen", "VERB", 0, 3, "log_dice", 0, 0, "SUBJA"
        )
        expected = [
            Coocc(
                id=2373301,
                rel="SUBJA",
                lemma1="nehmen",
                lemma2="Polizei",
                form1="nehmen",
                form2="Polizei",
                tag1="VERB",
                tag2="NOUN",
                freq=262,
                score=8.5,
                inverse=0,
                has_mwe=1,
                num_concords=261,
                prep="_",
            ),
            Coocc(
                id=301,
                rel="SUBJA",
                lemma1="nehmen",
                lemma2="Feuerwehr",
                form1="nehmen",
                form2="Feuerwehr",
                tag1="VERB",
                tag2="NOUN",
                freq=210,
                score=8.25,
                inverse=0,
                has_mwe=0,
                num_concords=0,
                prep="_",
            ),
        ]
        self.assertEqual(expected, result)

    def test_retrieval_of_meta_relation_no_inverse(self):
        result = [
            (c.lemma2, c.rel, c.inverse, c.freq)
            for c in self.connector.get_relation_meta(
                "nehmen", "VERB", 0, 10, "frequency", 0, 0, ["SUBJA", "OBJ"]
            )
        ]
        expected = [
            ("fest", "OBJ", 0, 387),
            ("Polizei", "SUBJA", 0, 262),
            ("Feuerwehr", "SUBJA", 0, 210),
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_meta_relation(self):
        result = self.connector.get_relation_meta(
            "Kunst", "NOUN", 0, 10, "log_dice", 0, 0, ["KON", "~GMOD"]
        )
        expected = [
            Coocc(
                id=-368,
                rel="GMOD",
                lemma1="Kunst",
                lemma2="Haus",
                form1="Kunst",
                form2="Haus",
                tag1="NOUN",
                tag2="NOUN",
                freq=389,
                score=11.125,
                inverse=1,
                has_mwe=0,
                num_concords=374,
                prep="_",
            ),
            Coocc(
                id=3406416,
                rel="KON",
                lemma1="Kunst",
                lemma2="Kultur",
                form1="Kunst",
                form2="Kultur",
                tag1="NOUN",
                tag2="NOUN",
                freq=51,
                score=9.5,
                inverse=0,
                has_mwe=0,
                num_concords=50,
                prep="_",
            ),
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_diff_comparison_inverse(self):
        result = self.connector.get_relation_tuples_diff(
            lemma1="Feuerwehr",
            lemma2="Polizei",
            lemma_tag="NOUN",
            relation="~SUBJA",
            order_by="log_dice",
            min_freq=0,
            min_stat=0,
        )
        expected = [
            Coocc(
                id=-2373301,
                rel="SUBJA",
                lemma1="Polizei",
                lemma2="nehmen",
                form1="Polizei",
                form2="nehmen",
                tag1="NOUN",
                tag2="VERB",
                freq=262,
                score=8.5,
                inverse=1,
                has_mwe=1,
                num_concords=261,
                prep="_",
            ),
            Coocc(
                id=-301,
                rel="SUBJA",
                lemma1="Feuerwehr",
                lemma2="nehmen",
                form1="Feuerwehr",
                form2="nehmen",
                tag1="NOUN",
                tag2="VERB",
                freq=210,
                score=8.25,
                inverse=1,
                has_mwe=0,
                num_concords=0,
                prep="_",
            ),
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_diff_meta_inverse(self):
        result = self.connector.get_relation_tuples_diff_meta(
            lemma1="Feuerwehr",
            lemma2="Polizei",
            lemma_tag="NOUN",
            order_by="log_dice",
            min_freq=0,
            min_stat=0,
            relations=["~SUBJA"],
        )
        expected = [
            Coocc(
                id=-2373301,
                rel="SUBJA",
                lemma1="Polizei",
                lemma2="nehmen",
                form1="Polizei",
                form2="nehmen",
                tag1="NOUN",
                tag2="VERB",
                freq=262,
                score=8.5,
                inverse=1,
                has_mwe=0,
                num_concords=261,
                prep="_",
            ),
            Coocc(
                id=-301,
                rel="SUBJA",
                lemma1="Feuerwehr",
                lemma2="nehmen",
                form1="Feuerwehr",
                form2="nehmen",
                tag1="NOUN",
                tag2="VERB",
                freq=210,
                score=8.25,
                inverse=1,
                has_mwe=0,
                num_concords=0,
                prep="_",
            ),
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_collocates_order_by_logdice(self):
        result = [
            (col[0], round(col[1], 2))
            for col in self.connector.get_collocates(
                "Feuerwehr", "NOUN", order_by="log_dice"
            )
        ]
        expected = [("nehmen", 8.25), ("Angabe", 7.25), ("Sprecher", 7.05)]
        self.assertEqual(result, expected)

    def test_retrieval_of_collocates_order_by_freq(self):
        result = self.connector.get_collocates("Kunst", "NOUN", order_by="frequency")
        expected = [("Haus", 389), ("Kultur", 51), ("schön", 42)]
        self.assertEqual(result, expected)

    def test_retrieval_of_collocates_cutoff(self):
        result = self.connector.get_collocates(
            "nehmen", "VERB", order_by="frequency", number=3
        )
        expected = [
            ("fest", 387),
            ("Angabe", 386),
            ("Polizei", 262),
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_collocates_returns_empty_list_for_oov(self):
        result = self.connector.get_collocates("Unknown", "NOUN")
        self.assertEqual(result, [])

    def test_collocates_filtered_by_frequency(self):
        result = self.connector.get_collocates(
            "liegen", "VERB", order_by="frequency", min_freq=200
        )
        self.assertEqual(result, [("Boden", 210)])

    def test_collocates_filtered_by_logdice(self):
        result = [
            (col[0], round(col[1], 1))
            for col in self.connector.get_collocates(
                "nehmen", "VERB", order_by="log_dice", min_stat=10.0
            )
        ]
        self.assertEqual(result, [("Angabe", 11.0), ("fest", 10.9)])

    def test_get_lemma_and_pos_no_inverse(self):
        result = self.connector.get_lemma_and_pos(lemma="liegen", lemma_tag="VERB")
        self.assertEqual(
            result,
            [LemmaInfo(lemma="liegen", tag="VERB", rel="PP", freq=230, inv=0)],
        )

    def test_get_lemma_and_pos_with_inverse(self):
        result = sorted(
            self.connector.get_lemma_and_pos(lemma="Kunst", lemma_tag="NOUN"),
            key=lambda x: x.freq,
        )
        self.assertEqual(
            result,
            [
                LemmaInfo(lemma="Kunst", tag="NOUN", rel="ATTR", freq=42, inv=0),
                LemmaInfo(lemma="Kunst", tag="NOUN", rel="KON", freq=51, inv=0),
                LemmaInfo(lemma="Kunst", tag="NOUN", rel="GMOD", freq=389, inv=1),
            ],
        )

    def test_get_lemma_and_pos_oov(self):
        result = self.connector.get_lemma_and_pos(lemma="Karate", lemma_tag="NOUN")
        self.assertEqual(
            result,
            [],
        )

    def test_metadata_retrieval_tables(self):
        tables = sorted(
            [
                {"name": t["name"], "rows": t["rows"]}
                for t in self.connector.get_db_infos()
            ],
            key=lambda x: x["rows"],
        )
        expected = [
            {
                "name": "corpus_freqs",
                "rows": 6,
            },
            {
                "name": "mwe",
                "rows": 8,
            },
            {
                "name": "collocations",
                "rows": 13,
            },
            {
                "name": "token_freqs",
                "rows": 15,
            },
            {
                "name": "mwe_match",
                "rows": 166,
            },
            {
                "name": "corpus_files",
                "rows": 660,
            },
            {
                "name": "matches",
                "rows": 1126,
            },
            {
                "name": "concord_sentences",
                "rows": 20626,
            },
        ]

        self.assertEqual(tables, expected)

    def test_metadata_retrieval_tags(self):
        tags = self.connector.get_tag_frequencies()
        self.assertEqual(tags, {"ADJ": 437, "ADP": 3282, "NOUN": 50720, "VERB": 34897})

    def test_metadata_retrieval_labels(self):
        labels = self.connector.get_label_frequencies()
        self.assertEqual(
            labels,
            {"ATTR": 62, "GMOD": 449, "OBJ": 387, "KON": 51, "SUBJA": 472, "PP": 616},
        )

    def test_metadata_retrieval_corpora(self):
        corpora = self.connector.get_corpus_file_stats()
        self.assertEqual(
            corpora,
            {
                "corpus": {
                    "count": 660,
                    "max_date": datetime.datetime(2023, 10, 14, 0, 0),
                    "min_date": datetime.datetime(2005, 1, 13, 0, 0),
                }
            },
        )

    def test_retrieval_of_inverse_collocates(self):
        result = self.connector.get_collocates("Polizei", "NOUN", order_by="frequency")
        expected = [("nehmen", 262)]
        self.assertEqual(result, expected)

    def test_get_lemma_and_pos_without_pos(self):
        result = self.connector.get_lemma_and_pos(lemma="Boden")
        self.assertEqual(
            result,
            [LemmaInfo(lemma="Boden", tag="NOUN", rel="PP", freq=210, inv=1)],
        )

    def test_retrieve_inverse_coocc_by_id(self):
        result = self.connector.get_relation_by_id(-300)
        expected = Coocc(
            id=-300,
            rel="PP",
            lemma1="Angabe",
            lemma2="nehmen",
            form1="Angaben",
            form2="nehmen",
            tag1="NOUN",
            tag2="VERB",
            freq=386,
            score=11.0,
            inverse=1,
            has_mwe=0,
            num_concords=1,
            prep="nach",
        )
        self.assertEqual(result, expected)

    def test_retrieve_relation_tuples_with_inverse(self):
        result = self.connector.get_relation_tuples(
            "Kunst", "NOUN", 0, 3, "log_dice", 0, 0, "~GMOD"
        )
        expected = [
            Coocc(
                id=-368,
                rel="GMOD",
                lemma1="Kunst",
                lemma2="Haus",
                form1="Kunst",
                form2="Haus",
                tag1="NOUN",
                tag2="NOUN",
                freq=389,
                score=11.125,
                inverse=1,
                has_mwe=0,
                num_concords=374,
                prep="_",
            )
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_relation_tuples_with_inverse_order_by_frequency(self):
        result = [
            (c.lemma2, c.freq)
            for c in self.connector.get_relation_tuples(
                "Feuerwehr", "NOUN", 0, 3, "frequency", 0, 0, "~GMOD"
            )
        ]
        expected = [("Angabe", 20), ("Sprecher", 15)]
        self.assertEqual(result, expected)

    def test_retrieval_of_meta_relation_only_inverse(self):
        result = self.connector.get_relation_meta(
            "Kunst", "NOUN", 0, 10, "log_dice", 0, 0, ["~GMOD"]
        )
        expected = [
            Coocc(
                id=-368,
                rel="GMOD",
                lemma1="Kunst",
                lemma2="Haus",
                form1="Kunst",
                form2="Haus",
                tag1="NOUN",
                tag2="NOUN",
                freq=389,
                score=11.125,
                inverse=1,
                has_mwe=0,
                num_concords=374,
                prep="_",
            )
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_diff_comparison_no_inverse(self):
        result = [
            (c.id, c.rel, c.lemma1, c.lemma2, c.tag2, c.inverse, c.freq)
            for c in self.connector.get_relation_tuples_diff(
                lemma1="Sprecher",
                lemma2="Angabe",
                lemma_tag="NOUN",
                relation="GMOD",
                order_by="frequency",
                min_freq=0,
                min_stat=0,
            )
        ]
        expected = [
            (304, "GMOD", "Angabe", "Feuerwehr", "NOUN", 0, 20),
            (30601, "GMOD", "Sprecher", "Feuerwehr", "NOUN", 0, 15),
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_diff_meta_mixed(self):
        result = [
            (c.id, c.rel, c.lemma1, c.lemma2, c.tag2, c.inverse, c.freq)
            for c in self.connector.get_relation_tuples_diff_meta(
                lemma1="Kunst",
                lemma2="Kultur",
                lemma_tag="NOUN",
                order_by="frequency",
                min_freq=0,
                min_stat=0,
                relations=["ATTR", "~GMOD"],
            )
        ]
        expected = [
            (-368, "GMOD", "Kunst", "Haus", "NOUN", 1, 389),
            (2006644, "ATTR", "Kunst", "schön", "ADJ", 0, 42),
            (-306, "GMOD", "Kultur", "Festival", "NOUN", 1, 25),
            (305, "ATTR", "Kultur", "modern", "ADJ", 0, 20),
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_diff_meta_no_inverse(self):
        result = [
            (c.id, c.rel, c.lemma1, c.lemma2, c.tag2, c.inverse, c.freq)
            for c in self.connector.get_relation_tuples_diff_meta(
                lemma1="Sprecher",
                lemma2="Angabe",
                lemma_tag="NOUN",
                order_by="frequency",
                min_freq=0,
                min_stat=0,
                relations=["GMOD"],
            )
        ]
        expected = [
            (304, "GMOD", "Angabe", "Feuerwehr", "NOUN", 0, 20),
            (30601, "GMOD", "Sprecher", "Feuerwehr", "NOUN", 0, 15),
        ]
        self.assertEqual(result, expected)

    def test_collocates_exclude_KON_relation_for_inverse(self):
        result = self.connector.get_collocates("Kultur", "NOUN", order_by="frequency")
        expected = [
            ("Festival", 25),
            ("modern", 20),
        ]
        self.assertEqual(result, expected)


class WPMweConnectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mwe_connector = WPMweConnect(
            host="localhost", user="wp", passwd="wp", dbname="wp"
        )

    def test_random_examples_extracted_for_mwe(self):
        sample = self.mwe_connector.get_concordances(
            512, start_index=0, result_number=5
        )
        all_available_concordances = self.mwe_connector.get_concordances(
            512, start_index=0, result_number=1000
        )
        with self.subTest():
            for conc in sample:
                self.assertTrue(conc in all_available_concordances)
        self.assertNotEqual(sample, all_available_concordances[:5])

    def test_examples_sorted_in_descending_order(self):
        result = [
            conc.date
            for conc in self.mwe_connector.get_concordances(
                512, start_index=0, result_number=100
            )
        ]
        self.assertEqual(result, sorted(result, reverse=True))

    def test_retrieval_of_inverse_attribute_from_database_by_id(self):
        result = self.mwe_connector.get_relation_by_id(512)
        expected = Coocc(
            id=512,
            rel="OBJ",
            lemma1="nehmen-Polizei",
            lemma2="fest",
            form1="nehmen-Polizei",
            form2="fest",
            tag1="VERB-NOUN",
            tag2="ADP",
            freq=164,
            score=11.0,
            inverse=1,
            has_mwe=0,
            num_concords=164,
            prep="_",
        )
        self.assertEqual(result, expected)

    def test_retrieval_of_mwe_relation_tuples(self):
        result = self.mwe_connector.get_relation_tuples(
            [2367256], order_by="log_dice", min_freq=1, min_stat=1
        )
        expected = [
            Coocc(
                id=513,
                rel="SUBJA",
                lemma1="nehmen-fest",
                lemma2="Polizei",
                form1="nehmen-fest",
                form2="Polizei",
                tag1="VERB-ADP",
                tag2="NOUN",
                freq=164,
                score=11.0,
                inverse=0,
                has_mwe=0,
                num_concords=0,
                prep="_",
            )
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_mwe_relation_tuples_if_inverse(self):
        result = self.mwe_connector.get_relation_tuples(
            [2373301], order_by="log_dice", min_freq=1, min_stat=1
        )
        expected = [
            Coocc(
                id=512,
                rel="OBJ",
                lemma1="nehmen-Polizei",
                lemma2="fest",
                form1="nehmen-Polizei",
                form2="fest",
                tag1="VERB-NOUN",
                tag2="ADP",
                freq=164,
                score=11.0,
                inverse=1,
                has_mwe=0,
                num_concords=164,
                prep="_",
            )
        ]
        self.assertEqual(result, expected)

    def test_retrieve_collocation_id_via_lemmata(self):
        result = self.mwe_connector.get_collocations("nehmen", "Polizei")
        self.assertEqual(result, [(2373301,)])

    def test_retrieve_collocation_id_via_lemmata_inverse(self):
        result = self.mwe_connector.get_collocations("Polizei", "nehmen")
        self.assertEqual(result, [(2373301,)])

    def test_retrieval_of_collocation_id_for_non_mwe_collocation(self):
        result = self.mwe_connector.get_collocations("Neun", "falsch")
        self.assertEqual(result, [])

    def test_tuples_ordered_by_score(self):
        res = self.mwe_connector.get_relation_tuples(
            [2006644], order_by="log_dice", min_freq=1, min_stat=1
        )
        result = [(c.id, c.score) for c in res]
        self.assertEqual(result, [(511, 11.0), (515, 10.5), (516, 10.0), (514, 8.0)])

    def test_tuples_ordered_by_frequency(self):
        res = self.mwe_connector.get_relation_tuples(
            [2006644], order_by="frequency", min_freq=1, min_stat=1
        )
        result = [(c.id, c.freq) for c in res]
        self.assertEqual(result, [(514, 150), (511, 120), (515, 100), (516, 99)])

    def test_correct_prepositions_fetched_for_pp_collocates_of_pp_mwe_by_id(self):
        result = self.mwe_connector.get_relation_by_id(517)
        expected = Coocc(
            id=517,
            rel="PP",
            lemma1="liegen-Boden",
            lemma2="Lachen",
            form1="liegen-Boden",
            form2="Lachen",
            tag1="VERB-NOUN",
            tag2="NOUN",
            freq=99,
            score=10.0,
            inverse=0,
            has_mwe=0,
            num_concords=2,
            prep="vor",
        )
        self.assertEqual(result, expected)

    def test_correct_prepositions_fetched_for_pp_collocates_of_pp_mwe_by_list(self):
        result = self.mwe_connector.get_relation_tuples(
            [302], order_by="log_dice", min_freq=1, min_stat=1
        )
        expected = Coocc(
            id=517,
            rel="PP",
            lemma1="liegen-Boden",
            lemma2="Lachen",
            form1="liegen-Boden",
            form2="Lachen",
            tag1="VERB-NOUN",
            tag2="NOUN",
            freq=99,
            score=10.0,
            inverse=0,
            has_mwe=0,
            num_concords=2,
            prep="vor",
        )
        self.assertEqual(result[0], expected)
