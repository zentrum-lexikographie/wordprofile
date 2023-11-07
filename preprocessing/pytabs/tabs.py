#!/usr/bin/python3
import io
from dataclasses import dataclass
from pathlib import Path
from typing import List, Iterable

from preprocessing.pytabs.consts import UD_POS_MAP


@dataclass
class TabsToken:
    """Class for keeping track of tabs token."""

    surface: str
    lemma: str
    pos: str
    word_sep: int

    def __repr__(self):
        return f"TabsToken({self.surface},{self.lemma},{self.pos},{self.word_sep}"


@dataclass
class ConllToken:
    """Class for keeping track of tabs token."""

    surface: str
    lemma: str
    tag: str
    morph: str
    head: str
    rel: str
    misc: str

    def __repr__(self):
        return f"ConllToken({self.surface},{self.lemma},{self.tag},{self.morph},{self.head},{self.rel},{self.misc})"


class TabsSentence:
    """Data structure for processing sentences in tabs files
    - stores also meta data referring to the sentence."""

    def __init__(self, meta: List[List[str]], tokens: Iterable):
        self.meta = meta
        self.tokens = tuple(tokens)

    def add_column(self, column_items: Iterable):
        self.tokens = [row + (item,) for row, item in zip(self.tokens, column_items)]

    def to_tabs_token(self, index):
        return [
            TabsToken(
                t[index["Token"]],
                t[index["Lemma"]],
                t[index["Pos"]],
                int(t[index["WordSep"]]),
            )
            for t in self.tokens
        ]

    def to_conll(self, index):
        # 'surface', 'lemma', 'tag', 'morph', 'head', 'rel', 'misc'
        tokens = [
            ConllToken(
                t[index["Token"]],
                t[index["Lemma"]],
                t[index["Pos"]],
                "",
                t[index["Head"]] if "Head" in index else "_",
                t[index["Deprel"]] if "Deprel" in index else "_",
                str(t[index["WordSep"]]),
            )
            for t in self.tokens
        ]
        for t_i, t in enumerate(tokens):
            if t_i > 0 and t.misc == "0":
                tokens[t_i - 1].misc = "SpaceAfter=No"
            else:
                tokens[t_i - 1].misc = "_"
            tokens[-1].misc = "_"
        return tokens

    def __repr__(self):
        return f"TabsSentence(meta={self.meta},tokens={self.tokens})"


class TabsDocument:
    """Data structure for processing tabs files and generate output in
    either tabs or conllu format."""

    def __init__(self):
        self.meta = {}
        self.index = {}
        self.index_short = {}
        self.tokid = {}
        self.sentences: List[TabsSentence] = []

    def add_column(self, name: str, shortname: str):
        self.index[name] = len(self.index)
        self.index_short[name] = shortname

    @staticmethod
    def from_tabs(tabs_path: str):
        doc = TabsDocument()
        tabs_file = open(tabs_path, "r")
        meta_sent = []
        tokens = []
        for line in tabs_file:
            line = line.strip()
            if line.startswith("%%$DDC:tokid"):
                doc.tokid[line[len("%%$DDC:tokid.") : line.find("=")]] = line[
                    line.find("=") + 1 :
                ].strip()
            if line.startswith("%%$DDC:meta"):
                doc.meta[line[len("%%$DDC:meta.") : line.find("=")]] = line[
                    line.find("=") + 1 :
                ].strip()
            elif line.startswith("%%$DDC:index"):
                name, shortname = line[line.find("=") + 1 :].split(" ")
                doc.index[name] = int(line[line.find("[") + 1 : line.find("]")])
                doc.index_short[name] = shortname
            elif line.startswith("%%$DDC:BREAK"):
                meta_sent.append(line[len("%%$DDC:BREAK.") :].split("="))
            elif line.strip() and not line.startswith("%%$DDC"):
                tokens.append(tuple(line.split("\t")))
            elif not line.strip() and tokens and meta_sent:
                doc.sentences.append(TabsSentence(meta_sent, tokens))
                meta_sent = []
                tokens = []
        return doc

    def remove_xml_tags_from_tabs(self):
        """Removes invalid xml fragments from token.

        Makes comparison on sentence level, e.g. consecutive token with
        separated parts of xml tags.
        """
        for sent in self.sentences:
            tokens = sent.to_tabs_token(self.index)
            tokens_new = []
            for tok_i, tok in enumerate(sent.tokens):
                if tokens[tok_i].surface in [
                    "<",
                    "/><",
                    "strong>",
                    "p>",
                    ">",
                    "/></p><p>",
                    "</p><p>",
                    "/>",
                    "/></p><p>",
                    "/><a",
                ]:
                    continue
                if (
                    tok_i > 0
                    and tokens[tok_i].surface in ["strong", "p", "a", "br", "/"]
                    and tokens[tok_i - 1].surface[-1] == "<"
                ):
                    continue
                for s in ["<", "strong>", "></p"]:
                    tok = list(tok)
                    if tokens[tok_i].surface.startswith(s):
                        tok[self.index["Token"]] = tok[self.index["Token"]][len(s) :]
                        tok[self.index["Lemma"]] = tok[self.index["Lemma"]][len(s) :]
                    if tokens[tok_i].surface.endswith(s):
                        tok[self.index["Token"]] = tok[self.index["Token"]][: -len(s)]
                        tok[self.index["Lemma"]] = tok[self.index["Lemma"]][: -len(s)]
                    if not tok[self.index["Token"]]:
                        continue
                tokens_new.append(tuple(tok))
            sent.tokens = tokens_new

    def remove_invalid_sentence(self):
        """Removes sentences with less than three valid token.

        A valid token is defined by any POS tag except punctuation and unknown.
        """

        def is_valid_word(tag):
            return UD_POS_MAP.get(tag, "X") not in ["PUNCT", "X"]

        sents_valid = []
        for sent in self.sentences:
            tokens = sent.to_tabs_token(self.index)
            nb_valid_pos = sum(int(is_valid_word(t.pos)) for t in tokens)
            if nb_valid_pos > 3:
                sents_valid.append(sent)
        self.sentences = sents_valid

    @staticmethod
    def from_conll(conll_path: str):
        doc = TabsDocument()
        tabs_file = open(conll_path, "r")
        meta_sent = []
        tokens = []
        for line in tabs_file:
            line = line.strip()
            if line.startswith("# DDC:tokid"):
                doc.tokid[line[len("%%$DDC:tokid.") : line.find("=")].strip()] = line[
                    line.find("=") + 2 :
                ].strip()
            if line.startswith("# DDC:meta"):
                doc.meta[line[len("# DDC:meta.") : line.find("=")].strip()] = line[
                    line.find("=") + 2 :
                ].strip()
            elif line.startswith("# DDC:BREAK"):
                meta_sent.append(line[len("# DDC:BREAK.") :].split(" = "))
            elif line.strip() and not line.startswith("#"):
                tokens.append(tuple(line.split("\t")))
            elif not line.strip() and tokens and meta_sent:
                doc.sentences.append(TabsSentence(meta_sent, tokens))
                meta_sent = []
                tokens = []
        for i, (name, shortname) in enumerate(
            [
                ("Index", "idx"),
                ("Token", "t"),
                ("Lemma", "l"),
                ("Pos", "pos"),
                ("XPos", "xpos"),
                ("Morph", "m"),
                ("Head", "hd"),
                ("Deprel", "rel"),
                ("Unknown", "ukn"),
                ("WordSep", "ws"),
            ]
        ):
            doc.index[name] = i
            doc.index_short[name] = shortname
        return doc

    def as_tabs(self):
        buf = io.StringIO()
        for name, value in self.tokid.items():
            buf.write("%%$DDC:tokid.{}={}\n".format(name, value))
        for name, value in self.meta.items():
            buf.write("%%$DDC:meta.{}={}\n".format(name, value))
        for name, i in self.index.items():
            buf.write(
                "%%$DDC:index[{}]={} {}\n".format(i, name, self.index_short[name])
            )
        for sent in self.sentences:
            for meta_name, meta_val in sent.meta:
                buf.write("%%$DDC:BREAK.{}={}\n".format(meta_name, meta_val))
            for token in sent.tokens:
                buf.write("{}\n".format("\t".join(map(str, token))))
            buf.write("\n")
        return buf.getvalue()

    def as_conllu(self):
        buf = io.StringIO()
        for name, value in self.tokid.items():
            buf.write("# DDC:tokid.{} = {}\n".format(name, value))
        for name, value in self.meta.items():
            buf.write("# DDC:meta.{} = {}\n".format(name, value))
        for sent in self.sentences:
            for meta_name, meta_val in sent.meta:
                buf.write("# DDC:BREAK.{} = {}\n".format(meta_name, meta_val))
            conll_sent = sent.to_conll(self.index)
            buf.write("# text = {}\n".format(" ".join(t.surface for t in conll_sent)))
            for token_i, token in enumerate(conll_sent):
                buf.write(
                    "{idx}\t{t.surface}\t{t.lemma}\t{xpos}\t{t.tag}\t_\t{t.head}\t{t.rel}\t_\t{t.misc}\n".format(
                        idx=token_i + 1, t=token, xpos=UD_POS_MAP.get(token.tag, "X")
                    )
                )
            buf.write("\n")
        return buf.getvalue()

    def save(self, path, as_conll=False):
        if isinstance(path, str):
            path = Path(path)
        if not path.parent.exists():
            path.parent.mkdir(parents=True)
        with open(path, "w") as fh:
            if as_conll:
                fh.write(self.as_conllu())
            else:
                fh.write(self.as_tabs())

    def __repr__(self):
        return (
            f"TabsDocument(meta={self.meta},index={self.index},index_short={self.index_short},"
            f"tokid={self.tokid},sentences={self.sentences})"
        )
