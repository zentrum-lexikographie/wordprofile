import argparse
import itertools
import re
import warnings
from pathlib import Path
from random import random
from tempfile import NamedTemporaryFile, TemporaryDirectory
from urllib.request import urlretrieve
from zipfile import ZipFile

from conllu.models import TokenList
from lxml import etree
from syntok.segmenter import analyze

from .conllu import serialize
from .utils import look_ahead

warnings.simplefilter(action='ignore', category=FutureWarning)

_no_whitespace = {"SpaceAfter": "No"}


def parse_doc(xml_file):
    xml_doc = etree.parse(xml_file)
    for text_el in xml_doc.iter("text"):
        for content in text_el.iter("rohtext"):
            content = re.sub(r"\\s+", " ", content.text.strip())
            sentences = (s for para in analyze(content) for s in para)
            for si, (sentence, next_sentence) in enumerate(look_ahead(sentences)):
                metadata = None
                if si == 0:
                    bibl = ". ".join((
                        text_el.attrib.get("person") or "Anonym",
                        text_el.attrib.get("titel") or "ohne Titel",
                        text_el.attrib.get("datum") or "n.d",
                        text_el.attrib.get("ort") or "o.O",
                        ""
                    ))
                    metadata = {
                        "newdoc id": text_el.attrib.get("url"),
                        "bibl": bibl,
                        "date": text_el.attrib.get("datum")
                    }
                next_sentence_t = next_sentence[0] if next_sentence else None
                tokens = []
                for ti, (t, next_t) in enumerate(look_ahead(sentence)):
                    next_t = next_t or next_sentence_t
                    no_space_after = next_t and (not next_t.spacing)
                    tokens.append({
                        "id": ti + 1,
                        "form": t.value.strip() or "---",
                        "misc": _no_whitespace if no_space_after else {}
                    })
                yield TokenList(tokens, metadata)


def as_conll(limit=0, sample=1.0):
    with TemporaryDirectory() as data_dir, \
         NamedTemporaryFile("w", delete_on_close=False) as zip_file:
        zip_file.close()
        urlretrieve(
            "https://politische-reden.eu/German-Political-Speeches-Corpus.zip",
            zip_file.name
        )
        with ZipFile(zip_file.name) as zf:
            zf.extractall(data_dir)
        sentences = (
            s
            for xml_file in Path(data_dir).rglob("*.xml")
            for s in parse_doc(xml_file)
        )
        if sample < 1.0:
            sentences = (
                s for s in sentences
                if s.metadata.get("newdoc id") or random() < sample
            )
        if limit > 0:
            sentences = itertools.islice(sentences, limit)
        for sentence in sentences:
            yield sentence


arg_parser = argparse.ArgumentParser(description="Download German Political Speeches")
arg_parser.add_argument(
    "-l", "--limit", help="limit # of sentences (no limit by default)",
    type=int, default="0"
)
arg_parser.add_argument(
    "-o", "--output-file", help="CoNLL-U output file (stdout by default)",
    type=argparse.FileType("w"), default="-"
)
arg_parser.add_argument(
    "-s", "--sample", help="sample ratio [0.0,1.0] (all sentences by default)",
    type=float, default="1.0"
)


def main():
    args = arg_parser.parse_args()
    for sentence in as_conll(args.limit, args.sample):
        args.output_file.write(serialize(sentence))


if __name__ == "__main__":
    main()
