from pathlib import Path

import pytest
import preprocessing.annotate_deprel as deprel

TEST_DIR = Path(__file__).parent


@pytest.fixture
def short_conll_file():
    return TEST_DIR / "testdata" / "short.conll"


@pytest.fixture
def multiple_docs_conll_file():
    test_dir = Path(__file__).parent
    return TEST_DIR / "testdata" / "four_docs.conll"


def test_conll_file_chunked_correctly(short_conll_file):
    with open(short_conll_file) as fh:
        for sent in deprel.iter_conll_sentences(fh):
            assert sent.startswith("#")
            lines = sent.split("\n")
            assert lines[-2][0].isnumeric()


def test_last_sentence_from_file_not_eaten_if_newline_missing(short_conll_file):
    with open(short_conll_file, "r") as fh:
        result = list(deprel.iter_conll_sentences(fh))
    assert len(result) == 10


def test_avoid_yielding_empty_string_if_newline_present(multiple_docs_conll_file):
    with open(multiple_docs_conll_file) as fh:
        result = list(deprel.iter_conll_sentences(fh))
        assert result[-1] != ""
