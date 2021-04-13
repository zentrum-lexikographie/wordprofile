from collections import defaultdict
from typing import List, Dict

from wordprofile.datatypes import DBToken, Match, DependencyTree

# rel_map : (rel, head_pos, dep_pos)
#           (rel1, rel2, head_pos, mid_pos, dep_pos)
RELATION_PATTERNS = {
    "KON": [
        ("CJ", "NOUN", "NOUN"),
        ("CJ", "ADJ", "ADJ"),
        ("CJ", "VERB", "VERB"),
        ("KON", "CJ", "NOUN", "NOUN", "CCONJ"),
        ("KON", "CJ", "ADJ", "ADJ", "CCONJ"),
        ("KON", "CJ", "VERB", "VERB", "CCONJ"),
    ],
    "GMOD": [
        ("GMOD", "NOUN", "NOUN"),
    ],
    "OBJ": [
        ("OBJA", "VERB", "NOUN"),
        ("OBJA2", "VERB", "NOUN"),
        ("OBJD", "VERB", "NOUN"),
    ],
    "SUBJA": [
        ("SUBJ", "NOUN", "NOUN"),
        ("SUBJ", "NOUN", "ADJ"),
        ("SUBJ", "VERB", "NOUN"),
        ("SUBJ", "VERB", "ADJ"),
    ],
    "ADV": [
        ("ADV", "VERB", "ADJ"),
        ("ADV", "VERB", "ADV"),
        ("ADV", "ADJ", "ADJ"),
        ("ADV", "ADJ", "ADV"),
    ],
    "ATTR": [
        ("ATTR", "NOUN", "ADJ"),
    ],
    "VZ": [
        ("AVZ", "VERB", "VERB"),
        ("AVZ", "AUX", "VERB"),
    ],
    "KOM": [
        ("KOM", "CJ", "NOUN", "NOUN", "CCONJ"),
        ("KOM", "CJ", "VERB", "NOUN", "CCONJ"),
    ],
    "PN": [
        ("PP", "NOUN", "ADP"),
        ("PP", "AUX", "ADP"),
        ("PP", "VERB", "ADP"),
    ],
    "PP": [
        ("PP", "PN", "NOUN", "NOUN", "ADP"),
        ("PP", "PN", "VERB", "NOUN", "ADP"),
        ("PP", "PN", "VERB", "ADJ", "ADP"),
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


def extract_pattern_matches(relations_inv, tokens: List[DBToken], sid: int) -> List[Match]:
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
                matches.append(Match(
                    t_head_2,
                    t,
                    t_head_1,
                    relations_inv[rel_types][(t.tag, t_head_1.tag, t_head_2.tag)],
                    sid,
                ))
    return matches


def extract_predicates(tokens: List[DBToken], sid: int) -> List[Match]:
    tree = DependencyTree(tokens)
    matches = []
    for n in tree.nodes:
        if n.is_root():
            continue
        if n.token.tag == "AUX":
            for c1 in n.children:
                if c1.token.rel == "SUBJ" and c1.token.tag in {'NOUN', 'VERB', 'ADJ'}:
                    for c2 in n.children:
                        if c2.token.rel == "PRED" and c2.token.tag in {'NOUN', 'VERB', 'ADJ'}:
                            matches.append(Match(
                                c1.token,
                                c2.token,
                                None,
                                "PRED",
                                sid,
                            ))
    return matches


def extract_matches_from_doc(parses: List[List[DBToken]]):
    matches = []
    relations_inv = get_inverted_relation_patterns(RELATION_PATTERNS)
    for sid, sentence in enumerate(parses):
        relations = extract_pattern_matches(relations_inv, sentence, sid + 1)
        relations.extend(extract_predicates(sentence, sid + 1))
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
        ('NOUN', 'spec/lemma_repair_substantiv.csv'),
        ('VERB', 'spec/lemma_repair_verb.csv'),
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
    return not sentence[0].surface.islower() or sentence[0].tag == 'PRON'


def sent_filter_tags(sentence: List[DBToken]) -> bool:
    return any(t.tag in ["NOUN", "VERB", "AUX"] for t in sentence)


def sent_filter_invalid_tags(sentence: List[DBToken]) -> bool:
    return sum(1 for t in sentence if not t.tag) < 10


def sentence_is_valid(s: List[DBToken]) -> bool:
    return sent_filter_length(s) and sent_filter_tags(s) and sent_filter_endings(s) and sent_filter_invalid_tags(s)
