import logging
import os
import sys
import time
from datetime import date, datetime
from typing import Iterable, Iterator

import click
import conllu
from spacy.tokens import Doc

logger = logging.getLogger(__name__)


class SpacyParser:
    def __init__(self, model: str = "", batch_size: int = 128) -> None:
        import spacy

        spacy.prefer_gpu()

        tmp_stdout = sys.stdout
        sys.stdout = sys.stderr
        self.nlp = spacy.load(model)
        self.batch_size = batch_size
        sys.stdout = tmp_stdout
        self.make_doc = lambda s: Doc(self.nlp.vocab, words=list(s))

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


def configure_logging():
    log_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log")
    os.makedirs(log_directory, exist_ok=True)
    logging.basicConfig(
        filename=os.path.join(
            log_directory, f"{date.today().isoformat()}-annotate-deprel.log"
        ),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s: %(message)s",
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
    default="de_dwds_dep_hdt_dist",
    type=str,
    help="Name of spacy model, default is 'de_dwds_dep_hdt_dist'.",
)
@click.option(
    "--batch-size",
    "-b",
    default=128,
    type=int,
    help="Batch size used by model during processing. Default is 128 (sentences).",
)
def main(input, output, model, batch_size):
    configure_logging()
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
