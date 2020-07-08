#!/usr/bin/python3

import argparse
import io
import logging
import multiprocessing
import os
import sys
from glob import glob
from pathlib import Path
from typing import List, Iterable

from imsnpars.nparser import options
from imsnpars.tools import utils
from wordprofile.datatypes import TabsToken, ConllToken
from wordprofile.parsing import get_parser, parse_document
from wordprofile.utils import chunks

# Set for graph search in parser
sys.setrecursionlimit(200)

lformat = '[%(levelname)s] %(asctime)s %(name)s# %(message)s'
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format=lformat)


class TabsSentence:
    def __init__(self, meta: List[str], tokens: Iterable):
        self.meta = meta
        self.tokens = tuple(tokens)

    def add_column(self, column_items: Iterable):
        self.tokens = [row + (item,) for row, item in zip(self.tokens, column_items)]

    def to_tabs_token(self, index):
        return [TabsToken(t[index["Token"]], t[index["Lemma"]], t[index["Pos"]], int(t[index["WordSep"]]))
                for t in self.tokens]

    def to_conll(self, index):
        # 'surface', 'lemma', 'tag', 'morph', 'head', 'rel', 'misc'
        return [ConllToken(t[index["Token"]], t[index["Lemma"]], t[index["Pos"]], "",
                           t[index["Head"]] if "Head" in index else "_",
                           t[index["Deprel"]] if "Deprel" in index else "_", int(t[index["WordSep"]]))
                for t in self.tokens]


class TabsDocument:
    def __init__(self, tabs_path: str):
        self.meta = {}
        self.index = {}
        self.index_short = {}
        self.tokid = {}
        self.sentences: List[TabsSentence] = []
        self.read(tabs_path)

    def add_column(self, name: str, shortname: str):
        self.index[name] = len(self.index)
        self.index_short[name] = shortname

    def read(self, tabs_path: str):
        tabs_file = open(tabs_path, "r")
        meta_sent = []
        tokens = []
        for line in tabs_file:
            line = line.strip()
            if line.startswith("%%$DDC:tokid"):
                self.tokid[line[len("%%$DDC:tokid."):line.find("=")]] = line[line.find("=") + 1:].strip()
            if line.startswith("%%$DDC:meta"):
                self.meta[line[len("%%$DDC:meta."):line.find("=")]] = line[line.find("=") + 1:].strip()
            elif line.startswith("%%$DDC:index"):
                name, shortname = line[line.find("=") + 1:].split(" ")
                self.index[name] = int(line[line.find("[") + 1:line.find("]")])
                self.index_short[name] = shortname
            elif line.startswith("%%$DDC:BREAK"):
                meta_sent.append(line[len('%%$DDC:BREAK.'):])
            elif line.strip() and not line.startswith("%%$DDC"):
                tokens.append(tuple(line.split("\t")))
            elif not line.strip() and tokens and meta_sent:
                self.sentences.append(TabsSentence(meta_sent, tokens))
                meta_sent = []
                tokens = []

    def as_tabs(self):
        buf = io.StringIO()
        for name, value in self.tokid.items():
            buf.write("%%$DDC:tokid.{}={}\n".format(name, value))
        for name, value in self.meta.items():
            buf.write("%%$DDC:meta.{}={}\n".format(name, value))
        for name, i in self.index.items():
            buf.write("%%$DDC:index[{}]={} {}\n".format(i, name, self.index_short[name]))
        for sent in self.sentences:
            for meta in sent.meta:
                buf.write("%%$DDC:BREAK.{}\n".format(meta))
            for token in sent.tokens:
                buf.write("{}\n".format("\t".join(map(str, token))))
            buf.write("\n")
        return buf.getvalue()

    def as_conllu(self):
        buf = io.StringIO()
        for name, value in self.tokid.items():
            buf.write("#DDC:tokid.{}={}\n".format(name, value))
        for name, value in self.meta.items():
            buf.write("#DDC:meta.{}={}\n".format(name, value))
        for name, i in self.index.items():
            buf.write("#DDC:index[{}]={} {}\n".format(i, name, self.index_short[name]))
        for sent in self.sentences:
            for meta in sent.meta:
                buf.write("#DDC:BREAK.{}\n".format(meta))
            for token_i, token in enumerate(sent.to_conll(self.index)):
                buf.write(
                    "{idx}\t{t.surface}\t{t.lemma}\t{t.tag}\t{t.tag}\t_\t{t.head}\t{t.rel}\t_\t_\t{t.misc}\n".format(
                        idx=token_i + 1, t=token))
            buf.write("\n")
        return buf.getvalue()

    def save(self, path):
        if not path.parent.exists():
            path.parent.mkdir(parents=True)
        with open(path, 'w') as fh:
            fh.write(self.as_tabs())


# TODO refactor parser generation - too complicated right now
def build_parser_from_args(cmd_args=None):
    argParser = argparse.ArgumentParser(description="""IMS BiLSTM Parser""", add_help=False)

    parserArgs = argParser.add_argument_group('parser')
    parserArgs.add_argument("--parser", help="which parser to use", choices=["GRAPH", "TRANS"], required=True)
    parserArgs.add_argument("--jobs", help="", type=int, default=1)
    parserArgs.add_argument("--normalize", help="normalize the words", type=bool, required=False, default=True)

    # files
    filesArgs = argParser.add_argument_group('files')
    filesArgs.add_argument("--src", help="source file", type=str, required=True)
    filesArgs.add_argument("--list", help="input file consists of whitespace separated input output files",
                           action="store_true", required=False)
    filesArgs.add_argument("--dest", help="source file destination", type=str, required=True)
    filesArgs.add_argument("--model", help="load model from the file", type=str, required=True)

    # parse for the first time to only get the parser name
    args, _ = argParser.parse_known_args(cmd_args)

    # parse the second time to get all the args
    options.addParserCmdArguments(args.parser, argParser)
    args = argParser.parse_args(cmd_args)

    opts = utils.NParserOptions()
    options.fillParserOptions(args, opts)
    opts.load(args.model + ".args")
    opts.logOptions()

    return args, opts


def process_files_parallel(srcs, args, options):
    parser = get_parser(args, options)
    for src_i, src in enumerate(srcs):
        doc = TabsDocument(src)
        tgt_path = Path(os.path.join(args.dest, doc.meta['collection'], os.path.basename(src)))
        if not tgt_path.exists() or (os.path.getmtime(tgt_path) < os.path.getmtime(src)):
            parse_document(parser, doc, options.normalize)
            logging.info("({}) - parsed document".format(doc.meta['basename']))
            doc.save(tgt_path)
        else:
            logging.info("({}) - SKIP - parsed document up-to-date".format(src))


def main():
    args, options = build_parser_from_args()
    src_files = glob("{}/**/*.tabs".format(args.src), recursive=True)
    if len(src_files) == 0:
        raise FileNotFoundError("No files found for parsing!")
    files = [(src, args, options) for src in chunks(src_files, 25)]
    logging.info("Create MPPool with #njobs:", args.jobs)
    with multiprocessing.Pool(args.jobs) as pool:
        pool.starmap(process_files_parallel, files, chunksize=10)


if __name__ == '__main__':
    main()
