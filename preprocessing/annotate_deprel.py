import logging
import os
import sys
import time
from datetime import date, datetime

import click
import conllu


logger = logging.getLogger(__name__)


class SpacyParser:
    def __init__(self, model_path="", batch_size=256):
        import spacy
        from spacy.tokens import Doc

        spacy.prefer_gpu()

        tmp_stdout = sys.stdout
        sys.stdout = sys.stderr
        self.nlp = spacy.load(model_path or "de_dep_hdt_sm")
        self.batch_size = batch_size
        sys.stdout = tmp_stdout
        self.make_doc = lambda s: Doc(self.nlp.vocab, words=list(s))

    def custom_tokenizer(self, sentence):
        return self.make_doc(
            token["form"] if token["form"] else "---" for token in sentence
        )

    def __call__(self, sentences):
        try:
            docs = self.nlp.pipe(
                map(self.custom_tokenizer, sentences), batch_size=self.batch_size
            )
            for sent, doc in zip(sentences, docs):
                for token, word in zip(sent, doc):
                    token.update(
                        upos=word.pos_,
                        xpos=word.tag_,
                        feats=word.morph if word.morph else "_",
                        head=0 if word.dep_ == "ROOT" else word.head.i + 1,
                        deprel=word.dep_,
                    )
        except RuntimeError as e:
            sys.stderr.write(f"Runtime Error: {e}")
        return sentences


def iter_conll_sentences(file_handle):
    chunk = []
    for line in file_handle:
        if line == "\n":
            if chunk:
                yield "".join(chunk)
                chunk.clear()
        else:
            chunk.append(line)
    if chunk:
        yield "".join(chunk)


def group_sentences_to_documents(sentences):
    doc = []
    for sent in sentences:
        if "# DDC:meta.file_ =" in sent:
            if len(doc):
                yield "\n".join(doc)
            doc = [sent]
        else:
            doc.append(sent)
    if len(doc):
        yield "\n".join(doc)


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


@click.command()
@click.option("-i", "--input", default="-", type=click.File("r"))
@click.option("-o", "--output", default="-", type=click.File("w", encoding="utf-8"))
@click.option("--model", default="de_dwds_dep_hdt_dist", type=str)
def main(input, output, model):
    configure_logging()
    input_file = input.name if input != "-" else "from stdin"
    logger.info("Processing corpus %s with %s model." % (input_file, model))
    parser = SpacyParser(model_path=model)

    start = time.time()
    logger.info("Start time: %s" % datetime.fromtimestamp(start))
    for doc_str in group_sentences_to_documents(iter_conll_sentences(input)):
        doc = conllu.parse(doc_str, fields=conllu.parser.DEFAULT_FIELDS)
        for sentence in parser(doc):
            output.write(sentence.serialize())
        output.flush()
    end = time.time()
    elapsed_time = end - start
    logger.info("End time: %s" % datetime.fromtimestamp(end))
    logger.info("Elapsed time: %f s" % elapsed_time)


if __name__ == "__main__":
    main()
