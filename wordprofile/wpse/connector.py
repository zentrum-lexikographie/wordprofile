import logging
from typing import List

import pymysql

import wordprofile.config
from wordprofile.datatypes import Concordance, Coocc, LemmaInfo
from wordprofile.errors import InternalError
from wordprofile.utils import split_relation_inversion

pymysql.install_as_MySQLdb()
import MySQLdb

logger = logging.getLogger("wordprofile.mysql")


class WPConnect:
    """Gives access to word profile database backend, following the repository pattern."""

    def __init__(self, host=None, user=None, passwd=None, dbname=None):
        self.__host = host or wordprofile.config.DB_HOST
        self.__user = user or wordprofile.config.DB_USER
        self.__passwd = passwd or str(wordprofile.config.DB_PASSWORD)
        self.__dbname = dbname or wordprofile.config.DB_NAME
        self.__conn = None
        self.__cursor = None

    def __init_connection(self):
        self.__conn = MySQLdb.connect(
            host=self.__host, user=self.__user, passwd=self.__passwd, db=self.__dbname
        )
        self.__cursor = self.__conn.cursor()

    def __close_connection(self):
        self.__cursor.close()
        self.__conn.close()

    def __fetchall(self, query, params=None):
        self.__init_connection()
        try:
            self.__cursor.execute(query, params)
            res = self.__cursor.fetchall()
        except (MySQLdb.Error, MySQLdb.Warning) as e:
            logger.exception(e)
            return []
        finally:
            self.__close_connection()
        return res

    def get_db_infos(self):
        query = """SELECT TABLE_NAME, TABLE_ROWS, CREATE_TIME, UPDATE_TIME
                   FROM information_schema.tables WHERE table_schema = DATABASE();"""
        return [
            {"name": t[0], "rows": t[1], "create_time": t[2], "last_update": t[3]}
            for t in self.__fetchall(query)
            if t[1]
        ]

    def get_label_frequencies(self):
        query = """SELECT label, freq FROM corpus_freqs;"""
        return {t[0]: t[1] for t in self.__fetchall(query)}

    def get_tag_frequencies(self):
        query = """
        SELECT tag, SUM(freq)
        FROM token_freqs tf
        GROUP BY tag;"""
        return {t[0]: t[1] for t in self.__fetchall(query)}

    def get_corpus_file_stats(self):
        query = """
        SELECT corpus, COUNT(*), min(`date`) as min_date, MAX(`date`) as max_date
        FROM corpus_files cf
        GROUP BY corpus;"""
        return {
            t[0]: {
                "count": t[1],
                "min_date": t[2],
                "max_date": t[3],
            }
            for t in self.__fetchall(query)
        }

    def get_concordances(
        self, coocc_id: int, start_index: int, result_number: int
    ) -> List[Concordance]:
        """Fetches concordances for collocation id from database backend.

        Args:
            coocc_id: Collocation id for concordances.
            start_index: Row index to start with.
            result_number: Number of results to return.

        Return:
            List of Concordance.
        """
        query = """
            SELECT * FROM
            (SELECT
                s_center.sentence, matches.head_position, matches.dep_position,
                matches.prep_position, cf.corpus, cf.date, cf.orig, cf.available,
                cf.file
            FROM
                matches
            INNER JOIN corpus_files as cf ON (matches.corpus_file_id = cf.id)
            INNER JOIN concord_sentences as s_center ON
                (s_center.corpus_file_id = cf.id
                AND s_center.sentence_id = matches.sentence_id)
            WHERE
                matches.collocation_id = %(id)s
            ORDER BY s_center.random_val
            LIMIT %(start)s,%(number)s)
            as sample
            ORDER BY date DESC;
            """
        params = {
            "id": abs(coocc_id),
            "start": start_index,
            "number": result_number,
        }
        return list(map(lambda i: Concordance(*i), self.__fetchall(query, params)))

    def get_lemma_and_pos(self, lemma: str, lemma_tag: str = "") -> List[LemmaInfo]:
        """Fetches lemma information for valid inputs.
        Args:
            lemma: Lemma of form [a-zA-Z-]
            lemma_tag (optional): Pos tag of lemma.

        Return:
            List of LemmaInfo that fits criteria.
        """
        if lemma_tag:
            query = """
                SELECT
                    sub.lemma,
                    sub.tag,
                    sub.label,
                    SUM(sub.frequency) AS freq,
                    sub.inv
                FROM (
                    SELECT
                        lemma1 AS lemma,
                        lemma1_tag AS tag,
                        label,
                        frequency,
                        0 AS inv
                    FROM collocations
                    WHERE lemma1 = %(lemma)s AND lemma1_tag = %(tag)s
                    UNION ALL
                    SELECT
                        lemma2 AS lemma,
                        lemma2_tag AS tag,
                        label,
                        frequency,
                        1 AS inv
                    FROM collocations
                    WHERE lemma2 = %(lemma)s AND lemma2 != lemma1
                        AND lemma2_tag = %(tag)s
                ) AS sub
                GROUP BY sub.lemma, sub.tag, sub.label, sub.inv;"""

            params: dict[str, str] = {"lemma": lemma, "tag": lemma_tag}
        else:
            query = """
                SELECT
                    sub.lemma,
                    sub.tag,
                    sub.label,
                    SUM(sub.frequency) AS freq,
                    sub.inv
                FROM (
                    SELECT
                        lemma1 AS lemma,
                        lemma1_tag AS tag,
                        label,
                        frequency,
                        0 AS inv
                    FROM collocations
                    WHERE lemma1 = %(lemma)s
                    UNION ALL
                    SELECT
                        lemma2 AS lemma,
                        lemma2_tag AS tag,
                        label,
                        frequency,
                        1 AS inv
                    FROM collocations
                    WHERE lemma2 = %(lemma)s and lemma2 != lemma1
                ) AS sub
                GROUP BY sub.lemma, sub.tag, sub.label, sub.inv;"""
            params = {"lemma": lemma}
        return list(
            filter(
                lambda l: l.lemma.lower() == lemma.lower(),
                map(lambda i: LemmaInfo(*i), self.__fetchall(query, params)),
            )
        )

    def get_relation_by_id(self, coocc_id: int, min_freq: int = 1) -> Coocc:
        """Fetches collocation information for collocation id from database backend.

        Args:
            coocc_id: Collocation id for concordances.
            min_freq: Minimal number of occurrences for multi word expression

        Return:
            Collocation information.
        """
        query = """
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, tf1.surface, tf2.surface, c.lemma1_tag, c.lemma2_tag,
            IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, 0,
            IF(ABS(c.id) IN (SELECT collocation1_id FROM mwe WHERE frequency >= %s), 1, 0) as has_mwe,
            (SELECT COUNT(*) FROM matches m WHERE m.collocation_id = ABS(c.id)) as num_concords, c.preposition
        FROM collocations c
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag)
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag)
        WHERE c.id = %s;
        """
        res = self.__fetchall(query, (min_freq, abs(coocc_id)))
        if len(res) == 0:
            raise ValueError("Invalid Id")
        elif len(res) > 1:
            raise InternalError(f"Too many results for coocc id {coocc_id}.")
        else:
            result = Coocc(*res[0])
            if coocc_id < 0:
                return self._invert_coocc(result)
            return result

    def _invert_coocc(self, coocc: Coocc) -> Coocc:
        coocc.inverse = 1
        coocc.id = coocc.id * -1
        coocc.lemma1, coocc.lemma2 = coocc.lemma2, coocc.lemma1
        coocc.tag1, coocc.tag2 = coocc.tag2, coocc.tag1
        coocc.form1, coocc.form2 = coocc.form2, coocc.form1
        return coocc

    def get_relation_tuples(
        self,
        lemma1: str,
        lemma1_tag: str,
        start: int,
        number: int,
        order_by: str,
        min_freq: int,
        min_stat: float,
        relation: str,
    ) -> List[Coocc]:
        """
        Fetches collocations with related statistics for a specific relation
        from database backend.

        Args:
            lemma1: Lemma of interest, first collocate.
            lemma1_tag: Pos tag of lemma.
            start: Number of collocations to skip.
            number: Number of collocations to take.
            order_by: Metric for ordering, frequency or log_dice.
            min_freq: Filter collocations with minimal frequency.
            min_stat: Filter collocations with minimal stats score.
            relation: relation label.

        Return:
            List of Coocc.
        """
        relation, inv = split_relation_inversion(relation)
        query = f"""
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, tf1.surface, tf2.surface, c.lemma1_tag,
            c.lemma2_tag, IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice,
            %(inv)s, IF(ABS(c.id) IN (SELECT collocation1_id FROM mwe WHERE frequency >= %(min_freq)s), 1, 0)
            as has_mwe, (SELECT COUNT(*) FROM matches m WHERE m.collocation_id = ABS(c.id))
            as num_concords, c.preposition
        FROM collocations c
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag)
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag)
        WHERE
            (lemma1 = %(lemma)s AND lemma1_tag = %(tag)s
            AND label = %(label)s AND %(inv)s = 0
            AND frequency >= %(min_freq)s AND c.score >= %(min_stat)s)
            OR
            (lemma2 = %(lemma)s AND lemma2_tag = %(tag)s
            AND label = %(label)s AND %(inv)s = 1
            AND c.frequency >= %(min_freq)s AND c.score >= %(min_stat)s)
        ORDER BY {order_by} DESC LIMIT %(start)s,%(number)s;
        """
        params = {
            "min_freq": min_freq,
            "lemma": lemma1,
            "tag": lemma1_tag,
            "start": start,
            "number": number,
            "label": relation,
            "min_stat": min_stat,
            "inv": inv,
        }
        return list(
            map(lambda i: self._coocc_from_db_result(i), self.__fetchall(query, params))
        )

    def get_relation_meta(
        self,
        lemma1: str,
        lemma1_tag: str,
        start: int,
        number: int,
        order_by: str,
        min_freq: int,
        min_stat: float,
        relations: List[str],
    ) -> List[Coocc]:
        """
        Fetches collocations with related statistics for all relations
        from database backend.

        Args:
            lemma1: Lemma of interest, first collocate.
            lemma1_tag: Pos tag of lemma.
            start: Number of collocations to skip.
            number: Number of collocations to take.
            order_by: Metric for ordering, 'frequency' or 'log_dice'.
            min_freq: Filter collocations with minimal frequency.
            min_stat: Filter collocations with minimal stats score.
            relations: List of relations to be returned.

        Return:
            List of Coocc.
        """
        query = f"""
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, tf1.surface, tf2.surface, c.lemma1_tag,
            c.lemma2_tag, IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0)
            as log_dice,
            CASE
                WHEN lemma1 = %(lemma)s
                    THEN 0
                WHEN lemma2 = %(lemma)s
                    THEN 1
            END AS inv, 0, (SELECT COUNT(*) FROM matches m WHERE m.collocation_id = ABS(c.id))
            as num_concords, c.preposition
        FROM collocations c
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag)
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag)
        WHERE
            ((lemma1 = %(lemma)s AND lemma1_tag = %(tag)s
            AND frequency >= %(min_freq)s AND c.score >= %(min_stat)s
            AND label in %(base_relations)s )
            OR
            (lemma2 = %(lemma)s AND lemma2_tag = %(tag)s
            AND frequency >= %(min_freq)s AND c.score >= %(min_stat)s
            AND label in %(inverse_relations)s )
            )
        ORDER BY {order_by} DESC LIMIT %(start)s,%(number)s;
        """
        base_relations = {
            relation for relation in relations if not relation.startswith("~")
        }
        inverse_relations = {
            relation.strip("~") for relation in relations if relation.startswith("~")
        }
        params = {
            "lemma": lemma1,
            "tag": lemma1_tag,
            "min_freq": min_freq,
            "min_stat": min_stat,
            "start": start,
            "number": number,
            "base_relations": base_relations or {""},
            "inverse_relations": inverse_relations or {""},
        }
        return list(
            map(
                lambda i: self._coocc_from_db_result(i), self.__fetchall(query, params)
            ),
        )

    def _coocc_from_db_result(self, result) -> Coocc:
        coocc = Coocc(*result)
        if coocc.inverse == 1:
            return self._invert_coocc(coocc)
        return coocc

    def get_collocates(
        self,
        lemma: str,
        tag: str,
        number: int = 20,
        order_by: str = "log_dice",
        min_freq: int = 5,
        min_stat: float = 0.0,
    ) -> list[tuple[str, int | float]]:
        """
        Fetch only collocates and metrics (logDice or frequency) for target
        lemma from all relations.

        The result is a list of tuples (collocate, score) sorted by the
        retrieved metric in descending order. Collocations are filtered
        by frequency and logDice score.
        N.B.: The look-up of collocates is relation-agnostic and returns
        only the lemma of the collocate. I.e. the same lemma might appear
        more than once with different scores because they originate from
        different relations or are differentiated by their preposition.

        Args:
            lemma:      Target lemma.
            tag:        POS tag of lemma.
            number:     Number of collocates to return.
            order_by:   Metric retrieved and used for ordering. 'log_dice'
                        or 'frequency'; default is 'log_dice'.
            min_freq:   Frequency threshold of collocations. Default is 5.
            min_stat:   Minimal logDice score that collocations must have.
                        Default is 0.0.
        """
        metric = "score" if order_by == "log_dice" else "frequency"
        query = f"""
        SELECT
          CASE
            WHEN %(lemma)s = c.lemma1
                THEN c.lemma2
            WHEN %(lemma)s = c.lemma2
                THEN c.lemma1
          END AS lemma, IFNULL(c.{metric}, 0) as metric
        FROM collocations c
        WHERE
          (
            (%(lemma)s = c.lemma1
             AND c.lemma1_tag = %(tag)s
             AND c.frequency >= %(min_freq)s
             AND c.score >= %(min_stat)s)
            OR
            (%(lemma)s = c.lemma2
             AND c.lemma2_tag = %(tag)s
             AND c.frequency >= %(min_freq)s
             AND c.score >= %(min_stat)s)
             AND c.label != "KON"
          )
        ORDER BY metric DESC LIMIT 0,%(number)s;"""
        params = {
            "lemma": lemma,
            "tag": tag,
            "min_freq": min_freq,
            "min_stat": min_stat,
            "number": number,
        }
        return list(self.__fetchall(query, params))

    def get_relation_tuples_diff(
        self,
        lemma1: str,
        lemma2: str,
        lemma_tag: str,
        relation: str,
        order_by: str,
        min_freq: int,
        min_stat,
    ) -> List[Coocc]:
        """Fetches collocations for both lemmas with related statistics for a specific relation from database backend.

        Args:
            lemma1: First lemma of interest for comparison.
            lemma2: Second lemma of interest.
            lemma_tag: Pos tag of compared lemmata.
            relation: Relation label.
            order_by: Metric for ordering, 'frequency' or 'log_dice'.
            min_freq: Filter collocations with minimal frequency.
            min_stat: Filter collocations with minimal stats score.

        Return:
            List of Coocc.
        """
        relation, inv = split_relation_inversion(relation)
        query = f"""
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, tf1.surface, tf2.surface, c.lemma1_tag, c.lemma2_tag,
            IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0) as log_dice, %(inv)s,
            IF(ABS(c.id) IN (SELECT collocation1_id FROM mwe WHERE frequency >= %(min_freq)s), 1, 0)
            as has_mwe, (SELECT COUNT(*) FROM matches m WHERE m.collocation_id = ABS(c.id)) as num_concords,
            c.preposition
        FROM collocations c
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag)
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag)
        WHERE
            ((c.lemma1 IN %(lemmata)s AND c.lemma1_tag = %(tag)s
            AND c.label = %(relation)s AND c.frequency >= %(min_freq)s
            AND c.score >= %(min_stat)s AND %(inv)s = 0)
            OR
            (c.lemma2 IN %(lemmata)s AND c.lemma2_tag = %(tag)s
            AND c.label = %(relation)s AND c.frequency >=%(min_freq)s
            AND c.score >=%(min_stat)s AND %(inv)s = 1)
            )
        ORDER BY {order_by} DESC;"""
        params = {
            "lemmata": (lemma1, lemma2),
            "tag": lemma_tag,
            "min_freq": min_freq,
            "min_stat": min_stat,
            "relation": relation,
            "inv": inv,
        }
        return list(
            map(lambda i: self._coocc_from_db_result(i), self.__fetchall(query, params))
        )

    def get_relation_tuples_diff_meta(
        self,
        lemma1: str,
        lemma2: str,
        lemma_tag: str,
        order_by: str,
        min_freq: int,
        min_stat,
        relations: List[str],
    ) -> List[Coocc]:
        """Fetches collocations for both lemmas with related statistics for all relations from database backend.

        Args:
            lemma1: First lemma of interest for comparison.
            lemma2: Second lemma of interest.
            lemma_tag: Pos tag of lemmata.
            order_by: Metric for ordering, 'frequency' or 'log_dice'.
            min_freq: Filter collocations with minimal frequency.
            min_stat: Filter collocations with minimal stats score.
            relations: List of relations to be returned.

        Return:
            List of Coocc.
        """
        query = f"""
        SELECT
            c.id, c.label, c.lemma1, c.lemma2, tf1.surface, tf2.surface, c.lemma1_tag,
            c.lemma2_tag, IFNULL(c.frequency, 0) as frequency, IFNULL(c.score, 0.0)
            as log_dice,
            CASE
                WHEN lemma1 IN %(lemmata)s
                    THEN 0
                WHEN lemma2 IN %(lemmata)s
                    THEN 1
            END AS inv, 0, (SELECT COUNT(*) FROM matches m WHERE m.collocation_id = ABS(c.id))
            as num_concords, c.preposition
        FROM collocations c
        JOIN token_freqs tf1 ON (c.lemma1 = tf1.lemma && c.lemma1_tag = tf1.tag)
        JOIN token_freqs tf2 ON (c.lemma2 = tf2.lemma && c.lemma2_tag = tf2.tag)
        WHERE
            ((c.lemma1 IN %(lemmata)s AND c.lemma1_tag = %(tag)s
            AND c.frequency >= %(min_freq)s AND c.score >= %(min_stat)s
            AND c.label IN %(base_relations)s)
            OR
            (c.lemma2 IN %(lemmata)s AND c.lemma2_tag = %(tag)s
            AND c.frequency >= %(min_freq)s AND c.score >= %(min_stat)s
            AND c.label IN %(inverse_relations)s))
        ORDER BY {order_by} DESC;"""
        base_relations = {
            relation for relation in relations if not relation.startswith("~")
        }
        inverse_relations = {
            relation.strip("~") for relation in relations if relation.startswith("~")
        }
        params = {
            "lemmata": (lemma1, lemma2),
            "tag": lemma_tag,
            "min_freq": min_freq,
            "min_stat": min_stat,
            "base_relations": base_relations or {""},
            "inverse_relations": inverse_relations or {""},
        }
        return list(
            map(
                lambda i: self._coocc_from_db_result(i), self.__fetchall(query, params)
            ),
        )
