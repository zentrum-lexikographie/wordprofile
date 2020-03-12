from collections import namedtuple, defaultdict
from typing import List

from imsnpars.tools.utils import ConLLToken as IMSConllToken, ConLLToken

TabsToken = namedtuple("Token", ["surface", "lemma", "pos", "word_sep"])
ConllToken = namedtuple('ConllToken',
                        ['surface', 'lemma', 'tag', 'morph', 'head', 'rel', 'misc'])
DBToken = namedtuple('DBToken', ['idx', 'surface', 'lemma', 'tag', 'head', 'rel', 'misc'])

Match = namedtuple('Match', ['head', 'dep', 'prep', 'relation', 'sid'])

simplified_pos = {
    'APPR': 'APP',
    'APPO': 'APP',
    'APPRART': 'APP',
    'ADJA': 'ADJ',
    'ADJD': 'ADV',
    'ADV': 'ADV',
    'PAV': 'ADV',
    # 'ADJC': 'ADJ',
    'NN': 'NN',
    'KOKOM': 'KOKOM',
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
    "VZ": [("VZ", "VV", "VV"),
           ("AVZ", "VV", "VV"),
           ],
}
# rel_map : (rel1, rel2, head_pos, dep_pos, prep_pos)
relations_prep = {
    "KOM": [("KOM", "CJ", "NN", "NN", "KOKOM"),
            # ("KOM", "CJ", "NN", "PP", "KOKOM"),
            # ("KOM", "CJ", "PP", "NN", "KOKOM"),
            # ("KOM", "CJ", "PP", "PP", "KOKOM"),
            ("KOM", "CJ", "VV", "NN", "KOKOM"),
            # ("KOM", "CJ", "VV", "PP", "KOKOM"),
            ],
    "PP": [("PP", "PN", "NN", "NN", "APP"),
           # ("PP", "PN", "NN", "PP", "APP"),
           # ("PP", "PN", "PP", "NN", "APP"),
           # ("PP", "PN", "PP", "PP", "APP"),
           ("PP", "PN", "VV", "NN", "APP"),
           # ("PP", "PN", "VV", "PP", "APP"),
           ],
}


def get_inverted_relation_patterns(relation_mappings):
    relations_inv = defaultdict(lambda: defaultdict(str))
    for relation_dest, relation_patters in relation_mappings.items():
        for p in relation_patters:
            if len(p) == 3:
                relation_src, head_pos, dep_pos = p
                relations_inv[relation_src][(head_pos, dep_pos)] = relation_dest
            elif len(p) == 5:
                r1, r2, t1, t2, t3 = p
                relations_inv[(r2, r1)][(t2, t3, t1)] = relation_dest
            else:
                raise ValueError('Pattern has unknown dimension')
    return {k: dict(vd) for k, vd in relations_inv.items()}


relations_inv = get_inverted_relation_patterns(relations)
relations_prep_inv = get_inverted_relation_patterns(relations_prep)


def extract_prepositional_matches(tokens, sid):
    relations = []
    for dep in tokens:
        prep = tokens[int(dep.head) - 1]
        if int(prep.head) <= 0:
            continue
        head = tokens[int(prep.head) - 1]
        rel_types = (dep.rel, prep.rel)
        if rel_types in relations_prep_inv:
            if (dep.tag, prep.tag, head.tag) in relations_prep_inv[rel_types]:
                relations.append(Match(
                    head,
                    dep,
                    prep,
                    relations_prep_inv[rel_types][(dep.tag, prep.tag, head.tag)],
                    sid,
                ))
    return relations


def extract_binary_matches(tokens, sid):
    matches = []
    for dep in tokens:
        if dep.head == '0' or dep.rel in ('--', '_', '-') or dep.tag.startswith('$'):
            continue
        head = tokens[int(dep.head) - 1]
        if head.tag.startswith('$'):
            continue
        relation_type = dep.rel
        if relation_type in relations_inv:
            if (head.tag, dep.tag) in relations_inv[relation_type]:
                matches.append(Match(
                    head,
                    dep,
                    None,
                    relations_inv[relation_type][(head.tag, dep.tag)],
                    sid,
                ))
    return matches


def extract_matches_from_doc(parses):
    matches = []
    sid = 1
    for sentence in parses:
        relations = extract_binary_matches(sentence, sid)
        relations.extend(extract_prepositional_matches(sentence, sid))
        for r in relations:
            # TODO filter inconsistent relations
            #  - 0 is marked by parser
            if (r.relation == "0"
                    or len(r.head.surface) < 2 or len(r.dep.surface) < 2
                    or any(c.isdigit() for c in r.head.lemma) or any(c.isdigit() for c in r.dep.lemma)
                    or any(c in ['"', "'"] for c in r.head.surface)
                    or any(c in ['"', "'"] for c in r.dep.surface)
                    or r.head.tag == "-" or r.dep.tag == "-"):
                continue
            matches.append(r)
        sid += 1
    return matches


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
            continue
        elif line.strip() and not line.startswith("%%$DDC"):
            # End of meta header
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
        sentence_conll.append(ConllToken(pars_token.orth, pars_token.lemma, pos,
                                         pars_token.morph, pars_token.headId, pars_token.dep,
                                         bool(tabs_token.word_sep)))
    return sentence_conll
