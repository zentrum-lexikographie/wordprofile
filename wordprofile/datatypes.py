from collections import namedtuple

LemmaInfo = namedtuple("LemmaInfo", ["lemma", "tag", "rel", "freq", "inv"])
CooccInfo = namedtuple("CooccInfo", ["rel", "lemma1", "lemma2", "pos1", "pos2", "inv"])
Coocc = namedtuple("Coocc", ["RelId", "Rel", "Lemma1", "Lemma2", "Pos1", "Pos2",
                             "Frequency", "LogDice", "inverse"])
Concordance = namedtuple("Concordance",
                         ["sentence", "token_position_1", "token_position_2", "prep_position", "corpus", "date",
                          "textclass", "orig", "scan", "avail", "page", "file", "score", "sentence_left",
                          "sentence_right"])
TabsToken = namedtuple("Token", ["surface", "lemma", "pos", "word_sep"])
ConllToken = namedtuple('ConllToken',
                        ['surface', 'lemma', 'tag', 'morph', 'head', 'rel', 'misc'])
DBToken = namedtuple('DBToken', ['idx', 'surface', 'lemma', 'tag', 'head', 'rel', 'misc'])
Match = namedtuple('Match', ['head', 'dep', 'prep', 'relation', 'sid'])
