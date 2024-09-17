from __future__ import annotations

import datetime
from collections import namedtuple
from dataclasses import asdict, dataclass
from typing import Optional, Protocol


@dataclass
class LemmaInfo:
    lemma: str
    tag: str
    rel: str
    freq: int
    inv: int


@dataclass
class Coocc:
    id: int
    rel: str
    lemma1: str
    lemma2: str
    form1: str
    form2: str
    tag1: str
    tag2: str
    freq: int
    score: float
    inverse: int
    has_mwe: int
    num_concords: int


@dataclass
class WPConcordance(Protocol):
    sentence: str
    token_position_1: int
    token_position_2: int
    extra_position: int
    corpus: str
    date: datetime.date
    textclass: str
    orig: str
    scan: str
    avail: str
    page: str
    file: str
    score: int
    sentence_left: str
    sentence_right: str

    def get_highlight_positions(self) -> list[int]:
        """Returns list of indices of target tokens."""
        ...


@dataclass
class Concordance:
    sentence: str
    token_position_1: int
    token_position_2: int
    extra_position: str
    corpus: str
    date: datetime.date
    textclass: str
    orig: str
    scan: str
    avail: str
    page: str
    file: str
    score: int
    sentence_left: str
    sentence_right: str

    def get_highlight_positions(self) -> list[int]:
        extra_positions = [int(pos) for pos in self.extra_position.split("-") if pos]
        return sorted([self.token_position_1, self.token_position_2] + extra_positions)


@dataclass
class MweConcordance:
    sentence: str
    token1_position_1: int
    token1_position_2: int
    extra1_position: str
    token2_position_1: int
    token2_position_2: int
    extra2_position: str
    corpus: str
    date: datetime.date
    textclass: str
    orig: str
    scan: str
    avail: str
    page: str
    file: str
    score: int
    sentence_left: str
    sentence_right: str

    def get_highlight_positions(self) -> list[int]:
        extra_positions1 = [int(pos) for pos in self.extra1_position.split("-") if pos]
        extra_positions2 = [int(pos) for pos in self.extra2_position.split("-") if pos]
        all_positions = (
            [
                self.token1_position_1,
                self.token1_position_2,
                self.token2_position_1,
                self.token2_position_2,
            ]
            + extra_positions1
            + extra_positions2
        )
        return sorted(all_positions)


@dataclass
class WPToken:
    """
    Represents a token with information relevant for wordprofile
    """

    idx: int
    surface: str
    lemma: str
    tag: str
    head: int
    rel: str
    misc: bool
    morph: Optional[dict[str, str]] = None
    prt_pos: Optional[int] = None


Match = namedtuple("Match", ["head", "dep", "prep", "relation", "sid"])
DBCorpusFile = namedtuple(
    "DBCorpusFile",
    ["id", "corpus", "file", "orig", "scan", "date", "text_class", "available"],
)
DBConcordance = namedtuple(
    "DBConcordance", ["corpus_file_id", "sentence_id", "sentence", "page"]
)


@dataclass
class DBMatch:
    relation_label: str
    head_lemma: str
    dep_lemma: str
    head_tag: str
    dep_tag: str
    prep: str
    head_surface: str
    dep_surface: str
    head_position: int
    dep_position: int
    extra_position: str
    corpus_file_id: str
    sentence_id: int

    def __iter__(self):
        yield from asdict(self).values()

    @classmethod
    def fromline(cls, line: str) -> DBMatch:
        args = line.strip().split("\t")
        if len(args) != 13:
            raise ValueError
        return cls(
            relation_label=args[0],
            head_lemma=args[1],
            dep_lemma=args[2],
            head_tag=args[3],
            dep_tag=args[4],
            prep=args[5],
            head_surface=args[6],
            dep_surface=args[7],
            head_position=int(args[8]),
            dep_position=int(args[9]),
            extra_position=args[10],
            corpus_file_id=args[11],
            sentence_id=int(args[12]),
        )

    def get_collocation_key(self) -> str:
        return "-".join(
            [
                self.relation_label,
                self.head_lemma,
                self.dep_lemma,
                self.head_tag,
                self.dep_tag,
                self.prep,
            ]
        )

    def convert_to_database_entry(self, idx: int, collocation_id: int) -> str:
        sep = "\t"
        match_info = [
            self.head_surface,
            self.dep_surface,
            self.head_position,
            self.dep_position,
            self.extra_position,
            self.corpus_file_id,
            self.sentence_id,
        ]
        return f"{idx}\t{collocation_id}\t{sep.join(map(str, match_info))}"


CollocInstance = namedtuple(
    "CollocInstance",
    [
        "id",
        "collocation_id",
        "head_surface",
        "dep_surface",
        "head_pos",
        "dep_pos",
        "prep_pos",
        "doc_id",
        "sent_id",
    ],
)
Colloc = namedtuple(
    "Colloc",
    ["id", "label", "lemma1", "lemma2", "lemma1_tag", "lemma2_tag", "inv", "frequency"],
)


class DependencyTree:
    class Node:
        def __init__(self, token: WPToken) -> None:
            self.token = token
            self.parent: Optional["DependencyTree.Node"] = None
            self.children: list["DependencyTree.Node"] = []

        def add_child(self, token: "DependencyTree.Node") -> None:
            if token not in self.children:
                self.children.append(token)

        def is_root(self) -> bool:
            return self.parent is None

    def __init__(self, tokens: list[WPToken]) -> None:
        self.nodes = [DependencyTree.Node(token) for token in tokens]
        self.root: Optional[DependencyTree.Node] = None
        for n in self.nodes:
            if int(n.token.head) > 0:
                n.parent = self.nodes[int(n.token.head) - 1]
                self.nodes[int(n.token.head) - 1].add_child(n)
            else:
                self.root = n
