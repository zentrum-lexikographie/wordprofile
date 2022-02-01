import datetime
from collections import namedtuple
from dataclasses import dataclass
from typing import List


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
    tag1: str
    tag2: str
    freq: int
    score: float
    inverse: int
    has_mwe: int


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


DBToken = namedtuple('DBToken', ['idx', 'surface', 'lemma', 'tag', 'head', 'rel', 'misc'])
Match = namedtuple('Match', ['head', 'dep', 'prep', 'relation', 'sid'])


class DependencyTree:
    class Node:
        def __init__(self, token: DBToken):
            self.token = token
            self.parent = None
            self.children = []

        def add_child(self, token):
            if token not in self.children:
                self.children.append(token)

        def is_root(self):
            return self.parent is None

    def __init__(self, tokens: List[DBToken]):
        self.nodes = [DependencyTree.Node(token) for token in tokens]
        self.root = None
        for n in self.nodes:
            if int(n.token.head) > 0:
                n.parent = self.nodes[int(n.token.head) - 1]
                self.nodes[int(n.token.head) - 1].add_child(n)
            else:
                self.root = n
