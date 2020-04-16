#!/usr/bin/python

import logging
import math
from collections import defaultdict
from typing import List, Union

from wordprofile.formatter import format_comparison, format_concordances, format_cooccs, format_lemma_pos
from wordprofile.wpse.connector import WPConnect
from wordprofile.wpse.variations import generate_orth_variations
from wordprofile.wpse.wpse_spec import WpSeSpec

logger = logging.getLogger('wordprofile')


class Wordprofile:
    def __init__(self, db_host, db_user, db_passwd, db_name, wp_spec_file):
        logger.info("start init ...")
        self.wp_spec = WpSeSpec(wp_spec_file)
        self.db = WPConnect(db_host, db_user, db_passwd, db_name)
        logger.info("init complete")

    def get_lemma_and_pos(self, lemma: str, pos: str = '', use_external_variations: bool = True) -> List[dict]:
        """Fetches lemma information from word-profile database.

        Args:
            lemma: Lemma of interest.
            pos: Pos tag of first lemma.
            use_external_variations: Whether to use variations for either lemmas if not found in database.

        Return:
            List of lemma-pos combinations with stats and possible relations.
        """
        results = self.db.get_lemma_and_pos(lemma, pos)
        # if not found in word-profile database, try variations mapping
        if not results and use_external_variations and lemma in self.wp_spec.mapVariation:
            lemma = self.wp_spec.mapVariation[lemma]
            results = self.db.get_lemma_and_pos(lemma, pos)
        # if not found in variations mapping, try orthographic variations function
        if not results and use_external_variations:
            for lemma in generate_orth_variations(lemma):
                results = self.db.get_lemma_and_pos(lemma, pos)
                if results:
                    break
        return format_lemma_pos(results)

    def get_lemma_and_pos_diff(self, lemma1: str, lemma2: str, use_variations: bool = True) -> List[dict]:
        """Fetches lemma pairs with common pos tags from word-profile database.

        Args:
            lemma1: Lemma of interest.
            lemma2: Lemma for comparison.
            use_variations: Whether to use variations for either lemmas if not found in database.

        Returns:
            List of lemma1–lemma2 combinations with additional information such as frequency and relation.
        """
        list1 = self.get_lemma_and_pos(lemma1, use_external_variations=use_variations)
        list2 = self.get_lemma_and_pos(lemma2, use_external_variations=use_variations)
        # checks lemma pairs for common pos tags
        results = []
        for i in list1:
            for j in list2:
                if i['POS'] == j['POS']:
                    relations = list(set(i['Relations']) | set(j['Relations']))
                    results.append({
                        'LemmaId1': i['Lemma'],
                        'LemmaId2': j['Lemma'],
                        'POS': i['POS'],
                        'PosId': i['POS'],
                        'Frequency1': i['Frequency'],
                        'Frequency2': j['Frequency'],
                        'Relations': relations
                    })
        return results

    def get_relations(self, lemma1: str, pos1: str, lemma2: str = '', pos2: str = '', relations: List[str] = (),
                      start: int = 0, number: int = 20, order_by: str = 'log_dice', min_freq: int = 0,
                      min_stat: int = -1000) -> List[dict]:
        """Fetches collocations from word-profile database.

        Args:
            lemma1: Lemma of interest, first collocate.
            pos1: Pos tag of first lemma.
            lemma2 (optional): Second collocate.
            pos2 (optional): Pos tag of second lemma.
            relations (optional): List of relation labels.
            start (optional): Number of collocations to skip.
            number (optional): Number of collocations to take.
            order_by (optional): Metric for ordering, frequency or log_dice.
            min_freq (optional): Filter collocations with minimal frequency.
            min_stat (optional): Filter collocations with minimal stats score.

        Return:
            List of selected collocations grouped by relation.
        """
        results = []
        for relation in relations:
            # meta relation is a summary of all relations
            if relation == 'META':
                cooccs = self.db.get_relation_meta(lemma1, pos1, lemma2, pos2, start, number,
                                                   order_by, min_freq, min_stat)
            else:
                cooccs = self.db.get_relation_tuples(lemma1, pos1, lemma2, pos2, start, number,
                                                     order_by, min_freq, min_stat, relation)
            results.append({
                'Relation': relation,
                'Description': self.wp_spec.mapRelDesc.get(relation, self.wp_spec.strRelDesc),
                'Tuples': format_cooccs(cooccs),
                'RelId': "{}#{}#{}".format(lemma1, pos1, relation)
            })
        return results

    def get_diff(self, lemma1: str, lemma2: str, pos: str, relations: List[str], number: int = 20,
                 order_by: str = 'log_dice', min_freq: int = 0, min_stat: int = -1000, operation: str = 'adiff',
                 use_intersection: bool = False, nbest: int = 0) -> List[dict]:
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
        results = []
        for rel in relations:
            diffs = self.db.get_relation_tuples_diff(lemma1, lemma2, pos, rel, order_by, min_freq, min_stat)
            diffs = self.__calculate_diff(lemma1, lemma2, diffs, number, nbest, use_intersection, operation)
            results.append({
                'Relation': rel,
                'Description': self.wp_spec.mapRelDesc.get(rel, self.wp_spec.strRelDesc),
                'Tuples': format_comparison(diffs)
            })
        return results

    def __calculate_diff(self, lemma1: str, lemma2: str, diffs, number: int, nbest: int, use_intersection: bool,
                         operation: str) -> List[dict]:
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
            if c.Lemma1 == lemma1:
                if not nbest or lemma1_ctr <= nbest:
                    diffs_grouped[c.Lemma2]['coocc_1'] = c
                    diffs_grouped[c.Lemma2]['rank_1'] = i
                    diffs_grouped[c.Lemma2]['pos'] = c.Pos1
                lemma1_ctr += 1
            elif c.Lemma1 == lemma2:
                if not nbest or lemma2_ctr <= nbest:
                    diffs_grouped[c.Lemma2]['coocc_2'] = c
                    diffs_grouped[c.Lemma2]['rank_2'] = i
                    diffs_grouped[c.Lemma2]['pos'] = c.Pos1
                lemma2_ctr += 1
            else:
                raise ValueError("Unexpected lemma")
        # for intersection, only a subset is used further
        if use_intersection:
            diffs_grouped = [d for d in diffs_grouped.values() if 'coocc_1' in d and 'coocc_2' in d]
        else:
            diffs_grouped = list(diffs_grouped.values())
        # compute score based on occurring cooccs
        for d in diffs_grouped:
            if 'coocc_1' in d and 'coocc_2' in d:
                d['score'] = self.__diff_operation(operation, d['coocc_1'].LogDice, d['coocc_2'].LogDice, d['rank_1'],
                                                   d['rank_2'])
            elif 'coocc_1' in d:
                d['score'] = self.__diff_operation(operation, d['coocc_1'].LogDice, 0, d['rank_1'], 0)
            elif 'coocc_2' in d:
                d['score'] = self.__diff_operation(operation, 0, d['coocc_2'].LogDice, 0, d['rank_2'])
        # final sort and cut after nbest cooccs
        if operation in ["adiff", "ardiff"]:
            diffs_grouped.sort(key=lambda x: math.fabs(x['score']), reverse=True)
            diffs_grouped = diffs_grouped[:number]
            diffs_grouped.sort(key=lambda x: x['score'], reverse=True)
        elif operation == "rmax":
            diffs_grouped.sort(key=lambda x: x['score'])
            diffs_grouped = diffs_grouped[:number]
        else:
            diffs_grouped.sort(key=lambda x: x['score'], reverse=True)
            diffs_grouped = diffs_grouped[:number]
        return diffs_grouped

    def __diff_operation(self, operation: str, s1: float, s2: float, r1: int, r2: int) -> Union[int, float]:
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

    def get_relation_by_info_id(self, coocc_id: int) -> dict:
        """Fetches collocation information for a specific hit id.

        Args:
            coocc_id: DB index of the collocation.

        Return:
            Dictionary with collocation information.
        """
        coocc_info = self.db.get_relation_by_id(coocc_id)
        if coocc_info.rel in self.wp_spec.mapRelDescDetail:
            description = self.wp_spec.mapRelDescDetail[coocc_info.rel]
            description = description.replace('$1', coocc_info.lemma1)
            description = description.replace('$2', coocc_info.lemma2)
        else:
            description = ""
        return {'Description': description, 'Relation': coocc_info.rel,
                'Lemma1': coocc_info.lemma1, 'Lemma2': coocc_info.lemma2,
                'POS1': coocc_info.pos1, 'POS2': coocc_info.pos2}

    def get_concordances_and_relation(self, coocc_id: int, use_context: bool = False, start_index: int = 0,
                                      result_number: int = 20):
        """Fetches collocation information and concordances for a specified hit id.

        Args:
            coocc_id: Collocation id.
            use_context: If true, returns surrounding sentences for matched collocation.
            start_index: Collocation id.
            result_number: Collocation id.

        Return:
            Dictionary with collocation information and their concordances.
        """
        relation = self.get_relation_by_info_id(coocc_id)
        relation['Tuples'] = format_concordances(
            self.db.get_concordances(coocc_id, use_context, start_index, result_number))
        return relation
