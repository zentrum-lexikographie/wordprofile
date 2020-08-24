#!/usr/bin/python3
from collections import namedtuple

LemmaInfo = namedtuple("LemmaInfo", ["lemma", "tag", "rel", "freq", "inv"])
CooccInfo = namedtuple("CooccInfo", ["id", "rel", "lemma1", "lemma2", "pos1", "pos2", "inv", "has_mwe"])
Coocc = namedtuple("Coocc", ["RelId", "Rel", "Lemma1", "Lemma2", "Pos1", "Pos2",
                             "Frequency", "LogDice", "inverse", "has_mwe"])
Concordance = namedtuple("Concordance",
                         ["sentence", "token_position_1", "token_position_2", "prep_position", "corpus", "date",
                          "textclass", "orig", "scan", "avail", "page", "file", "score", "sentence_left",
                          "sentence_right"])
MweConcordance = namedtuple("Concordance",
                            ["sentence", "token1_position_1", "token1_position_2", "prep1_position",
                             "token2_position_1", "token2_position_2", "prep2_position",
                             "corpus", "date", "textclass", "orig", "scan",
                             "avail", "page", "file", "score",
                             "sentence_left", "sentence_right"])
DBToken = namedtuple('DBToken', ['idx', 'surface', 'lemma', 'tag', 'head', 'rel', 'misc'])
Match = namedtuple('Match', ['head', 'dep', 'prep', 'relation', 'sid'])
