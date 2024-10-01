import re
from collections import defaultdict
from typing import List

from wordprofile.datatypes import Coocc, LemmaInfo, WPConcordance
from wordprofile.utils import tag_b2f

RE_HIT_DELIMITER = re.compile(r"([^\x01\x02]+)([\x01\x02])")


def format_lemma_pos(db_results: List[LemmaInfo], relation_order):
    """
    Converts lemma-pos items with their information into output format
    """
    lemma_pos_mapping = defaultdict(list)
    for i in sorted(db_results, key=lambda x: x.freq, reverse=True):
        relation = "~" + i.rel if i.inv else i.rel
        lemma_pos_mapping[(i.lemma, i.tag)].append((relation, int(i.freq)))

    results = []
    for (lemma, pos), rel_freqs in lemma_pos_mapping.items():
        relations, frequencies = zip(*rel_freqs)
        pos_tag = tag_b2f.get(pos)
        if pos_tag not in relation_order:
            continue
        if len(relations) > 1:
            relations_ordered = ["META"] + [
                r for r in relation_order[pos_tag] if r in relations
            ]
        else:
            relations_ordered = list(relations)
        results.append(
            {
                "Lemma": lemma,
                "POS": pos_tag,
                "PosId": pos_tag,
                "Frequency": sum(frequencies),
                "Relations": relations_ordered,
            }
        )
    return results


def format_relations(cooccs: List[Coocc], wp_spec, is_mwe=False):
    """Converts co-occurrences into output format"""
    results = []
    for coocc in cooccs:
        relation = ("~" if coocc.inverse else "") + coocc.rel
        results.append(
            {
                "Relation": relation,
                "RelationDescription": wp_spec.mapRelDesc.get(
                    relation, wp_spec.strRelDesc
                ),
                "POS": tag_b2f.get(coocc.tag2, ""),
                "Form": coocc.form2,
                "Lemma": coocc.lemma2,
                "Score": {
                    "Frequency": coocc.freq,
                    "logDice": coocc.score,
                },
                "ConcordId": ("#mwe" if is_mwe else "") + str(coocc.id),
                "ConcordNoAccessible": coocc.num_concords,
                "HasMwe": coocc.has_mwe,
            }
        )
    return results


def format_concordances(concords: list[WPConcordance]):
    """Converts concordances into output format"""
    results = []
    for c in concords:
        sentence_main = format_sentence_and_highlight(
            c.sentence, c.get_highlight_positions()
        )
        results.append(
            {
                "Bibl": {
                    "Corpus": c.corpus,
                    "Orig": c.orig.replace("#page#", c.page),
                },
                "ConcordLine": sentence_main,
            }
        )
    return results


def format_comparison(diffs):
    """Converts co-occurrence comparisons into output format"""
    results = []
    for diff in diffs:
        # create result with common/default values
        coocc_diff = {
            "POS": tag_b2f[diff["pos"]],
            "ConcordId1": None,
            "ConcordId2": None,
            "ConcordNoAccessible1": 0,
            "ConcordNoAccessible2": 0,
            "Score": {
                "AScomp": diff.get("score"),
                "Frequency1": 0,
                "Assoziation1": 0.0,
                "Frequency2": 0,
                "Assoziation2": 0.0,
            },
        }
        # complete information for first coocc
        if "coocc_1" in diff:
            coocc_1 = diff["coocc_1"]
            coocc_diff["Score"]["Frequency1"] = coocc_1.freq
            coocc_diff["Score"]["Assoziation1"] = coocc_1.score
            coocc_diff["ConcordId1"] = coocc_1.id
            concord_no = coocc_1.num_concords
            if coocc_1.rel == "KON" and coocc_1.lemma1 == coocc_1.lemma2:
                concord_no = concord_no / 2
            coocc_diff["ConcordNoAccessible1"] = concord_no
            relation = coocc_1.rel
            coocc_diff["Relation"] = ("~" if coocc_1.inverse else "") + relation
            coocc_diff["Lemma"] = coocc_1.lemma2
            coocc_diff["Form"] = coocc_1.form2
            if "coocc_2" in diff:
                coocc_diff["Position"] = "center"
            else:
                coocc_diff["Position"] = "left"
        # complete information for second coocc
        if "coocc_2" in diff:
            coocc_2 = diff["coocc_2"]
            coocc_diff["Score"]["Frequency2"] = coocc_2.freq
            coocc_diff["Score"]["Assoziation2"] = coocc_2.score
            coocc_diff["ConcordId2"] = coocc_2.id
            concord_no = coocc_2.num_concords
            if coocc_2.rel == "KON" and coocc_2.lemma1 == coocc_2.lemma2:
                concord_no = concord_no / 2
            coocc_diff["ConcordNoAccessible2"] = concord_no
            if "coocc_1" not in diff:
                relation = coocc_2.rel
                coocc_diff["Relation"] = ("~" if coocc_2.inverse else "") + relation
                coocc_diff["Lemma"] = coocc_2.lemma2
                coocc_diff["Form"] = coocc_2.form2
                coocc_diff["Position"] = "right"
        results.append(coocc_diff)
    return results


def format_sentence(sent: str) -> str:
    """Format of single concordance sentence.

    All special characters are removed from the concordance taken from the database.
    """
    if not sent:
        return ""
    return sent.replace("\x02", " ").replace("\x01", "").strip()


def format_sentence_and_highlight(sent: str, positions: List[int]) -> str:
    """Format concordance sentence and highlight certain positions."""
    if not sent:
        return ""
    sent += "\x01"
    tokens = RE_HIT_DELIMITER.findall(sent)
    for idx, (token, delim) in enumerate(tokens):
        padding = " " if delim == "\x02" else ""
        if (idx + 1) in positions:
            tokens[idx] = "_&{}&_{}".format(token, padding)
        else:
            tokens[idx] = "{}{}".format(token, padding)
    return "".join(tokens)


def format_relation_description(colloc: Coocc, description: str) -> dict[str, str]:
    if colloc.rel == "PP":
        if colloc.inverse:
            lemma2 = f"{colloc.lemma2} {colloc.prep}"
        else:
            lemma2 = f"{colloc.prep} {colloc.lemma2}"
    else:
        lemma2 = colloc.lemma2
    description = description.replace("$1", colloc.lemma1).replace("$2", lemma2)
    return {
        "Description": description,
        "Lemma1": colloc.lemma1,
        "Lemma2": lemma2,
    }
