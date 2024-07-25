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
        lemma_pos_mapping[(i.lemma, i.form, i.tag)].append((relation, int(i.freq)))

    results = []
    for (lemma, form, pos), rel_freqs in lemma_pos_mapping.items():
        relations, frequencies = zip(*rel_freqs)
        pos_tag = tag_b2f.get(pos)
        if pos_tag not in relation_order:
            continue
        if len(relations) > 1:
            relations_ordered = ["META"] + [
                r for r in relation_order[pos_tag] if r in relations
            ]
        results.append(
            {
                "Form": form,
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
                "PosId": tag_b2f.get(coocc.tag2, ""),
                "Form": coocc.form2,
                "Lemma": coocc.lemma2,
                "Score": {
                    "Frequency": coocc.freq,
                    "logDice": coocc.score,
                },
                "ConcordId": ("#mwe" if is_mwe else "") + str(coocc.id),
                "ConcordNo": coocc.num_concords,
                "ConcordNoAccessible": coocc.num_concords,
                "HasMwe": coocc.has_mwe,
            }
        )
    return results


def format_concordances(concords: list[WPConcordance]):
    """Converts concordances into output format"""
    results = []
    for c in concords:
        sentence_left = format_sentence(c.sentence_left)
        sentence_right = format_sentence(c.sentence_right)
        sentence_main = format_sentence_and_highlight(
            c.sentence, c.get_highlight_positions()
        )
        results.append(
            {
                "Bibl": {
                    "Corpus": c.corpus,
                    "Date": c.date.strftime("%d-%m-%Y"),
                    "TextClass": c.textclass,
                    "Orig": c.orig.replace("#page#", c.page),
                    "Scan": c.scan.replace("#page#", c.page),
                    "Avail": c.avail,
                    "Page": c.page,
                    "File": c.file,
                },
                "ConcordLine": sentence_main,
                "ConcordLeft": sentence_left,
                "ConcordRight": sentence_right,
                "Score": c.score,
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
            "ConcordId1": 0,
            "ConcordId2": 0,
            "ConcordNo1": 0,
            "ConcordNo2": 0,
            "ConcordNoAccessible1": 0,
            "ConcordNoAccessible2": 0,
            "Score": {
                "AScomp": diff.get("score"),
                "Rank1": diff.get("rank_1", -1),
                "Rank2": diff.get("rank_2", -1),
                "Frequency1": 0,
                "Assoziation1": 0.0,
                "Frequency2": 0,
                "Assoziation2": 0.0,
            },
        }
        # complete information for first coocc
        if "coocc_1" in diff:
            coocc_diff["Score"]["Frequency1"] = diff["coocc_1"].freq
            coocc_diff["Score"]["Assoziation1"] = diff["coocc_1"].score
            coocc_diff["ConcordId1"] = diff["coocc_1"].id
            concord_no = diff["coocc_1"].freq
            if (
                diff["coocc_1"].rel == "KON"
                and diff["coocc_1"].lemma1 == diff["coocc_1"].lemma2
            ):
                concord_no = concord_no / 2
            coocc_diff["ConcordNo1"] = concord_no
            coocc_diff["Relation"] = diff["coocc_1"].rel
            coocc_diff["Lemma"] = diff["coocc_1"].lemma2
            coocc_diff["Form"] = diff["coocc_1"].form2
            if "coocc_2" in diff:
                coocc_diff["Position"] = "center"
            else:
                coocc_diff["Position"] = "left"
        # complete information for second coocc
        if "coocc_2" in diff:
            coocc_diff["Score"]["Frequency2"] = diff["coocc_2"].freq
            coocc_diff["Score"]["Assoziation2"] = diff["coocc_2"].score
            coocc_diff["ConcordId2"] = diff["coocc_2"].id
            concord_no = diff["coocc_2"].freq
            if (
                diff["coocc_2"].rel == "KON"
                and diff["coocc_2"].lemma1 == diff["coocc_2"].lemma2
            ):
                concord_no = concord_no / 2
            coocc_diff["ConcordNo2"] = concord_no
            if "coocc_1" not in diff:
                coocc_diff["Relation"] = diff["coocc_2"].rel
                coocc_diff["Lemma"] = diff["coocc_2"].lemma2
                coocc_diff["Form"] = diff["coocc_2"].form2
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
