from collections import defaultdict
from typing import List, Iterator

from wordprofile.datatypes import DBToken, Match, DependencyTree

RELATION_PATTERNS = {
    'ADV': {
        'desc': "hat Adverbialbestimmung",
        'inverse': "ist Adverbialbestimmung von",
        'rules': [
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
            ('amod', 'noun', 'adj'),
            ('amod', 'propn', 'adj'),
        ],
    },
    'GMOD': {
        'desc': "hat Genitivattribut",
        'inverse': "ist Genitivattribut von",
        'rules': [
            ('nmod', 'noun', 'noun'),
            ('nmod', 'noun', 'propn'),
            ('nmod:poss', 'noun', 'noun'),
            ('nmod:poss', 'noun', 'propn'),
        ],
    },
    'KOM': {
        'desc': "hat vergleichende Wortgruppe",
        'inverse': "ist in vergleichender Wortgruppe",
        'rules': [
            # ('obl', 'case', 'verb', 'noun', 'cconj'),
            # ('obl', 'case', 'noun', 'noun', 'cconj'),
            # ('nmod', 'case', 'noun', 'noun', 'cconj'),
        ],
    },
    'KON': {
        'desc': "hat Koordination mit",
        'inverse': "",
        'rules': [
            ('conj', 'cc', 'noun', 'noun', 'cconj'),
            ('conj', 'cc', 'verb', 'verb', 'cconj'),
            ('conj', 'cc', 'adj', 'adj', 'cconj'),
        ],
    },
    'OBJ': {
        'desc': "hat Akkusativ/Dativ-Objekt",
        'inverse': "ist Akkusativ/Dativ-Objekt von",
        'rules': [
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
    #         # ("PP", "NOUN", "ADP"),
    #         # ("PP", "AUX", "ADP"),
    #         # ("PP", "VERB", "ADP"),
    #     ]
    # },
    'PP': {
        'desc': "hat Präpositionalgruppe",
        'inverse': "ist in Präpositionalgruppe",
        'rules': [
            ('nmod', 'case', 'noun', 'noun', 'adp'),
            ('obl', 'case', 'verb', 'noun', 'adp'),
            ('obl', 'case', 'verb', 'adj', 'adp'),
        ],
    },
    'PRED': {
        'desc': "hat Prädikativ",
        'inverse': "ist Prädikativ von",
        'rules': [
            # ('nsubj', 'verb', 'noun'),
            # ('nsubj', 'verb', 'propn'),
            # ('nsubj', 'adj', 'noun'),
            # ('nsubj', 'noun', 'noun'),
            # nur wenn cop (aux?) an head hängt
        ],
    },
    'SUBJA': {
        'desc': "hat Subjekt",
        'inverse': "ist Subjekt von",
        'rules': [
            # ('nsubj', 'verb', 'noun'),
            # ('nsubj', 'verb', 'propn'),
            # ('nsubj', 'adj', 'noun'),
            # ('nsubj', 'noun', 'noun'),
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
            ('compound:prt', 'verb', 'adp'),  # liegt ... zugrunde
            ('compound:prt', 'aux', 'adp'),  # hat ... vor
            ('compound:prt', 'adj', 'adp'),  # leid tun
        ],
    },
}


def get_relation_types() -> List[str]:
    """Extract wordprofile relation types from relation patterns.

    Returns:
        Alphabetically sorted list of relation types for wordprofile.
    """
    return sorted(list(RELATION_PATTERNS.keys()))


def get_inverted_relation_patterns() -> dict:
    """Generates inverted search structure for relation pattern matching.

    Returns:
        2 level dictionary which maps from dependency relations over pos tags to the wordprofile relation.
    """
    relations_inv = defaultdict(lambda: defaultdict(str))
    for relation_dest, relation_patters in RELATION_PATTERNS.items():
        for p in relation_patters['rules']:
            if len(p) == 3:
                relation_src, head_pos, dep_pos = p
                relations_inv[relation_src][(head_pos.upper(), dep_pos.upper())] = relation_dest
            elif len(p) == 5:
                r1, r2, t1, t2, t3 = p
                relations_inv[(r1, r2)][(t1.upper(), t2.upper(), t3.upper())] = relation_dest
            else:
                raise ValueError('Pattern has unknown dimension')
    return {k: dict(vd) for k, vd in relations_inv.items()}


def extract_matches_by_pattern(relations_inv: dict, tokens: List[DBToken], sid: int) -> Iterator[Match]:
    """Extracts matches from a sequence of tokens by using a generated relation dictionary.

    Args:
        relations_inv: relation pattern dictionary
        tokens: sequence of tokens representing a single sentence
        sid: sentence id used for match initialization

    Returns:
        Generator over extracted matches from sentence.
    """
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
        rel_types = (t_head_1.rel, t.rel)
        if rel_types in relations_inv:
            if (t_head_2.tag, t_head_1.tag, t.tag) in relations_inv[rel_types]:
                yield Match(
                    t_head_2,
                    t_head_1,
                    t,
                    relations_inv[rel_types][(t_head_2.tag, t_head_1.tag, t.tag)],
                    sid,
                )


def extract_comparing_groups(tokens: List[DBToken], sid: int) -> Iterator[Match]:
    """Extracts matches for comparison relation from a sequence of tokens.

    Args:
        tokens: sequence of tokens representing a single sentence
        sid: sentence id used for match initialization

    Returns:
        Generator over extracted matches from sentence.
    """
    for t in tokens:
        if int(t.head) <= 0 or t.rel != 'case' or t.tag != "CCONJ" or t.surface not in ['als', 'wie']:
            # token is root
            continue
        t_head_1 = tokens[int(t.head) - 1]
        if int(t_head_1.head) <= 0 or t_head_1.rel not in {'obl', 'nmod'} or t_head_1.tag != "NOUN":
            # token head is root, cannot make ternary relation
            continue
        t_head_2 = tokens[int(t_head_1.head) - 1]
        if t.surface == 'als' and t_head_2.tag != 'ADJ':
            # expect relations with 'als' to relate to an adjective
            # TODO: preferably check for comparative (https://universaldependencies.org/u/feat/Degree.html)
            continue
        if t_head_2.tag in {'ADJ', 'VERB', 'NOUN'}:
            yield Match(
                t_head_2,
                t_head_1,
                t,
                'KOM',
                sid,
            )


def extract_predicatives(dtree: DependencyTree, sid: int) -> Iterator[Match]:
    """Extracts matches for subject predicative relation from a dependency tree of a sentence.
    TODO: extend for object predicative relations (https://www.deutschplus.net/pages/Pradikativ)

    Args:
        dtree: dependency tree of a single sentence
        sid: sentence id used for match initialization

    Returns:
        Generator over extracted matches from sentence.
    """
    for n in dtree.nodes:
        if n.token.tag in {'NOUN', 'VERB', 'ADJ'}:
            if any(c.token.rel == "cop" and c.token.tag == "AUX" for c in n.children):
                if not any(c.token.rel == "case" for c in n.children):
                    for nsubj in n.children:
                        if nsubj.token.rel == "nsubj" and nsubj.token.tag == 'NOUN':
                            yield Match(
                                nsubj.token,
                                n.token,
                                None,
                                "PRED",
                                sid,
                            )


def extract_active_subjects(dtree: DependencyTree, sid: int) -> Iterator[Match]:
    """Extracts matches for active subject relation from a dependency tree of a sentence.

    Args:
        dtree: dependency tree of a single sentence
        sid: sentence id used for match initialization

    Returns:
        Generator over extracted matches from sentence.
    """
    for n in dtree.nodes:
        if n.is_root():
            continue
        if any(cop.token.rel == "cop" for cop in n.children):
            continue
        if n.token.tag in {'NOUN', 'VERB', 'ADJ'}:
            for nsubj in n.children:
                if nsubj.token.rel == "nsubj" and nsubj.token.tag in {'NOUN', 'PROPN'}:
                    yield Match(
                        n.token,
                        nsubj.token,
                        None,
                        "SUBJA",
                        sid,
                    )


def extract_matches(parses: List[List[DBToken]]) -> Iterator[Match]:
    """Extracts various matches from a given list of sentences.

    Args:
        parses: List of token sequences

    Returns:
        Generator over extracted matches from sentences.
    """
    relations_inv = get_inverted_relation_patterns()
    for sid, sentence in enumerate(parses):
        for match in extract_matches_by_pattern(relations_inv, sentence, sid + 1):
            yield match
        dtree = DependencyTree(sentence)
        for match in extract_predicates(dtree, sid + 1):
            yield match
        for match in extract_comparing_groups(sentence, sid + 1):
            yield match
        for match in extract_active_subjects(dtree, sid + 1):
            yield match
