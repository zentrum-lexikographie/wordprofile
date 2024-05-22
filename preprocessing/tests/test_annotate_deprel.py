from pathlib import Path

import pytest

import preprocessing.annotate_deprel as deprel

TEST_DIR = Path(__file__).parent


@pytest.fixture
def short_conll_file():
    return TEST_DIR / "testdata" / "short.conll"


@pytest.fixture
def multiple_docs_conll_file():
    return TEST_DIR / "testdata" / "four_docs.conll"
