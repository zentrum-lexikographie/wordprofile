from collections import defaultdict
from collections.abc import Iterator
from enum import Enum

from wordprofile.datatypes import DependencyTree, Match, WPToken

RELATION_PATTERNS: dict[str, dict[str, str | list[tuple[str, ...]]]] = {
    "ADV": {
        "desc": "hat Adverbialbestimmung",
        "inverse": "ist Adverbialbestimmung von",
        "rules": [
            ("advmod", "verb", "adv"),
            ("advmod", "adj", "adv"),
            ("advmod", "verb", "adj"),
            ("advmod", "adj", "adj"),
        ],
    },
    "ATTR": {
        "desc": "hat Adjektivattribut",
        "inverse": "ist Adjektivattribut von",
        "rules": [
            ("amod", "noun", "adj"),
        ],
    },
    "GMOD": {
        "desc": "hat Genitivattribut",
        "inverse": "ist Genitivattribut von",
        "rules": [],
    },
    "KOM": {
        "desc": "hat vergleichende Wortgruppe",
        "inverse": "ist in vergleichender Wortgruppe",
        "rules": [],
    },
    "KON": {
        "desc": "in Koordination mit",
        "inverse": "",
        "rules": [
            ("conj", "cc", "noun", "noun", "cconj"),
            ("conj", "cc", "verb", "verb", "cconj"),
            ("conj", "cc", "adj", "adj", "cconj"),
        ],
    },
    "OBJ": {
        "desc": "hat Akkusativ-Objekt",
        "inverse": "ist Akkusativ-Objekt von",
        "rules": [
            ("iobj", "verb", "noun"),
        ],
    },
    "OBJO": {
        "desc": "hat Dativ-/Genitiv-Objekt",
        "inverse": "ist Dativ-/Genitiv-Objekt von",
        "rules": [],
    },
    "PP": {
        "desc": "hat Präpositionalgruppe",
        "inverse": "ist in Präpositionalgruppe",
        "rules": [
            ("nmod", "case", "noun", "noun", "adp"),
            ("obl", "case", "verb", "noun", "adp"),
            ("obl", "case", "verb", "adj", "adp"),
            ("obl", "case", "verb", "adv", "adp"),
            ("obj", "case", "verb", "noun", "adp"),
        ],
    },
    "PRED": {
        "desc": "hat Prädikativ",
        "inverse": "ist Prädikativ von",
        "rules": [],
    },
    "SUBJA": {
        "desc": "hat Subjekt",
        "inverse": "ist Subjekt von",
        "rules": [],
    },
    "SUBJP": {
        "desc": "hat Passivsubjekt",
        "inverse": "ist Passivsubjekt von",
        "rules": [],
    },
}

relation_types = Enum(
    "RELATION_TYPE", sorted(list(RELATION_PATTERNS.keys()))  # type: ignore[misc]
)


def word_classes_of_rule(rule):
    if len(rule) == 3:
        return rule[1:]
    elif len(rule) == 5:
        return rule[2:]
    else:
        raise ValueError("Unexpected pattern length.")


word_classes = Enum(
    "TAG_TYPE",
    sorted(  # type: ignore[misc]
        set(
            c.upper()
            for pattern in RELATION_PATTERNS.values()
            for rule in pattern["rules"]
            for c in word_classes_of_rule(rule)
        )
    ),
)


def get_inverted_relation_patterns() -> (
    dict[str | tuple[str, ...], dict[tuple[str, ...], str]]
):
    """
    Generates inverted search structure for relation pattern matching.

    Returns:
        2 level dictionary which maps from dependency relations over
        pos tags to the wordprofile relation.
    """
    relations_inv: defaultdict[
        str | tuple[str, ...], defaultdict[tuple[str, ...], str]
    ] = defaultdict(lambda: defaultdict(str))
    for relation_dest, relation_patterns in RELATION_PATTERNS.items():
        for p in relation_patterns["rules"]:
            if len(p) == 3:
                relation_src, head_pos, dep_pos = p  # type: ignore
                relations_inv[relation_src][
                    (head_pos.upper(), dep_pos.upper())
                ] = relation_dest
            elif len(p) == 5:
                r1, r2, t1, t2, t3 = p  # type: ignore
                relations_inv[(r1, r2)][
                    (t1.upper(), t2.upper(), t3.upper())
                ] = relation_dest
            else:
                raise ValueError("Pattern has unknown dimension")
    return {k: dict(vd) for k, vd in relations_inv.items()}


def extract_matches_by_pattern(
    relations_inv: dict[str | tuple[str, ...], dict[tuple[str, ...], str]],
    tokens: list[WPToken],
    sid: int,
) -> Iterator[Match]:
    """Extracts matches from a sequence of tokens by using a generated
    relation dictionary.

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
                rel = relations_inv[rel_types][(t_head_2.tag, t_head_1.tag, t.tag)]
                prep = None if rel == "KON" else t
                yield Match(
                    t_head_2,
                    t_head_1,
                    prep,
                    rel,
                    sid,
                )


def extract_comparing_groups(tokens: list[WPToken], sid: int) -> Iterator[Match]:
    """
    Extracts matches for comparison relation from a sequence of tokens.

    Args:
        tokens: sequence of tokens representing a single sentence
        sid: sentence id used for match initialization

    Returns:
        Generator over extracted matches from sentence.
    """
    for t in tokens:
        if (
            int(t.head) <= 0
            or t.rel != "case"
            or t.tag != "CCONJ"
            or t.surface not in ["als", "wie"]
        ):
            # token is root
            continue
        t_head_1 = tokens[int(t.head) - 1]
        if (
            int(t_head_1.head) <= 0
            or t_head_1.rel not in {"obl", "nmod"}
            or t_head_1.tag != "NOUN"
        ):
            # token head is root, cannot make ternary relation
            continue
        t_head_2 = tokens[int(t_head_1.head) - 1]
        if t.surface == "als":
            # and t_head_2.tag != 'ADJ':
            # expect relations with 'als' to relate to an adjective
            # TODO: preferably check for comparative (https://universaldependencies.org/u/feat/Degree.html)
            continue
        if t_head_2.tag in {"ADJ", "VERB", "NOUN"}:
            yield Match(
                t_head_2,
                t_head_1,
                None,
                "KOM",
                sid,
            )


def extract_predicatives(dtree: DependencyTree, sid: int) -> Iterator[Match]:
    """
    Extracts matches for subject predicative relation from a dependency
    tree of a sentence.

    TODO: extend for object predicative relations
    (https://www.deutschplus.net/pages/Pradikativ)

    Args:
        dtree: dependency tree of a single sentence
        sid: sentence id used for match initialization

    Returns:
        Generator over extracted matches from sentence.
    """
    for n in dtree.nodes:
        # subject predicative
        if n.token.tag in {"NOUN", "VERB", "ADJ"}:
            if any(c.token.rel == "cop" and c.token.tag == "AUX" for c in n.children):
                if not any(c.token.rel == "case" for c in n.children):
                    for nsubj in n.children:
                        if nsubj.token.rel == "nsubj" and nsubj.token.tag == "NOUN":
                            yield Match(
                                nsubj.token,
                                n.token,
                                None,
                                "PRED",
                                sid,
                            )
        # object predicative
        if n.token.tag == "VERB":
            for obj in n.children:
                if obj.token.tag in {"VERB", "ADJ", "NOUN"} and obj.token.rel in {
                    "obj",
                    "obl",
                }:  # ++ 'advcl', 'xcomp'
                    # if any(c.token.rel in {'mark', 'case'} and c.token.tag in {'CCONJ', 'ADP'} for c in obj.children):
                    if any(c.token.surface in {"als", "für"} for c in obj.children):
                        yield Match(
                            n.token,
                            obj.token,
                            None,
                            "PRED",
                            sid,
                        )


def extract_genitives(dtree: DependencyTree, sid: int) -> Iterator[Match]:
    """
    Extracts matches for genitive modification relation from a dependency
    tree of a sentence.

    Args:
        dtree: dependency tree of a single sentence
        sid: sentence id used for match initialization

    Returns:
        Generator over extracted matches from sentence.
    """
    for n in dtree.nodes:
        if n.token.tag == "NOUN":
            for nmod in n.children:
                if nmod.token.rel == "nmod" and nmod.token.tag == "NOUN":
                    if _has_case_marking(nmod.token, "Gen") or any(
                        _has_case_marking(dep.token, "Gen") for dep in nmod.children
                    ):
                        if any(c.token.rel == "case" for c in nmod.children):
                            continue
                        yield Match(
                            n.token,
                            nmod.token,
                            None,
                            "GMOD",
                            sid,
                        )


def _has_case_marking(token: WPToken, case: str) -> bool:
    if token.morph is None:
        return False
    return ("Case", case) in token.morph.items()


def extract_active_subjects(dtree: DependencyTree, sid: int) -> Iterator[Match]:
    """
    Extracts matches for active subject relation from a dependency
    tree of a sentence.

    Args:
        dtree: dependency tree of a single sentence
        sid: sentence id used for match initialization

    Returns:
        Generator over extracted matches from sentence.
    """
    for n in dtree.nodes:
        if any(cop.token.rel == "cop" for cop in n.children):
            continue
        if n.token.tag in {"NOUN", "VERB", "ADJ"}:
            for nsubj in n.children:
                if nsubj.token.rel == "nsubj" and nsubj.token.tag == "NOUN":
                    yield Match(
                        n.token,
                        nsubj.token,
                        None,
                        "SUBJA",
                        sid,
                    )


def extract_objects(dtree: DependencyTree, sid: int) -> Iterator[Match]:
    """
    Extract acc./dat./gen. object relation from a dependency tree.

    Args:
        dtree: DependencyTree of a single sentence
        sid: sentence id

    Returns:
        Generator of extracted matches from sentence
    """
    for node in dtree.nodes:
        if node.token.tag == "VERB":
            for child in node.children:
                if child.token.rel in {"obj", "obl:arg"} and child.token.tag == "NOUN":
                    if any(dep.token.rel == "case" for dep in child.children):
                        continue
                    if child.token.rel == "obj":
                        if not (
                            _has_case_marking(child.token, "Dat")
                            or _has_case_marking(child.token, "Gen")
                            or any(
                                (
                                    _has_case_marking(dep.token, "Gen")
                                    and dep.token.rel != "nmod"
                                )
                                or (
                                    _has_case_marking(dep.token, "Dat")
                                    and dep.token.rel != "nmod"
                                )
                                for dep in child.children
                            )
                        ) or _has_case_marking(child.token, "Acc"):
                            relation = "OBJ"
                        else:
                            relation = "OBJO"
                    elif child.token.rel == "obl:arg":
                        relation = "OBJO"
                    yield Match(node.token, child.token, None, relation, sid)


def extract_matches(parses: list[list[WPToken]]) -> Iterator[Match]:
    """Extracts various matches from a given list of sentences.

    Args:
        parses: List of token sequences

    Returns:
        Generator over extracted matches from sentences.
    """
    relations_inv = get_inverted_relation_patterns()
    for sid, sentence in enumerate(parses, 1):
        for match in extract_matches_by_pattern(relations_inv, sentence, sid):
            yield match
        dtree = DependencyTree(sentence)
        for match in extract_objects(dtree, sid):
            yield match
        for match in extract_predicatives(dtree, sid):
            yield match
        for match in extract_genitives(dtree, sid):
            yield match
        for match in extract_comparing_groups(sentence, sid):
            yield match
        for match in extract_active_subjects(dtree, sid):
            yield match
