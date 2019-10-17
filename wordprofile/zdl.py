import json
import os
from collections import namedtuple, defaultdict
from typing import List

from imsnpars.tools.utils import ConLLToken as IMSConllToken, ConLLToken

TabsToken = namedtuple("Token", ["surface", "lemma", "pos", "word_sep"])
ConllToken = namedtuple('ConllToken',
                        ['idx', 'surface', 'lemma', 'upos', 'xpos', 'morph', 'head', 'rel', 'feature', 'misc'])
NoneToken = ConllToken(-1, "-", "-", "-", "-", "-", -1, "-", '', 0)
Match = namedtuple('Match', ['head', 'dep', 'prep', 'relation', 'sid'])

simplified_pos = {
    'APPRART': 'APPR',
    'ADJA': 'ADJ',
    'ADJD': 'ADJ',
    'ADJC': 'ADJ',
    'KOKOM': 'KON',
    'PTKANT': 'PTKA',
    'VVFIN': 'VV',
    'VVINF': 'VV',
    'VVIZU': 'VV',
    'VVPP': 'VV',
    'VVPP1': 'VV',
    'VVPP2': 'VV',
    'VAFIN': 'VA',
    'VAIMP': 'VA',
    'VAINF': 'VA',
    'VAPP': 'VA',
    'VMFIN': 'VM',
    'VMINF': 'VM',
    'VMPP': 'VM',
}


def extract_binary_relations(tokens, sid):
    relations = []
    for token in tokens:
        if token.head == '0' or token.rel in ('--', '_', '-') or token.xpos.startswith('$'):
            continue
        thead = tokens[int(token.head) - 1]
        if thead.xpos.startswith('$'):
            continue
        relation_type = token.rel
        if relation_type:
            if relation_type == "ATTR" and token.xpos != "ADJA":
                continue
            if relation_type in ['PP-PN', 'KOM-CJ', 'SUBJ-PRED']:
                relations.append(Match(
                    thead,
                    token,
                    None,
                    relation_type,
                    sid,
                ))
            else:
                relations.append(Match(
                    thead,
                    token,
                    None,
                    relation_type,
                    sid,
                ))
    return relations


def extract_matches_from_document(parses):
    rel_dict = defaultdict(list)
    sid = 1
    for sentence in parses:
        relations = extract_binary_relations(sentence, sid)
        for r in relations:
            # TODO filter inconsistent relations
            #  - 0 is marked by parser
            if r.relation == "0":
                continue
            rel_dict[(r.relation, r.head.surface, r.dep.surface, r.head.xpos, r.dep.xpos)].append(r)
        sid += 1
    return rel_dict


def process_tj(src, fout):
    with open(os.path.abspath(src), 'r') as fin:
        idx = 1
        for line in fin:
            line = line.strip()
            if not line:
                fout.write('\n')
                idx = 1
            elif line.startswith('%%'):
                pass
            else:
                line = json.loads(line.split('\t')[1])
                fout.write("{}\t{}\t{}\t{}\t{}\t{}\t_\t_\t_\t_\n".format(
                    idx,
                    line['text'],
                    line['moot']['lemma'],
                    line['moot']['tag'],
                    line['moot']['tag'],
                    line['moot']['details']['details']
                ))
                idx += 1


def read_tabs_format(tabs_file_path):
    sentences = []
    sentence = []
    meta = {}
    index = {}
    tabs_file = open(tabs_file_path, "r")
    for line in tabs_file:
        line = line.strip()
        if line.startswith("%%$DDC:meta"):
            meta[line[len("%%$DDC:meta."):line.find("=")]] = line[line.find("=") + 1:].strip()
        elif line.startswith("%%$DDC:index"):
            name, shortname = line[line.find("=") + 1:].split(" ")
            index[name] = int(line[line.find("[") + 1:line.find("]")])
        elif line.startswith("%%$DDC:BREAK.s"):
            if sentence:
                sentences.append(sentence)
                sentence = []
        elif line and not line.startswith("%"):
            items = line.split("\t")
            sentence.append(
                TabsToken(items[index["Token"]], items[index["Lemma"]], items[index["Pos"]],
                          int(items[index["WordSep"]])))
    return meta, sentences


def tokenized_sentence_to_conll_token(sentence, normalizer=None):
    sentence_conll = []
    for token_i, token in enumerate(sentence):
        sentence_conll.append(
            IMSConllToken(tokId=token_i + 1,
                          orth=token.surface,
                          lemma=token.lemma,
                          pos=token.pos,
                          langPos=token.pos,
                          morph="",
                          headId=None,
                          dep=None,
                          norm=normalizer.norm(token.surface) if normalizer else None))
    return sentence_conll


def conll_token_to_tokenized_sentence(sentence_orig: List[TabsToken], sentence: List[ConLLToken]):
    sentence_conll = []
    for token_i, (tabs_token, pars_token) in enumerate(zip(sentence_orig, sentence)):
        sentence_conll.append(ConllToken(pars_token.tokId, pars_token.orth, pars_token.lemma, pars_token.pos,
                                         pars_token.langPos, pars_token.morph, pars_token.headId, pars_token.dep, '',
                                         tabs_token.word_sep))
    return sentence_conll
