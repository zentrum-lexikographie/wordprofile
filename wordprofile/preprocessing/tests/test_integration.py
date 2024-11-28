import unittest
from datetime import date
from pathlib import Path
from shutil import rmtree

from click.testing import CliRunner

from wordprofile.preprocessing.cli import data_update, tabs2conllu


class Tabs2ConlluTest(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(__file__).parent
        self.tabs_file = self.test_dir / "testdata" / "sample.tabs"
        self.conll_file = self.test_dir / "testdata" / "sample.conllu"
        self.cli_runner = CliRunner()
        self.output_dir = self.test_dir / "output"

    def tearDown(self):
        if self.output_dir.exists():
            rmtree(self.output_dir)

    def test_conll_written_to_std(self):
        result = self.cli_runner.invoke(tabs2conllu.main, ["-i", str(self.tabs_file)])
        expected = self.conll_file.read_text()
        self.assertEqual(expected, result.output)

    def test_conll_written_to_file(self):
        self.cli_runner.invoke(
            tabs2conllu.main,
            ["-i", str(self.tabs_file), "-o", str(self.output_dir)],
        )
        result = next(self.output_dir.glob("*/sample.conllu")).read_text()
        expected = self.conll_file.read_text()
        self.assertEqual(expected, result)

    def test_output_path_matches_collection_of_input(self):
        self.cli_runner.invoke(
            tabs2conllu.main,
            ["-i", str(self.tabs_file), "-o", str(self.output_dir)],
        )
        self.assertTrue((self.output_dir / "politische_reden").exists())


class DataUpdateTest(unittest.TestCase):
    def setUp(self):
        self.cli_runner = CliRunner()
        self.data_dir = Path(__file__).parent / "testdata"
        self.todays_dir = self.data_dir / date.today().isoformat()

    def tearDown(self):
        if self.todays_dir.exists():
            rmtree(self.todays_dir)

    def test_subdir_with_current_date_created(self):
        assert self.todays_dir.exists() is False
        self.cli_runner.invoke(
            data_update.main,
            [
                "-c",
                "corpus",
                "-d",
                str(self.data_dir),
                "-t",
                str(self.data_dir / "dump"),
            ],
        )
        self.assertTrue(self.todays_dir.exists())

    def test_toc_created_for_new_data(self):
        self.cli_runner.invoke(
            data_update.main,
            [
                "-c",
                "corpus",
                "-d",
                str(self.data_dir),
                "-t",
                str(self.data_dir / "dump"),
            ],
        )
        self.assertTrue((self.todays_dir / "corpus.toc").exists())

    def test_new_basename_written_to_toc(self):
        self.cli_runner.invoke(
            data_update.main,
            [
                "-c",
                "corpus",
                "-d",
                str(self.data_dir),
                "-t",
                str(self.data_dir / "dump"),
            ],
        )
        result = (self.todays_dir / "corpus.toc").read_text()
        expected = "src/de1/DE1_0999_20090602"
        self.assertEqual(result, expected)

    def test_conll_data_written_to_file(self):
        self.cli_runner.invoke(
            data_update.main,
            [
                "-c",
                "corpus",
                "-d",
                str(self.data_dir),
                "-t",
                str(self.data_dir / "dump"),
            ],
        )
        result = (self.todays_dir / "corpus.conll").read_text()
        expected = (self.data_dir / "sample.conllu").read_text()
        self.assertEqual(result, expected)

    def test_no_new_directory_created_if_input_in_existing_toc(self):
        self.cli_runner.invoke(
            data_update.main,
            [
                "-c",
                "test",
                "-d",
                str(self.data_dir),
                "-t",
                str(self.data_dir / "dump"),
            ],
        )
        self.assertFalse(self.todays_dir.exists())
