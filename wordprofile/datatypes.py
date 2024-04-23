import datetime
from collections import namedtuple
from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class LemmaInfo:
    lemma: str
    form: str
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
    prep_position: int
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
    prep_position: int
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
        return [self.token_position_1, self.token_position_2, self.prep_position]


@dataclass
class MweConcordance:
    sentence: str
    token1_position_1: int
    token1_position_2: int
    prep1_position: int
    token2_position_1: int
    token2_position_2: int
    prep2_position: int
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
        return [
            self.token1_position_1,
            self.token1_position_2,
            self.prep1_position,
            self.token2_position_1,
            self.token2_position_2,
            self.prep2_position,
        ]


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
    prt_pos: Optional[int] = None


Match = namedtuple("Match", ["head", "dep", "prep", "relation", "sid"])
DBCorpusFile = namedtuple(
    "DBCorpusFile",
    ["id", "corpus", "file", "orig", "scan", "date", "text_class", "available"],
)
DBConcordance = namedtuple(
    "DBConcordance", ["corpus_file_id", "sentence_id", "sentence", "page"]
)
DBMatch = namedtuple(
    "DBMatch",
    [
        "relation_label",
        "head_lemma",
        "dep_lemma",
        "head_tag",
        "dep_tag",
        "head_surface",
        "dep_surface",
        "head_position",
        "dep_position",
        "extra_position",
        "corpus_file_id",
        "sentence_id",
    ],
)

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
