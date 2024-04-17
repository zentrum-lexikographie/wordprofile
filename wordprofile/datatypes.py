import datetime
from collections import namedtuple
from dataclasses import dataclass
from typing import Optional


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


@dataclass
class DBToken:
    idx: int
    surface: str
    lemma: str
    tag: str
    head: int
    rel: str
    misc: bool


Match = namedtuple("Match", ["head", "dep", "prep", "relation", "sid"])


class DependencyTree:
    class Node:
        def __init__(self, token: DBToken) -> None:
            self.token = token
            self.parent: Optional["DependencyTree.Node"] = None
            self.children: list["DependencyTree.Node"] = []

        def add_child(self, token: "DependencyTree.Node") -> None:
            if token not in self.children:
                self.children.append(token)

        def is_root(self) -> bool:
            return self.parent is None

    def __init__(self, tokens: list[DBToken]) -> None:
        self.nodes = [DependencyTree.Node(token) for token in tokens]
        self.root: Optional[DependencyTree.Node] = None
        for n in self.nodes:
            if int(n.token.head) > 0:
                n.parent = self.nodes[int(n.token.head) - 1]
                self.nodes[int(n.token.head) - 1].add_child(n)
            else:
                self.root = n
