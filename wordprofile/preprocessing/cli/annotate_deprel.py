import logging
import os
import sys
import time
from datetime import date, datetime
from subprocess import check_call
from typing import Iterable, Iterator
import warnings
import click
import conllu
import spacy
from spacy.tokens import Doc

from wordprofile.utils import configure_logs_to_file

logger = logging.getLogger(__name__)


def zdl_model_to_hf_url(model):
    return (
        f"https://huggingface.co/zentrum-lexikographie/{model}/resolve/main/"
        f"{model}-any-py3-none-any.whl"
    )


def load_zdl_spacy_model(model: str = "de_hdt_dist"):
    with warnings.catch_warnings():
        warnings.simplefilter(action='ignore', category=FutureWarning)
        spacy.prefer_gpu()
        try:
            return spacy.load(model)
        except OSError:
            requirement = f"{model} @ {zdl_model_to_hf_url(model)}"
            check_call([
                sys.executable,
                "-m",
                "pip",
                "install",
                "-qqq",
                "--progress-bar",
                "off",
                requirement
            ])
            return spacy.load(model)


class SpacyParser:
    def __init__(self, model: str = "de_hdt_dist", batch_size: int = 128) -> None:
        self.nlp = load_zdl_spacy_model(model)
        self.make_doc = lambda s: Doc(self.nlp.vocab, words=list(s))
        self.batch_size = batch_size

    def custom_tokenizer(
        self, sentence: conllu.models.TokenList
    ) -> tuple[Doc, conllu.models.TokenList]:
        return (
            self.make_doc(
                token["form"] if token["form"] else "---" for token in sentence
            ),
            sentence,
        )

    def __call__(
        self, sentences: Iterable[conllu.models.TokenList]
    ) -> Iterator[tuple[Doc, conllu.models.TokenList]]:
        return self.nlp.pipe(
            map(self.custom_tokenizer, sentences),
            batch_size=self.batch_size,
            as_tuples=True,
        )


def add_annotation_to_tokens(
    conll_sent: conllu.models.TokenList, annotation: Doc
) -> None:
    for token, word in zip(conll_sent, annotation):
        token.update(
            upos=word.pos_,
            xpos=word.tag_,
            feats=word.morph if word.morph else "_",
            head=0 if word.dep_ == "ROOT" else word.head.i + 1,
            deprel=word.dep_,
        )


@click.command(help="Parse conll file and add dependency relation annotations.")
@click.option(
    "-i",
    "--input",
    default="-",
    type=click.File("r"),
    help="Path to input file in conllu format.",
)
@click.option(
    "-o",
    "--output",
    default="-",
    type=click.File("w", encoding="utf-8"),
    help="Output file.",
)
@click.option(
    "--model",
    "-m",
    default="de_hdt_dist",
    type=str,
    help="Name of spacy model, default is 'de_hdt_dist'.",
)
@click.option(
    "--batch-size",
    "-b",
    default=128,
    type=int,
    help="Batch size used by model during processing. Default is 128 (sentences).",
)
def main(input, output, model, batch_size):
    configure_logs_to_file(log_file_identifier="annotate-deprel")
    input_file = input.name if input != "-" else "from stdin"
    logger.info(
        "Processing corpus %s with %s model (batch size: %d)."
        % (input_file, model, batch_size)
    )
    parser = SpacyParser(model=model, batch_size=batch_size)

    start = time.time()
    logger.info("Start time: %s" % datetime.fromtimestamp(start))
    for anno, sent in parser(
        conllu.parse_incr(input, fields=conllu.parser.DEFAULT_FIELDS)
    ):
        add_annotation_to_tokens(sent, anno)
        output.write(sent.serialize())
    end = time.time()
    elapsed_time = end - start
    logger.info("End time: %s" % datetime.fromtimestamp(end))
    logger.info("Elapsed time: %f s" % elapsed_time)


if __name__ == "__main__":
    main()
