from pathlib import Path

import conllu
import pytest
import spacy

import wordprofile.preprocessing.cli.annotate as deprel

TEST_DIR = Path(__file__).parent


@pytest.fixture
def short_conll_file():
    return TEST_DIR / "testdata" / "short.conll"


@pytest.fixture
def multiple_docs_conll_file():
    return TEST_DIR / "testdata" / "four_docs.conll"


@pytest.fixture(scope="module")
def parser():
    return deprel.SpacyParser(model="de_hdt_lg")


def test_custom_tokenizer(parser, short_conll_file):
    with open(short_conll_file) as fh:
        sentences = list(conllu.parse_incr(fh))
    sentence = sentences[0]
    sentence[1]["form"] = ""
    result = parser.custom_tokenizer(sentence)
    assert result[0][1].text == "---"


def test_parser_returns_annotations_and_original(parser, multiple_docs_conll_file):
    with open(multiple_docs_conll_file) as fh:
        doc = list(conllu.parse_incr(fh))
        result = next(parser(doc))
    assert len(result) == 2
    assert isinstance(result[0], spacy.tokens.Doc)
    assert isinstance(result[1], conllu.models.TokenList)
    assert result[1] == doc[0]


def test_add_token_annotation_to_conll_sentence(short_conll_file, parser):
    with open(short_conll_file) as fh:
        sentences = conllu.parse(fh.read())
    doc, conll_sent = next(parser(sentences[3:4]))
    deprel.add_annotation_to_tokens(conll_sent, doc)
    assert [
        (tok["form"], tok["upos"], tok["head"], tok["deprel"]) for tok in conll_sent
    ] == [
        ("Damals", "ADV", 2, "advmod"),
        ("ging", "VERB", 0, "ROOT"),
        ("eine", "DET", 5, "det"),
        ("ganze", "ADJ", 5, "amod"),
        ("Epoche", "NOUN", 2, "nsubj"),
        ("zu", "ADP", 7, "case"),
        ("Ende", "NOUN", 2, "obl"),
        (".", "PUNCT", 2, "punct"),
    ]
