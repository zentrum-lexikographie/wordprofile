#!/usr/bin/python3
import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from typing_extensions import Self

from preprocessing.pytabs.consts import UD_POS_MAP


@dataclass
class TabsToken:
    """Class for keeping track of tabs token."""

    surface: str
    lemma: str
    pos: str
    word_sep: int

    def __repr__(self) -> str:
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

    def __repr__(self) -> str:
        return f"ConllToken({self.surface},{self.lemma},{self.tag},{self.morph},{self.head},{self.rel},{self.misc})"


class TabsSentence:
    """Data structure for processing sentences in tabs files
    - stores also meta data referring to the sentence."""

    def __init__(self, meta: List[List[str]], tokens: Iterable) -> None:
        self.meta = meta
        self.tokens = tuple(tokens)

    def to_conll(self, index: Dict[str, int]) -> List[ConllToken]:
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

    def __repr__(self) -> str:
        return f"TabsSentence(meta={self.meta},tokens={self.tokens})"


class TabsDocument:
    """Data structure for processing tabs files and generate output in
    either tabs or conllu format."""

    def __init__(self) -> None:
        self.meta: Dict[str, str] = {}
        self.index: Dict[str, int] = {}
        self.index_short: Dict[str, str] = {}
        self.tokid: Dict[str, str] = {}
        self.sentences: List[TabsSentence] = []

    @classmethod
    def from_tabs(cls, tabs_path: str) -> Self:
        doc = cls()
        meta_sent = []
        tokens = []
        with open(tabs_path, "r") as tabs_file:
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
                elif line and not line.startswith("%%$DDC"):
                    tokens.append(tuple(line.split("\t")))
                elif not line and tokens and meta_sent:
                    doc.sentences.append(TabsSentence(meta_sent, _clean_tokens(tokens)))
                    meta_sent = []
                    tokens = []
        return doc

    def as_conllu(self) -> str:
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

    def save(self, path: Path) -> None:
        if isinstance(path, str):
            path = Path(path)
        if not path.parent.exists():
            path.parent.mkdir(parents=True)
        with open(path, "w") as fh:
            fh.write(self.as_conllu())

    def __repr__(self) -> str:
        return (
            f"TabsDocument(meta={self.meta},index={self.index},index_short={self.index_short},"
            f"tokid={self.tokid},sentences={self.sentences})"
        )


def _clean_tokens(tokens: list[tuple[str]]) -> list[tuple[str]]:
    cleaned = []
    for i, token in enumerate(tokens):
        if token[0] in {">", "<"}:
            continue
        elif match := re.match(r"<?\w+>(\w*)", token[0]):
            if clean_tok := match.group(1):
                new_token = (clean_tok, token[1], clean_tok, token[3])
                cleaned.append(new_token)
        elif match := re.match(r"([\w!?,.;:(){}\[\]\"]*)<(/\w+>)?", token[0]):
            if clean_tok := match.group(1):
                new_token = (clean_tok, token[1], clean_tok, token[3])
                cleaned.append(new_token)
        else:
            cleaned.append(token)
    return cleaned
