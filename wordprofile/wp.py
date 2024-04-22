import logging
import math
import re
from collections import defaultdict
from typing import List, Union

import wordprofile.config
from wordprofile.errors import InternalError
from wordprofile.formatter import (
    format_comparison,
    format_concordances,
    format_lemma_pos,
    format_relations,
)
from wordprofile.utils import tag_b2f, tag_f2b
from wordprofile.wpse.connector import WPConnect
from wordprofile.wpse.mwe_connector import WPMweConnect
from wordprofile.wpse.wpse_spec import WpSeSpec

logger = logging.getLogger("wordprofile")

RE_LEMMA = re.compile(r"[\w.\-]+")


class Wordprofile:
    def __init__(
        self,
        db_host=None,
        db_user=None,
        db_passwd=None,
        db_name=None,
        wp_spec_file=None,
    ):
        logger.info("start init ...")
        self.db_name = db_name or wordprofile.config.DB_NAME
        self.wp_spec = WpSeSpec(wp_spec_file)
        self.db = WPConnect(db_host, db_user, db_passwd, db_name)
        self.db_mwe = WPMweConnect(db_host, db_user, db_passwd, db_name)
        logger.info("init complete")

    def get_info_stats(self):
        return {
            "info": self.db_name,
            "tables": self.db.get_db_infos(),
            "tags": {
                "pos": self.db.get_tag_frequencies(),
                "label": self.db.get_label_frequencies(),
            },
            "corpora": self.db.get_corpus_file_stats(),
        }

    def get_lemma_and_pos(self, lemma: str, pos: str = "") -> List[dict]:
        """Fetches lemma information from word-profile database.

        Args:
            lemma: Lemma of interest.
            pos (optional): Pos tag of first lemma.

        Return:
            List of lemma-pos combinations with stats and possible relations.
        """
        if not RE_LEMMA.fullmatch(lemma):
            raise ValueError(f"Request for invalid lemma: ({lemma})")

        lemma = lemma.replace("+", " ")
        pos = tag_f2b[pos]
        results = self.db.get_lemma_and_pos(lemma, pos)
        return format_lemma_pos(results, self.wp_spec.mapRelOrder)

    def get_lemma_and_pos_diff(self, lemma1: str, lemma2: str) -> List[dict]:
        """Fetches lemma pairs with common pos tags from word-profile database.

        Args:
            lemma1: Lemma of interest.
            lemma2: Lemma for comparison.

        Returns:
            List of lemma1–lemma2 combinations with additional information such as frequency and relation.
        """
        list1 = self.get_lemma_and_pos(lemma1)
        list2 = self.get_lemma_and_pos(lemma2)
        # checks lemma pairs for common pos tags
        results = []
        for i in list1:
            for j in list2:
                if i["POS"] == j["POS"]:
                    relations = set(i["Relations"]) | set(j["Relations"])
                    relations = [
                        r for r in self.wp_spec.mapRelOrder[i["POS"]] if r in relations
                    ]
                    results.append(
                        {
                            "LemmaId1": i["Lemma"],
                            "LemmaId2": j["Lemma"],
                            "POS": i["POS"],
                            "PosId": i["POS"],
                            "Frequency1": i["Frequency"],
                            "Frequency2": j["Frequency"],
                            "Relations": relations,
                        }
                    )
        return results

    def get_relations(
        self,
        lemma1: str,
        pos1: str,
        lemma2: str = "",
        pos2: str = "",
        relations: List[str] = (),
        start: int = 0,
        number: int = 20,
        order_by: str = "log_dice",
        min_freq: int = 0,
        min_stat: float = -1000.0,
    ) -> List[dict]:
        """Fetches collocations from word-profile database.

        Args:
            lemma1: Lemma of interest, first collocate.
            pos1: Pos tag of first lemma.
            lemma2 (deprecated): Second collocate.
            pos2 (deprecated): Pos tag of second lemma.
            relations (optional): List of relation labels.
            start (optional): Number of collocations to skip.
            number (optional): Number of collocations to take.
            order_by (optional): Metric for ordering, frequency or log_dice.
            min_freq (optional): Filter collocations with minimal frequency.
            min_stat (optional): Filter collocations with minimal stats score.

        Return:
            List of selected collocations grouped by relation.
        """
        if lemma1 and not RE_LEMMA.fullmatch(lemma1):
            raise ValueError(f"Request for invalid lemma: ({lemma1})")

        results = []
        for relation in relations:
            # meta relation is a summary of all relations
            if relation == "META":
                cooccs = self.db.get_relation_meta(
                    lemma1,
                    tag_f2b[pos1],
                    start,
                    number,
                    order_by,
                    min_freq,
                    min_stat,
                    self.wp_spec.mapRelOrder[pos1],
                )
            else:
                cooccs = self.db.get_relation_tuples(
                    lemma1,
                    tag_f2b[pos1],
                    start,
                    number,
                    order_by,
                    min_freq,
                    min_stat,
                    relation,
                )
            results.append(
                {
                    "Relation": relation,
                    "Description": self.wp_spec.mapRelDesc.get(
                        relation, self.wp_spec.strRelDesc
                    ),
                    "Tuples": format_relations(cooccs, self.wp_spec),
                    "RelId": "{}#{}#{}".format(lemma1, pos1, relation),
                }
            )
        return results

    def get_collocation_ids(self, lemma1: str, lemma2: str) -> List[int]:
        """Fetches possible collocation ids for lemma pair.

        Args:
            lemma1: First lemma of collocation.
            lemma2: Second lemma of collocation.

        Return:
            Absolute collocation ids.
        """
        for lemma in [lemma1, lemma2]:
            if lemma and not RE_LEMMA.fullmatch(lemma):
                raise ValueError(f"Request for invalid lemma: ({lemma})")

        return [abs(c.id) for c in self.db_mwe.get_collocations(lemma1, lemma2)]

    def get_mwe_relations(
        self,
        coocc_ids: List[int],
        relations: List[str] = (),
        start: int = 0,
        number: int = 20,
        order_by: str = "log_dice",
        min_freq: int = 0,
        min_stat: float = -1000.0,
    ) -> dict:
        """Fetches MWE from word-profile database.

        Args:
            coocc_ids: List of collocation ids.
            start (optional): Number of collocations to skip.
            number (optional): Number of collocations to take.
            order_by (optional): Metric for ordering, frequency or log_dice.
            min_freq (optional): Filter collocations with minimal frequency.
            min_stat (optional): Filter collocations with minimal stats score.

        Return:
            List of selected collocations grouped by relation.
        """

        def filter_unique_cooccs(cs):
            res = []
            used = set()
            for c in cs:
                if c.lemma2 not in used:
                    used.add(c.lemma2)
                    res.append(c)
            return res

        if not coocc_ids:
            return {"parts": [], "data": {}}
        # TODO BUG checks only first coocc id!
        coocc_ids = [abs(int(i)) for i in coocc_ids]
        coocc_info = self.db.get_relation_by_id(coocc_ids[0], min_freq)
        grouped_relations = defaultdict(list)
        lemma1 = pos1 = ""
        for coocc in self.db_mwe.get_relation_tuples(
            coocc_ids, order_by, min_freq, min_stat
        ):
            if relations and coocc.rel not in relations:
                continue
            lemma1 = coocc.lemma1
            pos1 = coocc.tag1
            grouped_relations[coocc.rel].append(coocc)
        results = defaultdict(list)
        for relation, cooccs in grouped_relations.items():
            # TODO check origin of MWE duplicates
            cooccs = filter_unique_cooccs(cooccs)
            results[lemma1].append(
                {
                    "Relation": relation,
                    "Description": self.wp_spec.mapRelDesc.get(
                        relation, self.wp_spec.strRelDesc
                    ),
                    "Tuples": format_relations(
                        cooccs[:number], self.wp_spec, is_mwe=True
                    ),
                    "RelId": "{}#{}#{}".format(lemma1, pos1, relation),
                }
            )
        return {
            "parts": [
                {"Lemma": coocc_info.lemma1, "POS": tag_b2f[coocc_info.tag1]},
                {"Lemma": coocc_info.lemma2, "POS": tag_b2f[coocc_info.tag2]},
            ],
            "data": dict(results),
        }

    def get_diff(
        self,
        lemma1: str,
        lemma2: str,
        pos: str,
        relations: List[str],
        number: int = 20,
        order_by: str = "log_dice",
        min_freq: int = 0,
        min_stat: float = -1000.0,
        operation: str = "adiff",
        use_intersection: bool = False,
        nbest: int = 0,
    ) -> List[dict]:
        """Fetches collocations of common POS from word-profile database and computes distances for comparison.

        Args:
            lemma1: Lemma of interest, first collocate.
            lemma2: Second collocate.
            pos: Pos tag for both lemmas.
            relations (optional): List of relation labels.
            number (optional): Number of collocations to take.
            order_by (optional): Metric for ordering, frequency or log_dice.
            min_freq (optional): Filter collocations with minimal frequency.
            min_stat (optional): Filter collocations with minimal stats score.
            operation (optional): Lemma distance metric.
            use_intersection (optional): If set, only the intersection of both lemma is computed.
            nbest (optional): Checks only the n highest scored lemmas.
        Return:
            List of collocation-diffs grouped by relation.
        """
        for lemma in [lemma1, lemma2]:
            if lemma and not RE_LEMMA.fullmatch(lemma):
                raise ValueError(f"Request for invalid lemma: ({lemma})")

        results = []
        for rel in relations:
            if rel == "META":
                diffs = self.db.get_relation_tuples_diff_meta(
                    lemma1,
                    lemma2,
                    tag_f2b[pos],
                    order_by,
                    min_freq,
                    min_stat,
                    self.wp_spec.mapRelOrder[pos],
                )
            else:
                diffs = self.db.get_relation_tuples_diff(
                    lemma1, lemma2, tag_f2b[pos], rel, order_by, min_freq, min_stat
                )
            diffs = self.__calculate_diff(
                lemma1, lemma2, diffs, number, nbest, use_intersection, operation
            )
            results.append(
                {
                    "Relation": rel,
                    "Description": self.wp_spec.mapRelDesc.get(
                        rel, self.wp_spec.strRelDesc
                    ),
                    "Tuples": format_comparison(diffs),
                }
            )
        return results

    def __calculate_diff(
        self,
        lemma1: str,
        lemma2: str,
        diffs,
        number: int,
        nbest: int,
        use_intersection: bool,
        operation: str,
    ) -> List[dict]:
        """Compares two given word-profiles relation-wise.

        Comparison is based on a operation and is used to highlight either differences or similarities.
        Difference:
            1. calculate absolute difference (adiff) for all pairs: |s₁(K)-s₂(K)| for all K ∊ WP₁ ∪ WP₂
            2. sort and choose nbest
            3. calculate true difference (diff) for all pairs: s₁(K)-s₂(K) for all K ∊ WP₁ ∪ WP₂
            4. sort again
        Intersect:
            1. compute max rank (rmax) for all pairs: max(r₁(K),r₂(K)) for all K ∊ WP₁ ∩ WP₂
            2. sort and choose nbest

        Args:
            lemma1: Lemma of interest, first collocate.
            lemma2: Second collocate.
            diffs: Lemma of interest, first collocate.
            nbest: Checks only the n highest scored lemmas.
            use_intersection: If set, only the intersection of both lemma is computed.
            operation: Lemma distance metric.
        Return:
            List of collocation-diffs grouped by relation.
        """
        diffs_grouped = defaultdict(dict)
        lemma1_ctr = lemma2_ctr = 0
        for i, c in enumerate(diffs):
            if nbest and lemma1_ctr > nbest and lemma2_ctr > nbest:
                break
            if c.lemma1 == lemma1:
                if not nbest or lemma1_ctr <= nbest:
                    diffs_grouped[c.lemma2]["coocc_1"] = c
                    diffs_grouped[c.lemma2]["rank_1"] = i
                    diffs_grouped[c.lemma2]["pos"] = c.tag1
                lemma1_ctr += 1
            elif c.lemma1 == lemma2:
                if not nbest or lemma2_ctr <= nbest:
                    diffs_grouped[c.lemma2]["coocc_2"] = c
                    diffs_grouped[c.lemma2]["rank_2"] = i
                    diffs_grouped[c.lemma2]["pos"] = c.tag1
                lemma2_ctr += 1
            elif c.lemma1.lower() in {lemma1.lower(), lemma2.lower()}:
                continue
            else:
                raise InternalError(
                    f"Unexpected lemma {c} for Lemma1 ({lemma1}) and Lemma2 ({lemma2})"
                )
        # for intersection, only a subset is used further
        if use_intersection:
            diffs_grouped = [
                d for d in diffs_grouped.values() if "coocc_1" in d and "coocc_2" in d
            ]
        else:
            diffs_grouped = list(diffs_grouped.values())
        # compute score based on occurring cooccs
        for d in diffs_grouped:
            if "coocc_1" in d and "coocc_2" in d:
                d["score"] = self.__diff_operation(
                    operation,
                    d["coocc_1"].score,
                    d["coocc_2"].score,
                    d["rank_1"],
                    d["rank_2"],
                )
            elif "coocc_1" in d:
                d["score"] = self.__diff_operation(
                    operation, d["coocc_1"].score, 0, d["rank_1"], 0
                )
            elif "coocc_2" in d:
                d["score"] = self.__diff_operation(
                    operation, 0, d["coocc_2"].score, 0, d["rank_2"]
                )
        # final sort and cut after nbest cooccs
        if operation in ["adiff", "ardiff"]:
            diffs_grouped.sort(key=lambda x: math.fabs(x["score"]), reverse=True)
            diffs_grouped = diffs_grouped[:number]
            diffs_grouped.sort(key=lambda x: x["score"], reverse=True)
        elif operation == "rmax":
            diffs_grouped.sort(key=lambda x: x["score"])
            diffs_grouped = diffs_grouped[:number]
        else:
            diffs_grouped.sort(key=lambda x: x["score"], reverse=True)
            diffs_grouped = diffs_grouped[:number]
        return diffs_grouped

    def __diff_operation(
        self, operation: str, s1: float, s2: float, r1: int, r2: int
    ) -> Union[int, float]:
        """Calculates the score difference.

        Args:
            operation: Metric operation.
            s1: Score of first lemma.
            s2: Score of second lemma.
            r1: Rank of first lemma.
            r2: Rank of second lemma.

        Returns:
            Distance of either scores or ranks, depending on the operation.
        """
        if operation == "diff":
            score = s1 - s2
        elif operation == "adiff":
            score = s1 - s2
        elif operation == "max":
            score = max(s1, s2)
        elif operation == "rmax":
            score = max(r1, r2)
        elif operation == "avg":
            score = (s1 + s2) / 2
        else:
            raise ValueError("Unknown operation")
        return score

    def get_relation_by_info_id(self, coocc_id: int, is_mwe: bool = False) -> dict:
        """Fetches cooccurrence information for a specific hit id.

        Args:
            coocc_id: DB index of the collocation.
            is_mwe: If true, then coocc_id refers to MWE, otherwise collocation.
        Return:
            Dictionary with collocation information.
        """
        if is_mwe:
            coocc_info = self.db_mwe.get_relation_by_id(int(coocc_id))
        else:
            coocc_info = self.db.get_relation_by_id(int(coocc_id))
        relation_identifier = coocc_info.rel
        if coocc_info.inverse:
            relation_identifier = f"~{relation_identifier}"
        if relation_identifier in self.wp_spec.mapRelDescDetail:
            description = self.wp_spec.mapRelDescDetail[relation_identifier]
        else:
            description = self.wp_spec.strRelDescDetail
        description = description.replace("$1", coocc_info.lemma1)
        description = description.replace("$2", coocc_info.lemma2)
        return {
            "Description": description,
            "Relation": coocc_info.rel,
            "Lemma1": coocc_info.lemma1,
            "Lemma2": coocc_info.lemma2,
            "Form1": coocc_info.form1,
            "Form2": coocc_info.form2,
            "POS1": coocc_info.tag1,
            "POS2": coocc_info.tag2,
        }

    def get_concordances_and_relation(
        self,
        coocc_id: int,
        use_context: bool = False,
        start_index: int = 0,
        result_number: int = 20,
        is_mwe: bool = False,
    ):
        """Fetches collocation information and concordances for a specified hit id.

        Args:
            coocc_id: Collocation id.
            use_context: If true, returns surrounding sentences for matched collocation.
            start_index: Collocation id.
            result_number: Collocation id.
            is_mwe: If true, then coocc_id refers to MWE, otherwise collocation.

        Return:
            Dictionary with collocation information and their concordances.
        """
        relation = self.get_relation_by_info_id(coocc_id, is_mwe=is_mwe)
        if is_mwe:
            relation["Tuples"] = format_concordances(
                self.db_mwe.get_concordances(
                    int(coocc_id), use_context, start_index, result_number
                )
            )
        else:
            relation["Tuples"] = format_concordances(
                self.db.get_concordances(
                    int(coocc_id), use_context, start_index, result_number
                )
            )
        return relation
