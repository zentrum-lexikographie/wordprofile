from collections import defaultdict
from typing import List, Iterator

from wordprofile.datatypes import DBToken, Match, DependencyTree

RELATION_PATTERNS = {
    'ADV': {
        'desc': "hat Adverbialbestimmung",
        'inverse': "ist Adverbialbestimmung von",
        'rules': [
            # ("ADV", "VERB", "ADJ"),
            # ("ADV", "VERB", "ADV"),
            # ("ADV", "ADJ", "ADJ"),
            # ("ADV", "ADJ", "ADV"),
            ('advmod', 'verb', 'adj'),
            ('advmod', 'verb', 'adv'),
            ('advmod', 'adj', 'adj'),
            ('advmod', 'adj', 'adv'),
        ],
    },
    'ATTR': {
        'desc': "hat Adjektivattribut",
        'inverse': "ist Adjektivattribut von",
        'rules': [
            # ("ATTR", "NOUN", "ADJ"),
            ('amod', 'noun', 'adj'),
            ('amod', 'propn', 'adj'),
        ],
    },
    'GMOD': {
        'desc': "hat Genitivattribut",
        'inverse': "ist Genitivattribut von",
        'rules': [
            # ("GMOD", "NOUN", "NOUN"),
            ('nmod', 'noun', 'noun'),
            ('nmod', 'noun', 'propn'),
        ],
    },
    'KOM': {
        'desc': "hat vergleichende Wortgruppe",
        'inverse': "ist in vergleichender Wortgruppe",
        'rules': [
            # ("KOM", "CJ", "NOUN", "NOUN", "CCONJ"),
            # ("KOM", "CJ", "VERB", "NOUN", "CCONJ"),
        ],
    },
    'KON': {
        'desc': "hat Koordination mit",
        'inverse': "",
        'rules': [
            # ("CJ", "NOUN", "NOUN"),
            # ("CJ", "ADJ", "ADJ"),
            # ("CJ", "VERB", "VERB"),
            # ("KON", "CJ", "NOUN", "NOUN", "CCONJ"),
            # ("KON", "CJ", "ADJ", "ADJ", "CCONJ"),
            # ("KON", "CJ", "VERB", "VERB", "CCONJ"),
            ('conj', 'cc', 'noun', 'noun', 'cconj'),
            ('conj', 'cc', 'verb', 'verb', 'cconj'),
            ('conj', 'cc', 'adj', 'adj', 'cconj'),
        ],
    },
    'OBJ': {
        'desc': "hat Akkusativ/Dativ-Objekt",
        'inverse': "ist Akkusativ/Dativ-Objekt von",
        'rules': [
            # ("OBJA", "VERB", "NOUN"),
            # ("OBJA2", "VERB", "NOUN"),
            # ("OBJD", "VERB", "NOUN"),
            ('obj', 'verb', 'noun'),
            ('obj', 'verb', 'propn'),
            ('iobj', 'verb', 'noun'),
            ('iobj', 'verb', 'propn'),
        ],
    },
    # 'PN': {
    #     'desc': "",
    #     'inverse': "",
    #     'rules': [
    #         ("PP", "NOUN", "ADP"),
    #         ("PP", "AUX", "ADP"),
    #         ("PP", "VERB", "ADP"),
    #     ]
    # },
    'PP': {
        'desc': "hat Präpositionalgruppe",
        'inverse': "ist in Präpositionalgruppe",
        'rules': [
            # ("PP", "PN", "NOUN", "NOUN", "ADP"),
            # ("PP", "PN", "VERB", "NOUN", "ADP"),
            # ("PP", "PN", "VERB", "ADJ", "ADP"),
            ('nmod', 'case', 'noun', 'noun', 'adp'),
            ('obl', 'case', 'verb', 'noun', 'adp'),
            ('obl', 'case', 'verb', 'adj', 'adp'),
        ],
    },
    'PRED': {
        'desc': "hat Prädikativ",
        'inverse': "ist Prädikativ von",
        'rules': [
            ('nsubj', 'verb', 'noun'),
            ('nsubj', 'verb', 'propn'),
            ('nsubj', 'adj', 'noun'),
            ('nsubj', 'noun', 'noun'),
            # nur wenn cop (aux?) an head hängt
        ],
    },
    'SUBJA': {
        'desc': "hat Subjekt",
        'inverse': "ist Subjekt von",
        'rules': [
            # ("SUBJ", "NOUN", "NOUN"),
            # ("SUBJ", "NOUN", "ADJ"),
            # ("SUBJ", "VERB", "NOUN"),
            # ("SUBJ", "VERB", "ADJ"),
            ('nsubj', 'verb', 'noun'),
            ('nsubj', 'verb', 'propn'),
            ('nsubj', 'adj', 'noun'),
            ('nsubj', 'noun', 'noun'),
            # wenn weder aux noch cop an head hängen
        ],
    },
    'SUBJP': {
        'desc': "hat Passivsubjekt",
        'inverse': "ist Passivsubjekt von",
        'rules': [
            ('nsubj:pass', 'verb', 'noun'),
            ('nsubj:pass', 'verb', 'propn'),
        ],
    },
    'VZ': {
        'desc': "hat Verbzusatz",
        'inverse': "",
        'rules': [
            # ("AVZ", "VERB", "VERB"),
            # ("AVZ", "AUX", "VERB"),
            ('compound:prt', 'verb', 'adp'),  # liegt ... zugrunde
            ('compound:prt', 'aux', 'adp'),  # hat ... vor
            ('compound:prt', 'leid', 'adp'),  # leid tun
        ],
    },
}


def get_relation_types():
    return sorted(list(RELATION_PATTERNS.keys()))


def get_inverted_relation_patterns():
    relations_inv = defaultdict(lambda: defaultdict(str))
    for relation_dest, relation_patters in RELATION_PATTERNS.items():
        for p in relation_patters['rules']:
            if len(p) == 3:
                relation_src, head_pos, dep_pos = p
                relations_inv[relation_src][(head_pos.upper(), dep_pos.upper())] = relation_dest
            elif len(p) == 5:
                r1, r2, t1, t2, t3 = p
                relations_inv[(r2, r1)][(t2.upper(), t3.upper(), t1.upper())] = relation_dest
            else:
                raise ValueError('Pattern has unknown dimension')
    return {k: dict(vd) for k, vd in relations_inv.items()}


def extract_matches_by_pattern(relations_inv, tokens: List[DBToken], sid: int) -> Iterator[Match]:
    for t in tokens:
        if int(t.head) <= 0:
            # token is root
            continue
        t_head_1 = tokens[int(t.head) - 1]
        relation_type = t.rel
        if relation_type in relations_inv:
            if (t_head_1.tag, t.tag) in relations_inv[relation_type]:
                yield Match(
                    t_head_1,
                    t,
                    None,
                    relations_inv[relation_type][(t_head_1.tag, t.tag)],
                    sid,
                )
        if int(t_head_1.head) <= 0:
            # token head is root, cannot make ternary relation
            continue
        t_head_2 = tokens[int(t_head_1.head) - 1]
        rel_types = (t.rel, t_head_1.rel)
        if rel_types in relations_inv:
            if (t.tag, t_head_1.tag, t_head_2.tag) in relations_inv[rel_types]:
                yield Match(
                    t_head_2,
                    t,
                    t_head_1,
                    relations_inv[rel_types][(t.tag, t_head_1.tag, t_head_2.tag)],
                    sid,
                )


def extract_predicates(dtree: DependencyTree, sid: int) -> Iterator[Match]:
    for n in dtree.nodes:
        if n.is_root():
            continue
        if n.token.tag == "AUX":
            for c1 in n.children:
                if c1.token.rel == "SUBJ" and c1.token.tag in {'NOUN', 'VERB', 'ADJ'}:
                    for c2 in n.children:
                        if c2.token.rel == "PRED" and c2.token.tag in {'NOUN', 'VERB', 'ADJ'}:
                            yield Match(
                                c1.token,
                                c2.token,
                                None,
                                "PRED",
                                sid,
                            )


def extract_matches(parses) -> Iterator[Match]:
    relations_inv = get_inverted_relation_patterns()
    for sid, sentence in enumerate(parses):
        for match in extract_matches_by_pattern(relations_inv, sentence, sid + 1):
            yield match
        dtree = DependencyTree(sentence)
        for match in extract_predicates(dtree, sid + 1):
            yield match
