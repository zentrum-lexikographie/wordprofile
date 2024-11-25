#!/usr/bin/python3
import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from typing_extensions import Self

from wordprofile.preprocessing.pytabs.consts import UD_POS_MAP


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

    def __init__(
        self,
        meta: list[list[str]],
        tokens: list[tuple[str, ...]],
        index_map: Optional[dict[str, int]] = None,
    ) -> None:
        self.meta = meta
        self._idx = (
            {"Token": 0, "Pos": 1, "Lemma": 2, "WordSep": 3}
            if index_map is None
            else index_map
        )
        self.tokens = self._clean_sentence(tokens)

    def to_conll(self, index: dict[str, int]) -> list[ConllToken]:
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
        # .tabs encodes space before current token
        # convert information to space after for previous token
        if not tokens:
            return []
        for t_i, t in enumerate(tokens):
            if t_i == 0:
                continue
            if t.misc == "0":
                tokens[t_i - 1].misc = "SpaceAfter=No"
            else:
                tokens[t_i - 1].misc = "_"
        tokens[-1].misc = "_"
        return tokens

    def __repr__(self) -> str:
        return f"TabsSentence(meta={self.meta},tokens={self.tokens})"

    def _clean_sentence(
        self, tokens: list[tuple[str, ...]]
    ) -> tuple[tuple[str, ...], ...]:
        cleaned: list[tuple[str, ...]] = []
        for token in tokens:
            if token[self._idx["Token"]] in {">", "<"}:
                continue
            cleaned_token = self._clean_token(token)
            if cleaned_token is None:
                continue
            cleaned.append(cleaned_token)
        return tuple(cleaned)

    def _clean_token(self, token: tuple[str, ...]) -> Optional[tuple[str, ...]]:
        new_token = [part for part in token]
        clean_token = self._remove_xml_fragments(token[self._idx["Token"]])
        if not clean_token:
            return None
        clean_lemma = self._remove_xml_fragments(token[self._idx["Lemma"]])
        new_token[self._idx["Token"]] = clean_token
        new_token[self._idx["Lemma"]] = clean_lemma if clean_lemma else clean_token
        return tuple(new_token)

    def _remove_xml_fragments(self, token: str) -> str:
        if match := re.match(r"<?\w+>(\w*)", token):
            return match.group(1)
        elif match := re.match(r"([\w!?,.;:(){}\[\]\"]*)<(/\w+>)?", token):
            return match.group(1)
        return token


class TabsDocument:
    """Data structure for processing tabs files and generate output in
    either tabs or conllu format."""

    def __init__(self) -> None:
        self.meta: dict[str, str] = {}
        self.index: dict[str, int] = {}
        self.index_short: dict[str, str] = {}
        self.tokid: dict[str, str] = {}
        self.sentences: list[TabsSentence] = []

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
                    doc.sentences.append(TabsSentence(meta_sent, tokens, doc.index))
                    meta_sent = []
                    tokens = []
        return doc

    def as_conllu(self) -> str:
        buf = io.StringIO()
        for name, value in self.tokid.items():
            buf.write("# DDC:tokid.{} = {}\n".format(name, value))
        for name, value in self.meta.items():
            if value != "":
                buf.write("# DDC:meta.{} = {}\n".format(name, value))
        for sent in self.sentences:
            for meta_name, meta_val in sent.meta:
                buf.write("# DDC:BREAK.{} = {}\n".format(meta_name, meta_val))
            conll_sent = sent.to_conll(self.index)
            if not conll_sent:
                continue
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
