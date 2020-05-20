#!/usr/bin/python3
import io
from collections import namedtuple
from typing import List, Iterable

LemmaInfo = namedtuple("LemmaInfo", ["lemma", "tag", "rel", "freq", "inv"])
CooccInfo = namedtuple("CooccInfo", ["id", "rel", "lemma1", "lemma2", "pos1", "pos2", "inv"])
Coocc = namedtuple("Coocc", ["RelId", "Rel", "Lemma1", "Lemma2", "Pos1", "Pos2",
                             "Frequency", "LogDice", "inverse"])
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
TabsToken = namedtuple("Token", ["surface", "lemma", "pos", "word_sep"])
ConllToken = namedtuple('ConllToken',
                        ['surface', 'lemma', 'tag', 'morph', 'head', 'rel', 'misc'])
DBToken = namedtuple('DBToken', ['idx', 'surface', 'lemma', 'tag', 'head', 'rel', 'misc'])
Match = namedtuple('Match', ['head', 'dep', 'prep', 'relation', 'sid'])


class TabsSentence:
    """Data structure for processing sentences in tabs files - stores also meta data referring to the sentence.
    """

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
    """Data structure for processing tabs files and generate output in either tabs or conllu format.
    """

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
                doc.tokid[line[len("%%$DDC:tokid."):line.find("=")]] = line[line.find("=") + 1:].strip()
            if line.startswith("%%$DDC:meta"):
                doc.meta[line[len("%%$DDC:meta."):line.find("=")]] = line[line.find("=") + 1:].strip()
            elif line.startswith("%%$DDC:index"):
                name, shortname = line[line.find("=") + 1:].split(" ")
                doc.index[name] = int(line[line.find("[") + 1:line.find("]")])
                doc.index_short[name] = shortname
            elif line.startswith("%%$DDC:BREAK"):
                meta_sent.append(line[len('%%$DDC:BREAK.'):])
            elif line.strip() and not line.startswith("%%$DDC"):
                tokens.append(tuple(line.split("\t")))
            elif not line.strip() and tokens and meta_sent:
                doc.sentences.append(TabsSentence(meta_sent, tokens))
                meta_sent = []
                tokens = []
        return doc

    @staticmethod
    def from_conll(conll_path: str):
        doc = TabsDocument()
        tabs_file = open(conll_path, "r")
        meta_sent = []
        tokens = []
        for line in tabs_file:
            line = line.strip()
            if line.startswith("#DDC:tokid"):
                doc.tokid[line[len("%%$DDC:tokid."):line.find("=")]] = line[line.find("=") + 1:].strip()
            if line.startswith("#DDC:meta"):
                doc.meta[line[len("#DDC:meta."):line.find("=")]] = line[line.find("=") + 1:].strip()
            elif line.startswith("#DDC:BREAK"):
                meta_sent.append(line[len('#DDC:BREAK.'):])
            elif line.strip() and not line.startswith("#"):
                tokens.append(tuple(line.split("\t")))
            elif not line.strip() and tokens and meta_sent:
                doc.sentences.append(TabsSentence(meta_sent, tokens))
                meta_sent = []
                tokens = []
        for i, (name, shortname) in enumerate(
                [("Index", "idx"), ("Token", "t"), ("Lemma", "l"), ("Pos", "pos"), ("XPos", "xpos"), ("Morph", "m"),
                 ("Head", "hd"), ("Deprel", "rel"), ("Unknown", "ukn"), ("WordSep", "ws")]):
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
        for sent in self.sentences:
            for meta in sent.meta:
                buf.write("#DDC:BREAK.{}\n".format(meta))
            conll_sent = sent.to_conll(self.index)
            buf.write("# {}\n".format(" ".join(t.surface for t in conll_sent)))
            for token_i, token in enumerate(conll_sent):
                buf.write(
                    "{idx}\t{t.surface}\t{t.lemma}\t{xpos}\t{t.tag}\t_\t{t.head}\t{t.rel}\t_\t{t.misc}\n".format(
                        idx=token_i + 1, t=token, xpos=ud_pos_map.get(token.tag)))
            buf.write("\n")
        return buf.getvalue()

    def save(self, path, as_conll=False):
        if not path.parent.exists():
            path.parent.mkdir(parents=True)
        with open(path, 'w') as fh:
            if as_conll:
                fh.write(self.as_conllu())
            else:
                fh.write(self.as_tabs())


# Taken from https://universaldependencies.org/tagset-conversion/
ud_pos_map = {
    "$(": "PUNCT",  # "	PunctType=Brck	``, '', *RRB*, *LRB*, -
    "$,": "PUNCT",  # "	PunctType=Comm	,
    "$.": "PUNCT",  # "	PunctType=Peri	., :, ?, ;, !
    "ADJA": "ADJ",  # _	neuen, neue, deutschen, ersten, anderen
    "ADJD": "ADJ",  # Variant=Short	gut, rund, knapp, deutlich, möglich
    "ADV": "ADV",  # _	auch, nur, noch, so, aber
    "APPO": "ADP",  # AdpType=Post	zufolge, nach, gegenüber, wegen, über
    "APPR": "ADP",  # AdpType=Prep	in, von, mit, für, auf
    "APPRART": "ADP",  # AdpType=Prep|PronType=Art	im, am, zum, zur, vom
    "APZR": "ADP",  # AdpType=Circ	an, hinaus, aus, her, heraus
    "ART": "DET",  # PronType=Art	der, die, den, des, das
    "CARD": "NUM",  # NumType=Card	000, zwei, drei, vier, fünf
    "FM": "X",  # Foreign=Yes	New, of, de, Times, the
    "ITJ": "INTJ",  # _	naja, Ach, äh, Na, piep
    "KOKOM": "CCONJ",  # ConjType=Comp	als, wie, denn, wir
    "KON": "CCONJ",  # _	und, oder, sondern, sowie, aber
    "KOUI": "SCONJ",  # _	um, ohne, statt, anstatt, Ums
    "KOUS": "SCONJ",  # _	daß, wenn, weil, ob, als
    "NE": "PROPN",  # _	SPD, Deutschland, USA, dpa, Bonn
    "NN": "NOUN",  # _	Prozent, Mark, Millionen, November, Jahren
    "PAV": "ADV",  # PronType=Dem
    "PDAT": "DET",  # PronType=Dem	dieser, diese, diesem, dieses, diesen
    "PDS": "PRON",  # PronType=Dem	das, dies, die, diese, der
    "PIAT": "DET",  # PronType=Ind,Neg,Tot	keine, mehr, alle, kein, beiden
    "PIDAT": "DET",  # AdjType=Pdt|PronType=Ind,Neg,Tot
    "PIS": "PRON",  # PronType=Ind,Neg,Tot	man, allem, nichts, alles, mehr
    "PPER": "PRON",  # PronType=Prs	es, sie, er, wir, ich
    "PPOSAT": "DET",  # Poss=Yes|PronType=Prs	ihre, seine, seiner, ihrer, ihren
    "PPOSS": "PRON",  # Poss=Yes|PronType=Prs	ihren, Seinen, seinem, unsrigen, meiner
    "PRELAT": "DET",  # PronType=Rel	deren, dessen, die
    "PRELS": "PRON",  # PronType=Rel	die, der, das, dem, denen
    "PRF": "PRON",  # PronType=Prs|Reflex=Yes	sich, uns, mich, mir, dich
    "PTKA": "PART",  # _	zu, am, allzu, Um
    "PTKANT": "PART",  # PartType=Res	nein, ja, bitte, Gewiß, Also
    "PTKNEG": "PART",  # Polarity=Neg	nicht
    "PTKVZ": "ADP",  # PartType=Vbp	an, aus, ab, vor, auf
    "PTKZU": "PART",  # PartType=Inf	zu, zur, zum
    "PWAT": "DET",  # PronType=Int	welche, welchen, welcher, wie, welchem
    "PWAV": "ADV",  # PronType=Int	wie, wo, warum, wobei, wonach
    "PWS": "PRON",  # PronType=Int	was, wer, wem, wen, welches
    "TRUNC": "X",  # Hyph=Yes	Staats-, Industrie-, Finanz-, Öl-, Lohn-
    "VAFIN": "AUX",  # Mood=Ind|VerbForm=Fin	ist, hat, wird, sind, sei
    "VAIMP": "AUX",  # Mood=Imp|VerbForm=Fin	Seid, werde, Sei
    "VAINF": "AUX",  # VerbForm=Inf	werden, sein, haben, worden, Dabeisein
    "VAPP": "AUX",  # Aspect=Perf|VerbForm=Part	worden, gewesen, geworden, gehabt, werden
    "VMFIN": "VERB",  # Mood=Ind|VerbForm=Fin|VerbType=Mod	kann, soll, will, muß, sollen
    "VMINF": "VERB",  # VerbForm=Inf|VerbType=Mod	können, müssen, wollen, dürfen, sollen
    "VMPP": "VERB",  # Aspect=Perf|VerbForm=Part|VerbType=Mod	gewollt
    "VVFIN": "VERB",  # Mood=Ind|VerbForm=Fin	sagte, gibt, geht, steht, kommt
    "VVIMP": "VERB",  # Mood=Imp|VerbForm=Fin	siehe, sprich, schauen, Sagen, gestehe
    "VVINF": "VERB",  # VerbForm=Inf	machen, lassen, bleiben, geben, bringen
    "VVIZU": "VERB",  # VerbForm=Inf	einzusetzen, durchzusetzen, aufzunehmen, abzubauen, umzusetzen
    "VVPP": "VERB",  # Aspect=Perf|VerbForm=Part	gemacht, getötet, gefordert, gegeben, gestellt
    "XY": "X",  # _	dpa, ap, afp, rtr, wb
}
