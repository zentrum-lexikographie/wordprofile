from collections import defaultdict
from typing import List, Dict

from wordprofile.datatypes import DBToken, Match

SIMPLE_TAG_MAP = {
    'APP': 'APP',
    'ADJ': 'ADJ',
    'VV': 'VV',
    'VA': 'VV',
    'VM': 'VV',
    'NN': 'NN',
    'APPR': 'APP',
    'APPO': 'APP',
    'APPRART': 'APP',
    'ADJA': 'ADJ',
    'ADJD': 'ADV',
    'ADV': 'ADV',
    'PAV': 'ADV',
    # 'ADJC': 'ADJ',
    'KOKOM': 'KOKOM',
    'KON': 'KON',
    # 'PPER': 'PP',
    'PTKVZ': 'VV',
    'VVFIN': 'VV',
    'VVINF': 'VV',
    'VVIZU': 'VV',
    'VVPP': 'VV',
    'VVPP1': 'VV',
    'VVPP2': 'VV',
    'VVIMP': 'VV',
    'VAFIN': 'VV',
    'VAIMP': 'VV',
    'VAINF': 'VV',
    'VAPP': 'VV',
    'VMFIN': 'VV',
    'VMINF': 'VV',
    'VMPP': 'VV',
}

# rel_map : (rel, head_pos, dep_pos)
RELATIONS = {
    "KON": [
        ("CJ", "NN", "NN"),
        ("CJ", "ADJ", "ADJ"),
        ("CJ", "VV", "VV"),
        ("KON", "CJ", "NN", "NN", "KON"),
        ("KON", "CJ", "ADJ", "ADJ", "KON"),
        ("KON", "CJ", "VV", "VV", "KON"),
    ],
    "GMOD": [
        ("GMOD", "NN", "NN"),
    ],
    "OBJ": [
        ("OBJA", "VV", "NN"),
        ("OBJA2", "VV", "NN"),
        ("OBJD", "VV", "NN"),
    ],
    "PRED": [
        ("PRED", "NN", "NN"),
        ("PRED", "NN", "ADJ"),
        ("PRED", "VV", "ADJ"),
        ("PRED", "VV", "NN"),
        ("SUBJ", "NN", "NN"),
        ("SUBJ", "NN", "ADJ"),
        ("SUBJ", "VV", "NN"),
        ("SUBJ", "VV", "ADJ"),
    ],
    "ADV": [
        ("ADV", "VV", "ADJ"),
        ("ADV", "VV", "ADV"),
        ("ADV", "ADJ", "ADJ"),
        ("ADV", "ADJ", "ADV"),
    ],
    "ATTR": [
        ("ATTR", "NN", "ADJ"),
    ],
    "VZ": [
        ("AVZ", "VV", "VV"),
    ],
    "KOM": [
        ("KOM", "CJ", "NN", "NN", "KOKOM"),
        ("KOM", "CJ", "VV", "NN", "KOKOM"),
    ],
    "PP": [
        ("PP", "PN", "NN", "NN", "APP"),
        ("PP", "PN", "VV", "NN", "APP"),
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


def extract_matches(relations_inv, tokens: List[DBToken], sid: int) -> List[Match]:
    matches = []
    for t in tokens:
        if int(t.head) <= 0:
            # token is root
            continue
        t_head_1 = tokens[int(t.head) - 1]
        relation_type = t.rel
        if relation_type in relations_inv:
            if (t_head_1.tag, t.tag) in relations_inv[relation_type]:
                matches.append(Match(
                    t_head_1,
                    t,
                    None,
                    relations_inv[relation_type][(t_head_1.tag, t.tag)],
                    sid,
                ))
        if int(t_head_1.head) <= 0:
            # token head is root, cannot make ternary relation
            continue
        t_head_2 = tokens[int(t_head_1.head) - 1]
        rel_types = (t.rel, t_head_1.rel)
        if rel_types in relations_inv:
            if (t.tag, t_head_1.tag, t_head_2.tag) in relations_inv[rel_types]:
                if t_head_1.tag in ['APP', 'KOKOM']:
                    matches.append(Match(
                        t_head_2,
                        t,
                        t_head_1,
                        relations_inv[rel_types][(t.tag, t_head_1.tag, t_head_2.tag)],
                        sid,
                    ))
                else:
                    matches.append(Match(
                        t_head_2,
                        t,
                        None,
                        relations_inv[rel_types][(t.tag, t_head_1.tag, t_head_2.tag)],
                        sid,
                    ))

    return matches


def extract_matches_from_doc(parses: List[List[DBToken]]):
    matches = []
    relations_inv = get_inverted_relation_patterns(RELATIONS)
    for sid, sentence in enumerate(parses):
        relations = extract_matches(relations_inv, sentence, sid + 1)
        for r in relations:
            # TODO filter inconsistent relations
            #  - 0 is marked by parser
            if (len(r.head.surface) < 2 or len(r.dep.surface) < 2
                    or not r.head.surface[0].isalpha() or not r.dep.surface[0].isalpha()
                    or not r.head.surface[-1].isalpha() or not r.dep.surface[-1].isalpha()
                    or any(c.isdigit() for c in r.head.lemma) or any(c.isdigit() for c in r.dep.lemma)
                    or any(c in '"\'@§!?;#*/&<>()' for c in r.head.surface)
                    or any(c in '"\'@§!?;#*/&<>()' for c in r.dep.surface)):
                continue
            matches.append(r)
    return matches


def load_lemma_repair_files() -> Dict[str, Dict[str, str]]:
    """
    Load static repair mapping files into dict.

    These mappings are used to repair the poor lemmatizer output (already known problems).
    The files have tab-separated csv format. Each line contains a mapping of the form:
        <bad lemma>\t<correct lemma>
    """
    word_classes_repair = {}
    files = [
        ('ADJ', 'spec/lemma_repair_adjektiv.csv'),
        ('NN', 'spec/lemma_repair_substantiv.csv'),
        ('VV', 'spec/lemma_repair_verb.csv'),
    ]
    for word_class, path in files:
        word_class_repair = {}
        for line in open(path, 'r'):
            line = line.strip().split('\t')
            if len(line) == 2:
                if line[0] not in word_class_repair:
                    word_class_repair[line[0]] = line[1]
        word_classes_repair[word_class] = word_class_repair
    return word_classes_repair


LEMMA_REPAIR = load_lemma_repair_files()


def repair_lemma(lemma: str, lemma_tag: str) -> str:
    if lemma_tag in LEMMA_REPAIR:
        return LEMMA_REPAIR[lemma_tag].get(lemma, lemma)
    return lemma


def sent_filter_length(sentence: List[DBToken]) -> bool:
    return 3 <= len(sentence) <= 100


def sent_filter_endings(sentence: List[DBToken]) -> bool:
    return not sentence[-1].surface in [":", ","] or len(sentence) >= 5


def sent_filter_lower_start(sentence: List[DBToken]) -> bool:
    return not sentence[0].surface.islower() or sentence[0].tag == 'PPER'


def sent_filter_tags(sentence: List[DBToken]) -> bool:
    return any(t.tag in ["NN", "VV", "VM", "VA"] for t in sentence)


def sentence_is_valid(s: List[DBToken]) -> bool:
    return sent_filter_length(s) and sent_filter_tags(s) and sent_filter_endings(s)
