import pathlib
import unittest

import sqlalchemy as sq

import wordprofile.wpse.create as wc
from wordprofile.datatypes import Coocc
from wordprofile.wpse.connector import WPConnect
from wordprofile.wpse.mwe_connector import WPMweConnect
from wordprofile.wpse.processing import load_files_into_db


def create_database():
    engine = sq.create_engine(
        "mysql+pymysql://test:test@localhost:3306/test?charset=utf8mb4&local_infile=1"
    )
    with engine.connect() as conn:
        wc.init_word_profile_tables(conn, "test")
        data_dir = pathlib.Path(__file__).parent / "testdata" / "test_db"
        load_files_into_db(conn, data_dir)
        wc.create_indices(conn)
        wc.create_statistics(conn)


class WPConnectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_database()
        cls.connector = WPConnect(
            host="localhost", user="test", passwd="test", dbname="test"
        )

    def test_random_examples_extracted(self):
        concordances = self.connector.get_concordances(
            -30601, use_context=False, start_index=0, result_number=5
        )
        all_available_concordance = self.connector.get_concordances(
            -30601, use_context=False, start_index=0, result_number=100
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
                    368, use_context=False, start_index=0, result_number=1
                )
            )
        self.assertEqual(len(result), 1)

    def test_concordances_sorted_in_descending_order(self):
        result = [
            conc.date
            for conc in self.connector.get_concordances(
                -30601, use_context=False, start_index=0, result_number=100
            )
        ]
        self.assertEqual(result, sorted(result, reverse=True))

    def test_get_concordances_with_context(self):
        concordances = self.connector.get_concordances(
            2006644, use_context=True, start_index=0, result_number=1000
        )
        self.assertEqual(len(concordances), 40)

    def test_get_concordances_with_context_sorted_in_descending_order(self):
        result = [
            conc.date
            for conc in self.connector.get_concordances(
                3406416, use_context=True, start_index=0, result_number=100
            )
        ]
        self.assertEqual(result, sorted(result, reverse=True))


class WPMweConnectTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.connector = WPMweConnect(
            host="localhost", user="test", passwd="test", dbname="test"
        )

    def test_random_examples_extracted_for_mwe(self):
        sample = self.connector.get_concordances(
            512, use_context=False, start_index=0, result_number=5
        )
        all_available_concordances = self.connector.get_concordances(
            512, use_context=False, start_index=0, result_number=1000
        )
        with self.subTest():
            for conc in sample:
                self.assertTrue(conc in all_available_concordances)
        self.assertNotEqual(sample, all_available_concordances[:5])

    def test_examples_sorted_in_descending_order(self):
        result = [
            conc.date
            for conc in self.connector.get_concordances(
                512, use_context=False, start_index=0, result_number=100
            )
        ]
        self.assertEqual(result, sorted(result, reverse=True))

    def test_get_concordances_with_context(self):
        sample = self.connector.get_concordances(
            512, use_context=True, start_index=0, result_number=5
        )
        all_available_concordances = self.connector.get_concordances(
            512, use_context=True, start_index=0, result_number=1000
        )
        with self.subTest():
            for conc in sample:
                self.assertTrue(conc in all_available_concordances)
        self.assertNotEqual(sample, all_available_concordances[:5])

    def test_get_concordances_with_context_sorted_in_descending_order(self):
        result = [
            conc.date
            for conc in self.connector.get_concordances(
                512, use_context=True, start_index=0, result_number=100
            )
        ]
        self.assertEqual(result, sorted(result, reverse=True))

    def test_retrieval_of_inverse_attribute_from_database_by_id(self):
        result = self.connector.get_relation_by_id(512)
        expected = Coocc(
            id=512,
            rel="VZ",
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
        )
        self.assertEqual(result, expected)

    def test_retrieval_of_mwe_relation_tuples(self):
        result = self.connector.get_relation_tuples(
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
            )
        ]
        self.assertEqual(result, expected)

    def test_retrieval_of_mwe_relation_tuples_if_inverse(self):
        result = self.connector.get_relation_tuples(
            [2373301], order_by="log_dice", min_freq=1, min_stat=1
        )
        expected = [
            Coocc(
                id=512,
                rel="VZ",
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
            )
        ]
        self.assertEqual(result, expected)

    def test_retrieve_collocation_id_via_lemmata(self):
        result = self.connector.get_collocations("nehmen", "Polizei")
        self.assertEqual(result, [(2373301,)])

    def test_retrieve_collocation_id_via_lemmata_inverse(self):
        result = self.connector.get_collocations("Polizei", "nehmen")
        self.assertEqual(result, [(-2373301,)])

    def test_retrieval_of_collocation_id_for_non_mwe_collocation(self):
        result = self.connector.get_collocations("Neun", "falsch")
        self.assertEqual(result, [])