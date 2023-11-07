#!/usr/bin/python3

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
