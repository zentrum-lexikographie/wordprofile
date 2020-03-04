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
    'APPR': 'APP',
    'APPO': 'APP',
    'APPRART': 'APP',
    'ADJA': 'ADJ',
    'ADJD': 'ADJ',
    # 'ADJC': 'ADJ',
    'NN': 'NN',
    # 'PPER': 'PP',
    'VVFIN': 'VV',
    'VVINF': 'VV',
    'VVIZU': 'VV',
    'VVPP': 'VV',
    'VVPP1': 'VV',
    'VVPP2': 'VV',
    'VVIMP': 'VV',
    'VAFIN': 'VA',
    'VAIMP': 'VA',
    'VAINF': 'VA',
    'VAPP': 'VA',
    'VMFIN': 'VM',
    'VMINF': 'VM',
    'VMPP': 'VM',
}

# rel_map : (rel, head_pos, dep_pos)
relations = {
    "KON": [("CJ", "NN", "NN"),
            # ("CJ", "PP", "NN"),
            # ("CJ", "NN", "PP"),
            # ("CJ", "PP", "PP"),
            ("CJ", "ADJ", "ADJ"),
            ("CJ", "VV", "VV"),
            ],
    "GMOD": [("GMOD", "NN", "NN"),
             ],
    # "SUBJA": [("SUBJA", "VV", "NN"),
    #           ("SUBJA", "VV", "PP"),
    #           ],
    # "SUBJP": [("SUBJP", "VV", "NN"),
    #           ("SUBJP", "VV", "PP"),
    #           ],
    "OBJ": [("OBJA", "VV", "NN"),
            # ("OBJA", "VV", "PP"),
            ("OBJD", "VV", "NN"),
            # ("OBJD", "VV", "PP"),
            ],
    "PRED": [("PRED", "NN", "NN"),
             ("PRED", "NN", "ADJ"),
             # ("PRED", "PP", "NN"),
             # ("PRED", "NN", "PP"),
             # ("PRED", "PP", "PP"),
             # ("PRED", "PP", "ADJ"),
             ("SUBJ", "NN", "NN"),
             ("SUBJ", "NN", "ADJ"),
             # ("SUBJ", "PP", "NN"),
             # ("SUBJ", "NN", "PP"),
             # ("SUBJ", "PP", "PP"),
             # ("SUBJ", "PP", "ADJ"),
             ],
    "ADV": [("ADV", "VV", "ADJ"),
            ("ADV", "VV", "ADV"),
            # ("ADV", "VV", "PTKNEG"),
            ("ADV", "ADJ", "ADJ"),
            ("ADV", "ADJ", "ADV"),
            # ("ADV", "ADJ", "PTKNEG"),
            ],
    "ATTR": [("ATTR", "NN", "ADJ"),
             ],
    # "KOM": [("KOM", "CJ", "NN", "NN", "KOKOM"),
    #         ("KOM", "CJ", "NN", "PPER", "KOKOM"),
    #         ("KOM", "CJ", "PPER", "NN", "KOKOM"),
    #         ("KOM", "CJ", "PPER", "PPER", "KOKOM"),
    #         ("KOM", "CJ", "VV", "NN", "KOKOM"),
    #         ("KOM", "CJ", "VV", "PPER", "KOKOM"),
    #         ],
    # "PP": [("PP", "PN", "NN", "NN", "APPR"),
    #        ("PP", "PN", "NN", "PPER", "APPR"),
    #        ("PP", "PN", "PPER", "NN", "APPR"),
    #        ("PP", "PN", "PPER", "PPER", "APPR"),
    #        ("PP", "PN", "VV", "NN", "APPR"),
    #        ("PP", "PN", "VV", "PPER", "APPR"),
    #        ],
    "VZ": [("VZ", "VV", "VV"),
           ("AVZ", "VV", "VV"),
           ],
}

relations_inv = defaultdict(lambda: defaultdict(str))
for relation_dest, relation_patters in relations.items():
    for relation_src, head_pos, dep_pos in relation_patters:
        relations_inv[relation_src][(head_pos, dep_pos)] = relation_dest
relations_inv = {k: dict(vd) for k, vd in relations_inv.items()}

wp_pos_of_interest = {
    "ADJ": "Adjektiv",
    "ADV": "Adverb",
    "PPER": "Personalpronomen",
    "APPR": "Präposition",
    "APPO": "Postposition",
    "APZR": "Zirkumposition",
    "ART": "Artikel",
    "ITJ": "Interjektion",
    "KOUI": "Konjunktion",
    "KON": "Konjunktion",
    "KOM": "Konjunktion",
    "PTKNEG": "Negationspartikel",
    "PTKVZ": "Verbpartikel",
    "NN": "Substantiv",
    "XY": "Substantiv",
    "CARD": "Kardinalzahl",
    "VV": "Verb",
    "VA": "Auxiliar",
    "VM": "Modalverb",
}


def extract_binary_relations(tokens, sid):
    relations = []
    for dependent in tokens:
        if dependent.head == '0' or dependent.rel in ('--', '_', '-') or dependent.xpos.startswith('$'):
            continue
        head = tokens[int(dependent.head) - 1]
        if head.xpos.startswith('$'):
            continue
        relation_type = dependent.rel
        if relation_type in relations_inv:
            pos_head = simplified_pos.get(head.xpos, head.xpos)
            pos_dep = simplified_pos.get(dependent.xpos, dependent.xpos)
            if (pos_head, pos_dep) in relations_inv[relation_type]:
                relations.append(Match(
                    head,
                    dependent,
                    None,
                    relations_inv[relation_type][(pos_head, pos_dep)],
                    sid,
                ))

        # if relation_type == "ATTR" and dependent.xpos != "ADJA":
        #     continue
        # if relation_type in ['PP-PN', 'KOM-CJ', 'SUBJ-PRED']:
        #     relations.append(Match(
        #         head,
        #         dependent,
        #         None,
        #         relation_type,
        #         sid,
        #     ))
        # else:
        #     relations.append(Match(
        #         head,
        #         dependent,
        #         None,
        #         relation_type,
        #         sid,
        #     ))
    return relations


def extract_all_binary_relations(tokens, sid):
    relations = []
    for dependent in tokens:
        if (dependent.head == '0'
                or dependent.rel in {'--', '_', '-'}
                or dependent.xpos.startswith('$')):
            continue
        head = tokens[int(dependent.head) - 1]
        if head.xpos.startswith('$'):
            continue
        relations.append(Match(
            head,
            dependent,
            None,
            dependent.rel,
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
            if (r.relation == "0"
                    or len(r.head.surface) < 2 or len(r.dep.surface) < 2
                    or any(c.isdigit() for c in r.head.lemma) or any(c.isdigit() for c in r.dep.lemma)
                    or r.head.xpos == "-" or r.dep.xpos == "-"):
                continue
            rel_dict[(r.relation, r.head.lemma, r.dep.lemma, r.head.upos, r.dep.upos)].append(r)
        sid += 1
    return rel_dict


def extract_matches_from_doc(parses):
    matches = []
    sid = 1
    for sentence in parses:
        relations = extract_binary_relations(sentence, sid)
        for r in relations:
            # TODO filter inconsistent relations
            #  - 0 is marked by parser
            if (r.relation == "0"
                    or len(r.head.surface) < 2 or len(r.dep.surface) < 2
                    or any(c.isdigit() for c in r.head.lemma) or any(c.isdigit() for c in r.dep.lemma)
                    or any(c in ['"', "'"] for c in r.head.surface)
                    or any(c in ['"', "'"] for c in r.dep.surface)
                    or r.head.xpos == "-" or r.dep.xpos == "-"):
                continue
            matches.append(r)
        sid += 1
    return matches


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


def read_conll_file(path):
    sentences = []
    with open(path, 'r') as conll_fh:
        sentence = []
        sid = 1
        for line in conll_fh:
            if line.strip():
                tokens = line.strip().split('\t')
                tokens[3] = simplified_pos.get(tokens[3], tokens[3])
                # tokens[4] = simplified_pos.get(tokens[4], tokens[4])
                sentence.append(ConllToken(*tokens))
            else:
                if sentence:
                    sentences.append(sentence)
                    sentence = []
                    sid += 1
                else:
                    continue
    return sentences


def read_meta_tabs_format(tabs_file_path):
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
            break
    return meta, index


def read_text_tabs_format(index, tabs_file_path):
    sentences = []
    sentence = []
    tabs_file = open(tabs_file_path, "r")
    for line in tabs_file:
        line = line.strip()
        if line.startswith("%%$DDC:meta"):
            continue
        elif line.startswith("%%$DDC:index"):
            continue
        elif line.startswith("%%$DDC:BREAK.s"):
            if sentence:
                sentences.append(sentence)
                sentence = []
        elif line and not line.startswith("%"):
            items = line.split("\t")
            sentence.append(
                TabsToken(items[index["Token"]], items[index["Lemma"]], items[index["Pos"]],
                          int(items[index["WordSep"]])))
    return sentences


def read_tabs_format(tabs_file_path, meta_only=False):
    meta_data, index = read_meta_tabs_format(tabs_file_path)
    if meta_only:
        return meta_data, []
    else:
        sentences = read_text_tabs_format(index, tabs_file_path)
        return meta_data, sentences


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
        pos = simplified_pos.get(pars_token.pos, pars_token.pos)
        sentence_conll.append(ConllToken(pars_token.tokId, pars_token.orth, pars_token.lemma, pos,
                                         pos, pars_token.morph, pars_token.headId, pars_token.dep, '',
                                         tabs_token.word_sep))
    return sentence_conll
