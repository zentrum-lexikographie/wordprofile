import logging
import math
import re
from collections import defaultdict
from typing import List, Optional, Union

import wordprofile.config
import wordprofile.formatter as formatting
from wordprofile.datatypes import Coocc
from wordprofile.utils import tag_f2b
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
            logger.info("Request for invalid lemma: (%s)" % lemma)
            return []

        lemma = lemma.replace("+", " ")
        pos = tag_f2b[pos]
        results = self.db.get_lemma_and_pos(lemma, pos)
        return formatting.format_lemma_pos(results, self.wp_spec.mapRelOrder)

    def get_lemma_and_pos_diff(self, lemma1: str, lemma2: str) -> List[dict]:
        """Fetches lemma pairs with common pos tags from word-profile database.

        Args:
            lemma1: Lemma of interest.
            lemma2: Lemma for comparison.

        Returns:
            List of lemma1–lemma2 combinations with additional information such as relation.
        """
        list1 = self.get_lemma_and_pos(lemma1)
        list2 = self.get_lemma_and_pos(lemma2)
        # checks lemma pairs for common pos tags
        results = []
        for i in list1:
            for j in list2:
                if i["POS"] == j["POS"]:
                    relations = set(i["Relations"]) | set(j["Relations"])
                    relations_ordered = [
                        r for r in self.wp_spec.mapRelOrder[i["POS"]] if r in relations
                    ]
                    results.append(
                        {
                            "LemmaId1": i["Lemma"],
                            "LemmaId2": j["Lemma"],
                            "POS": i["POS"],
                            "PosId": i["POS"],
                            "Relations": relations_ordered,
                        }
                    )
        return results

    def get_relations(
        self,
        lemma1: str,
        pos1: str,
        relations: Optional[List[str]] = None,
        start: int = 0,
        number: int = 20,
        order_by: str = "log_dice",
        min_freq: int = 0,
        min_stat: float = -1000.0,
    ) -> List[dict]:
        """Fetches collocations from wordprofile database.

        Args:
            lemma1: Lemma of interest.
            pos1: POS tag of lemma.
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
            logger.info("Request for invalid lemma: (%s)" % lemma1)
            return []

        relations = [] if relations is None else relations
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
                    "Tuples": formatting.format_relations(cooccs, self.wp_spec),
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
            List of absolute collocation ids.
        """
        for lemma in [lemma1, lemma2]:
            if lemma and not RE_LEMMA.fullmatch(lemma):
                logger.info("Request for invalid lemma: (%s)" % lemma)
                return []

        return [
            abs(c[0])
            for c in self.db_mwe.get_collocations(lemma1, lemma2)
            if len(c) == 1
        ]

    def get_mwe_relations(
        self,
        coocc_ids: List[int],
        relations: Optional[List[str]] = None,
        number: int = 20,
        order_by: str = "log_dice",
        min_freq: int = 0,
        min_stat: float = -1000.0,
    ) -> dict:
        """Fetches MWE from word-profile database.

        Args:
            coocc_ids: List of collocation ids.
            relations (optional): List of relation labels to filter results.
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
                lemma2 = formatting.format_lemma_with_preposition(
                    c.lemma2, c.prep, c.inverse
                )
                if lemma2 not in used:
                    used.add(lemma2)
                    res.append(c)
            return res

        relations = [] if relations is None else relations
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
            relation_identifier = f"{'~' if coocc.inverse else ''}{coocc.rel}"
            if relations and relation_identifier not in relations:
                continue
            lemma1 = coocc.lemma1
            pos1 = coocc.tag1
            grouped_relations[relation_identifier].append(coocc)
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
                    "Tuples": formatting.format_relations(
                        cooccs[:number], self.wp_spec, is_mwe=True
                    ),
                    "RelId": "{}#{}#{}".format(lemma1, pos1, relation),
                }
            )
        return {
            "parts": [
                {"Lemma": coocc_info.lemma1},
                {
                    "Lemma": formatting.format_lemma_with_preposition(
                        coocc_info.lemma2, coocc_info.prep, coocc_info.inverse
                    )
                },
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
    ) -> List[dict]:
        """
        Compare word profiles for a pair of lemmas per relation.

        Comparison is based on logDice score and computed w.r.t
        difference or similarity/intersection of collocates for
        lemma1 and lemma2.

        Args:
            lemma1: First lemma of interest.
            lemma2: Second lemma of interest.
            pos: POS tag for both lemmas.
            relations (optional): List of relation labels to fetch
                collocations from.
            number (optional): Number of collocations for each lemma to
                return per relation.
            order_by (optional): Key for sorting collocations, 'frequency'
                or 'log_dice'. Default is log_dice. Frontend also only
                supports 'log_dice'.
            min_freq (optional): Filter collocations with minimal frequency.
            min_stat (optional): Filter collocations with minimal stats score.
            operation (optional): Metric used to compute score for ranking
                collocations, 'adiff' (absolute difference) or 'hmean'
                (harmonic mean). Default is 'adiff'.
            use_intersection (optional): Consider only collocates that
                occur with both lemmas. Default is 'False'.
        Return:
            List of collocation-diffs grouped by relation.
        """
        for lemma in [lemma1, lemma2]:
            if lemma and not RE_LEMMA.fullmatch(lemma):
                logger.info("Request for invalid lemma: (%s)" % lemma)
                return []

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
                lemma1, lemma2, diffs, number, use_intersection, operation
            )
            results.append(
                {
                    "Relation": rel,
                    "Description": self.wp_spec.mapRelDesc.get(
                        rel, self.wp_spec.strRelDesc
                    ),
                    "Tuples": formatting.format_comparison(diffs),
                }
            )
        return results

    def __calculate_diff(
        self,
        lemma1: str,
        lemma2: str,
        diffs: list[Coocc],
        number: int,
        use_intersection: bool,
        operation: str,
    ) -> List[dict]:
        """
        Sort collocations of two lemmas by logDice score of shared collocate.

        Comparison is based on either difference or intersection of
        logDice scores for pairs of collocations.

        Difference:
            1. calculate absolute difference (adiff) for all pairs:
                |s₁(K)-s₂(K)| for all K ∊ WP₁ ∪ WP₂
            2. sort and choose number
            3. calculate true difference (diff) for all pairs:
                s₁(K)-s₂(K) for all K ∊ WP₁ ∪ WP₂
            4. sort again
        Intersect:
            1. compute harmonic mean (hmean) for all pairs:
                2 * s₁(K) * s₂(K) / s₁(K) + s₂(K) for all K ∊ WP₁ ∩ WP₂
            2. sort and choose number

        Args:
            lemma1: First lemma of interest.
            lemma2: Second lemma of interest.
            diffs: List of cooccurrences (Coocc) for lemma1 or lemma2.
            number: Number of collocations to return.
            use_intersection: If set, only the intersection of both lemmas
                is computed.
            operation: Lemma distance metric (hmean or adiff).
        Return:
            Sorted list of collocation-diffs.
        """
        collocation_diffs: defaultdict[str, dict] = defaultdict(dict)
        for c in diffs:
            if c.lemma1 == lemma1:
                collocation_diffs[c.lemma2]["coocc_1"] = c
                collocation_diffs[c.lemma2]["pos"] = c.tag1
            elif c.lemma1 == lemma2:
                collocation_diffs[c.lemma2]["coocc_2"] = c
                collocation_diffs[c.lemma2]["pos"] = c.tag1
            else:
                logger.warning(
                    "Unexpected lemma %s from collocation %d for lemma pair (%s, %s)."
                    % (c.lemma1, c.id, lemma1, lemma2)
                )
                continue
        # for intersection, only a subset is used further
        if use_intersection:
            diffs_grouped = [
                d
                for d in collocation_diffs.values()
                if "coocc_1" in d and "coocc_2" in d
            ]
        else:
            diffs_grouped = list(collocation_diffs.values())
        # compute score based on occurring cooccs
        for d in diffs_grouped:
            coocc1 = d.get("coocc_1", None)
            coocc2 = d.get("coocc_2", None)
            d["score"] = self.__diff_operation(
                operation,
                coocc1.score if coocc1 is not None else 0,
                coocc2.score if coocc2 is not None else 0,
            )
        # final sort and cut after desired number of cooccs
        if operation == "adiff":
            diffs_grouped.sort(key=lambda x: math.fabs(x["score"]), reverse=True)
            diffs_grouped = diffs_grouped[:number]
            diffs_grouped.sort(key=lambda x: x["score"], reverse=True)
        else:
            diffs_grouped.sort(key=lambda x: x["score"], reverse=True)
            diffs_grouped = diffs_grouped[:number]
        return diffs_grouped

    def __diff_operation(
        self, operation: str, s1: float, s2: float
    ) -> Union[int, float]:
        """Calculates the score difference.

        Args:
            operation: Metric operation.
            s1: Score of first lemma.
            s2: Score of second lemma.

        Returns:
            Distance or harmonic mean of scores depending on operation.
        """
        if operation == "adiff":
            score = s1 - s2
        elif operation == "hmean":
            score = 2 * (s1 * s2) / (s1 + s2)
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
        if coocc_info is None:
            return {}
        relation_identifier = coocc_info.rel
        if coocc_info.inverse:
            relation_identifier = f"~{relation_identifier}"
        if relation_identifier in self.wp_spec.mapRelDescDetail:
            description = self.wp_spec.mapRelDescDetail[relation_identifier]
        else:
            description = self.wp_spec.strRelDescDetail
        return formatting.format_relation_description(coocc_info, description)

    def get_concordances_and_relation(
        self,
        coocc_id: int,
        start_index: int = 0,
        result_number: int = 20,
        is_mwe: bool = False,
    ):
        """Fetches collocation information and concordances for a specified hit id.

        Args:
            coocc_id: Collocation id.
            start_index: Collocation id.
            result_number: Collocation id.
            is_mwe: If true, then coocc_id refers to MWE, otherwise collocation.

        Return:
            Dictionary with collocation information and their concordances.
        """
        relation = self.get_relation_by_info_id(coocc_id, is_mwe=is_mwe)
        if is_mwe:
            relation["Tuples"] = formatting.format_concordances(
                self.db_mwe.get_concordances(int(coocc_id), start_index, result_number)
            )
        else:
            relation["Tuples"] = formatting.format_concordances(
                self.db.get_concordances(int(coocc_id), start_index, result_number)
            )
        return relation

    def get_reduced_profile(
        self,
        lemma1: str,
        pos1: str,
        number: int = 20,
        order_by: str = "log_dice",
        min_freq: int = 5,
        min_stat: float = 0.0,
    ) -> list[dict[str, str | int | float]]:
        """
        Retrieve only collocates and metric from all relations for lemma1.

        Results are ordered by score (frequency or logDice).

        Args:
            lemma1:     Target lemma.
            pos1:       POS tag of target lemma.
            number:     Number of collocates to return.
            order_by:   Metric retrieved and used for ordering. 'log_dice'
                        or 'frequency'. Default is 'log_dice'.
            min_freq:   Frequency threshold for collocations. Default is 5.
            min_stat:   Minimal logDice score that collocations must exceed.
                        Default is 0.0.

        """
        collocates = self.db.get_collocates(
            lemma1, tag_f2b[pos1], number, order_by, min_freq, min_stat
        )
        return [formatting.format_collocate(coll) for coll in collocates]
