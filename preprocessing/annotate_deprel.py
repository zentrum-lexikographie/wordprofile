import logging
import os
import re
import sys
import time
from collections import OrderedDict
from datetime import date, datetime

import click
import conllu
import torch


logger = logging.getLogger(__name__)


class TrankitParser:
    def __init__(self, model_type="german-hdt", embedding="xlm-roberta-base"):
        import trankit

        tmp_stdout = sys.stdout
        sys.stdout = sys.stderr
        self.parser = trankit.Pipeline(
            model_type, embedding=embedding, cache_dir=os.path.expanduser("~/.trankit/")
        )
        self.parser("Init")
        sys.stdout = tmp_stdout

    def __call__(self, sentences):
        sentences_in = [
            [token["form"] if token["form"] else "---" for token in sentence]
            for sentence in sentences
        ]
        try:
            res = self.parser(sentences_in)
            for sent_i, sent in enumerate(sentences):
                words = res["sentences"][sent_i]["tokens"]
                for tok_i, token in enumerate(sent):
                    ner_pred = words[tok_i].get("ner")
                    if ner_pred and ner_pred != "O":
                        if token["misc"]:
                            token["misc"]["NER"] = words[tok_i].get("ner")
                        else:
                            token["misc"] = OrderedDict(
                                [("NER", words[tok_i].get("ner"))]
                            )
                    # stay with the original lemma for better compliance
                    token.update(
                        upos=words[tok_i].get("upos", "_"),
                        xpos=words[tok_i].get("xpos", "_"),
                        feats=words[tok_i].get("feats", "_"),
                        head=words[tok_i].get("head", "_"),
                        deprel=words[tok_i].get("deprel", "_"),
                    )
        except RuntimeError as e:
            sys.stderr.write(f"Runtime Error: {e}")
        return sentences


class StanzaParser:
    def __init__(self, model_type="default"):
        import stanza

        self.parser = stanza.Pipeline(
            lang="de",
            package=model_type,
            processors="tokenize,pos,lemma,depparse,ner",
            tokenize_pretokenized=True,
        )
        self.parser("Init")

    def __call__(self, sentences):
        sentences_in = [
            [token["form"] if token["form"] else "---" for token in sentence]
            for sentence in sentences
        ]
        doc = self.parser(sentences_in)
        for sent_i, sent in enumerate(sentences):
            words = doc.sentences[sent_i].words
            for tok_i, (token, word) in enumerate(
                zip(sent, doc.sentences[sent_i].tokens)
            ):
                ner_pred = word.ner
                if token["misc"] and "NER" in token["misc"]:
                    del token["misc"]["NER"]
                if token["misc"] and "LT" in token["misc"]:
                    del token["misc"]["LT"]
                if ner_pred and ner_pred != "O":
                    if token["misc"]:
                        token["misc"]["NER"] = ner_pred
                    else:
                        token["misc"] = OrderedDict([("NER", ner_pred)])
                token.update(
                    upos=words[tok_i].upos,
                    xpos=words[tok_i].xpos,
                    feats=words[tok_i].feats if words[tok_i].feats else "_",
                    head=words[tok_i].head,
                    deprel=words[tok_i].deprel,
                )
        return sentences


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


RE_META = re.compile(r"# DDC:meta\.(\w+) = ?(.*)")


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
@click.option("--parser-type", default="trankit", type=str)
@click.option("--lang", default="german-hdt", type=str)
@click.option("--nthreads", default=1, type=int)
def main(input, output, parser_type, lang, nthreads):
    torch.set_num_threads(nthreads)
    configure_logging()
    input_file = input.name if input != "-" else "from stdin"
    logger.info("Processing corpus %s with %s parser." % (input_file, parser_type))
    if parser_type == "trankit":
        parser = TrankitParser(model_type=lang)
    elif parser_type == "trankit-xl":
        parser = TrankitParser(model_type=lang, embedding="xlm-roberta-large")
    elif parser_type == "stanza":
        parser = StanzaParser(model_type=lang)
    elif parser_type == "spacy":
        parser = SpacyParser(model_path=lang)
    else:
        raise ValueError("Unknown parser!")

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
