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
    return deprel.setup_spacy_pipeline(accurate=False)


def test_conversion_to_spacy_doc(parser, short_conll_file):
    with open(short_conll_file) as fh:
        sentences = list(conllu.parse_incr(fh))
    sentence = sentences[0]
    result = deprel.convert_to_spacy_doc(parser, sentence)
    assert isinstance(result, spacy.tokens.Doc)
    assert len(result) == 13
    assert (
        result.text
        == "Sehr geehrter Herr Präsident Palinkás, meine sehr verehrten Damen und Herren , "
    )


def test_add_token_annotation_to_conll_sentence(short_conll_file, parser):
    with open(short_conll_file) as fh:
        sentences = conllu.parse(fh.read())
    doc = next(deprel.annotate(parser, sentences[3:4]))
    assert [(tok["form"], tok["upos"], tok["head"], tok["deprel"]) for tok in doc] == [
        ("Damals", "ADV", 2, "advmod"),
        ("ging", "VERB", 0, "ROOT"),
        ("eine", "DET", 5, "det"),
        ("ganze", "ADJ", 5, "amod"),
        ("Epoche", "NOUN", 2, "nsubj"),
        ("zu", "ADP", 7, "case"),
        ("Ende", "NOUN", 2, "obl"),
        (".", "PUNCT", 2, "punct"),
    ]


def test_space_after(short_conll_file):
    with open(short_conll_file) as fh:
        sentences = conllu.parse(fh.read())
    spaces = [deprel.is_space_after(tok) for tok in sentences[7]]
    assert spaces == [True, True, False, False, True, True, True, False, True, True]


def test_ner_model_added_as_component_to_nlp_pipeline():
    nlp = deprel.setup_spacy_pipeline(accurate=False)
    assert nlp.has_pipe("wikiner")


def test_named_entity_annotation_added_to_tokens(parser, short_conll_file):
    with open(short_conll_file) as fh:
        sentences = conllu.parse(fh.read())
    result = next(deprel.annotate(parser, sentences))
    assert result[4]["misc"]["NE"] == "PER"
